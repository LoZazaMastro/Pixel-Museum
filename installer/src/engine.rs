use crate::{
    Options,
    manifest::{
        Manifest, Package, PackageFormat, PackageKind, ensure_no_links, safe_relative_path,
        valid_sha256, validate_release_url,
    },
};
use anyhow::{Context, Result, bail, ensure};
use reqwest::{
    blocking::Client,
    header::{ACCEPT_ENCODING, CONTENT_RANGE, RANGE},
    redirect::Policy,
};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::{
    collections::HashSet,
    fs::{self, File, OpenOptions},
    io::{Read, Seek, SeekFrom, Write},
    path::{Path, PathBuf},
    sync::{
        Mutex,
        atomic::{AtomicBool, Ordering},
    },
    time::{Duration, Instant},
};

pub const EMBEDDED_MANIFEST: &[u8] =
    include_bytes!(concat!(env!("OUT_DIR"), "/release-manifest.json"));
pub const LICENSE: &str = include_str!("../../LICENSE");
pub const NOTICES: &str = include_str!("../../THIRD_PARTY_NOTICES.md");
pub const FONT_LICENCE: &str = include_str!("../assets/Inter-LICENSE.txt");
pub const SOFTWARE_LICENCES: &str = include_str!("../licenses/THIRD-PARTY-NOTICES.txt");

#[derive(Clone)]
pub struct Release {
    pub manifest: Manifest,
    pub payload_dir: Option<PathBuf>,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Phase {
    Download,
    Check,
    Verify,
    Extract,
    Prepare,
    Install,
    Finish,
}

#[derive(Clone, Debug)]
pub struct Progress {
    pub phase: Phase,
    pub package: String,
    pub done: u64,
    pub total: u64,
}

pub fn check_cancel(cancel: &AtomicBool) -> Result<()> {
    ensure!(!cancel.load(Ordering::Relaxed), "Installation cancelled");
    Ok(())
}

#[derive(Default)]
pub struct InstallControl {
    cancelled: AtomicBool,
    committing: Mutex<bool>,
}

impl InstallControl {
    pub fn cancel_token(&self) -> &AtomicBool {
        &self.cancelled
    }

    pub fn request_cancel(&self) {
        if !*self.committing.lock().unwrap() {
            self.cancelled.store(true, Ordering::Relaxed);
        }
    }

    pub fn is_committing(&self) -> bool {
        *self.committing.lock().unwrap()
    }

    pub fn begin_commit(&self) -> Result<()> {
        let mut committing = self.committing.lock().unwrap();
        check_cancel(self.cancel_token())?;
        *committing = true;
        Ok(())
    }
}

pub fn client() -> Result<Client> {
    let _ = rustls::crypto::ring::default_provider().install_default();
    Client::builder()
        .user_agent("Pixel-Museum-Setup/0.1")
        .connect_timeout(Duration::from_secs(20))
        .timeout(Duration::from_secs(20))
        .redirect(Policy::custom(|attempt| {
            let host = attempt.url().host_str().unwrap_or("");
            if attempt.previous().len() >= 8 {
                return attempt.error("Too many download redirects");
            }
            if attempt.url().scheme() != "https"
                || !(host == "github.com"
                    || host == "release-assets.githubusercontent.com"
                    || host == "objects.githubusercontent.com"
                    || host == "github-releases.githubusercontent.com")
            {
                return attempt.error("Release redirected outside GitHub HTTPS asset storage");
            }
            attempt.follow()
        }))
        .build()
        .context("Cannot initialise HTTPS downloads")
}

pub fn load_release(opts: &Options, cancel: &AtomicBool) -> Result<Release> {
    check_cancel(cancel)?;
    let sidecar = std::env::current_exe()?
        .parent()
        .context("Setup has no parent folder")?
        .join("windows-manifest.json");
    let source = opts.manifest.clone().or_else(|| {
        option_env!("PIXEL_MUSEUM_MANIFEST_URL")
            .filter(|s| !s.is_empty())
            .map(str::to_owned)
    });
    let mut payload_dir = opts.payload_dir.clone();
    let data = if let Some(source) = source {
        if source.starts_with("https://") {
            validate_release_url(&source)?;
            let expected = opts
                .manifest_sha256
                .as_deref()
                .or(option_env!("PIXEL_MUSEUM_MANIFEST_SHA256"))
                .context("A remote manifest needs its trusted SHA-256 digest")?;
            ensure!(valid_sha256(expected), "Invalid trusted manifest SHA-256");
            let response = client()?
                .get(source)
                .header(ACCEPT_ENCODING, "identity")
                .send()
                .context("Cannot download release manifest")?
                .error_for_status()?;
            let mut data = Vec::new();
            response.take(1024 * 1024 + 1).read_to_end(&mut data)?;
            ensure!(
                format!("{:x}", Sha256::digest(&data)).eq_ignore_ascii_case(expected),
                "Release manifest SHA-256 does not match the trusted digest"
            );
            data
        } else {
            let path = PathBuf::from(source);
            if payload_dir.is_none() {
                payload_dir = path.parent().map(Path::to_path_buf);
            }
            read_manifest(&path)?
        }
    } else if !EMBEDDED_MANIFEST.is_empty() {
        EMBEDDED_MANIFEST.to_vec()
    } else if sidecar.is_file() {
        if payload_dir.is_none() {
            payload_dir = sidecar.parent().map(Path::to_path_buf);
        }
        read_manifest(&sidecar)?
    } else {
        bail!(
            "No Windows release package is configured. Select the windows-manifest.json supplied with your download."
        );
    };
    check_cancel(cancel)?;
    if payload_dir.is_none() {
        payload_dir = std::env::current_exe()?.parent().map(Path::to_path_buf);
    }
    Ok(Release {
        manifest: Manifest::parse(&data)?,
        payload_dir,
    })
}

fn read_manifest(path: &Path) -> Result<Vec<u8>> {
    let file = File::open(path)
        .with_context(|| format!("Cannot open release manifest {}", path.display()))?;
    ensure!(
        file.metadata()?.len() <= 1024 * 1024,
        "Manifest exceeds the 1 MiB limit"
    );
    let mut bytes = Vec::new();
    file.take(1024 * 1024 + 1).read_to_end(&mut bytes)?;
    Ok(bytes)
}

pub fn default_destination() -> PathBuf {
    std::env::var_os("LOCALAPPDATA")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir)
        .join("Programs")
        .join("Pixel Museum")
}

pub fn validate_destination(destination: &Path) -> Result<PathBuf> {
    crate::update::ordinary_absolute(destination)?;
    ensure!(
        destination.is_absolute(),
        "Choose an absolute installation path"
    );
    ensure!(
        destination.components().all(|c| !matches!(
            c,
            std::path::Component::ParentDir | std::path::Component::CurDir
        )),
        "Installation path cannot contain . or .."
    );
    ensure_no_links(destination)?;
    let parent = destination
        .parent()
        .context("Cannot install in a drive root")?;
    ensure!(
        !parent.as_os_str().is_empty(),
        "Cannot install in a drive root"
    );
    if destination.exists() {
        ensure!(
            destination.is_dir(),
            "The destination already contains files. Choose a new, empty Pixel Museum folder."
        );
        if fs::read_dir(destination)?.next().is_some() {
            uninstalled_folder(destination, destination)?;
        }
    }
    Ok(parent.to_path_buf())
}

const PERSONAL_FILES: [&str; 3] = ["preferences.json", "video-settings.json", "trophies-v1.dat"];

#[derive(Debug, PartialEq, Eq)]
struct ReinstallFile {
    path: PathBuf,
    bytes: u64,
    sha256: String,
}

#[derive(Debug, PartialEq, Eq)]
struct ReinstallFolder {
    files: Vec<ReinstallFile>,
    directories: Vec<PathBuf>,
}

// A completed V3 uninstall is the only nonempty destination accepted. The
// receipt establishes root ownership; it never authorizes deleting unknown data.
fn uninstalled_folder(root: &Path, identity: &Path) -> Result<ReinstallFolder> {
    use crate::{integration, update};
    ensure_no_links(root)?;
    let receipt: serde_json::Value = serde_json::from_slice(&update::read_limited(
        &root.join(integration::RECEIPT),
        1024 * 1024,
    )?)
    .context("Nonempty destination is not a completed Pixel Museum uninstall")?;
    let full_cleanup = receipt["personal_data_preserved"] == false
        && receipt["full_folder_cleanup_requested"] == true;
    ensure!(
        receipt["schema_version"] == 1
            && receipt["executable"] == "Pixel Museum.exe"
            && receipt["uninstalled"] == true
            && receipt["windows_registered"] == false
            && (receipt["personal_data_preserved"] == true || full_cleanup),
        "Nonempty destination is not a completed Pixel Museum uninstall"
    );
    let registration: integration::Registration = serde_json::from_value(
        receipt
            .get("windows_integration")
            .context("Missing previous installation ownership")?
            .clone(),
    )?;
    integration::validate(identity, &registration)?;
    let helper_sha = match (
        receipt.get("retained_maintenance_helper"),
        receipt.get("retained_maintenance_helper_sha256"),
    ) {
        (Some(serde_json::Value::Null), Some(serde_json::Value::Null)) => None,
        (Some(serde_json::Value::String(path)), Some(serde_json::Value::String(sha)))
            if path == integration::HELPER && valid_sha256(sha) =>
        {
            Some(sha)
        }
        _ => bail!("Invalid retained maintenance helper ownership"),
    };
    let mut result = ReinstallFolder {
        files: Vec::new(),
        directories: Vec::new(),
    };
    let mut pending = vec![PathBuf::new()];
    let mut seen = HashSet::new();
    while let Some(relative) = pending.pop() {
        for entry in fs::read_dir(root.join(&relative))? {
            let entry = entry?;
            let relative = relative.join(entry.file_name());
            let text = relative
                .to_str()
                .context("Invalid retained filename")?
                .replace('\\', "/");
            ensure!(
                seen.insert(text.to_ascii_lowercase()) && seen.len() <= 512,
                "Ambiguous or excessive files in uninstalled folder"
            );
            let path = root.join(&relative);
            ensure_no_links(&path)?;
            let metadata = fs::symlink_metadata(&path)?;
            if metadata.is_dir() {
                // Empty framework directories can remain after an owned uninstall.
                ensure!(
                    matches!(
                        text.split('/').next().unwrap_or(""),
                        "assets"
                            | "content"
                            | "music"
                            | "licenses"
                            | "models"
                            | "tools"
                            | "collection"
                            | "application-updates"
                    ),
                    "Unrelated directory prevents reinstall: {text}"
                );
                result.directories.push(relative.clone());
                pending.push(relative);
                continue;
            }
            let personal = PERSONAL_FILES.contains(&text.as_str());
            ensure!(
                !full_cleanup || !personal,
                "Full-cleanup receipt still contains personal progress"
            );
            let receipt_file = text == integration::RECEIPT;
            let helper = text == integration::HELPER && helper_sha.is_some();
            let lock = text == "application-updates/apply.lock";
            ensure!(
                personal || receipt_file || helper || lock,
                "Unrelated or modified file prevents reinstall: {text}"
            );
            // This also rejects reparse points, nonregular files and hardlinks.
            let file = update::process::open_regular(&path)?;
            let bytes = file.metadata()?.len();
            let limit = if helper {
                64 * 1024 * 1024
            } else if receipt_file {
                1024 * 1024
            } else if lock {
                0
            } else {
                16 * 1024 * 1024
            };
            ensure!(bytes <= limit, "Invalid retained file size: {text}");
            let sha256 = update::hash_file(&path)?;
            if helper {
                ensure!(
                    helper_sha.is_some_and(|sha| sha.eq_ignore_ascii_case(&sha256)),
                    "Retained maintenance helper was changed"
                );
            }
            result.files.push(ReinstallFile {
                path: relative,
                bytes,
                sha256,
            });
        }
    }
    if helper_sha.is_some() {
        ensure!(
            result
                .files
                .iter()
                .any(|file| file.path == Path::new(integration::HELPER)),
            "Retained maintenance helper is missing"
        );
    }
    result.files.sort_by(|a, b| a.path.cmp(&b.path));
    result.directories.sort();
    Ok(result)
}

fn preserve_personal_files(
    previous: &ReinstallFolder,
    root: &Path,
    stage: &Path,
    cancel: &AtomicBool,
) -> Result<()> {
    for retained in &previous.files {
        if !PERSONAL_FILES
            .iter()
            .any(|name| retained.path == Path::new(name))
        {
            continue;
        }
        let target = stage.join(&retained.path);
        ensure!(
            !target.exists(),
            "App package collides with personal progress"
        );
        let mut source = crate::update::process::open_regular(&root.join(&retained.path))?;
        ensure!(
            source.metadata()?.len() == retained.bytes,
            "Personal progress changed during reinstall"
        );
        copy_cancellable(&mut source, &target, cancel)?;
        ensure!(
            fs::metadata(&target)?.len() == retained.bytes
                && crate::update::hash_file(&target)? == retained.sha256,
            "Personal progress changed during reinstall; original files were preserved"
        );
    }
    Ok(())
}

fn clean_retired_folder(root: &Path, identity: &Path, expected: &ReinstallFolder) -> Result<()> {
    ensure!(
        uninstalled_folder(root, identity)? == *expected,
        "Retired folder changed; it has been preserved"
    );
    // Remove only the exact verified residue. Never recursively remove a folder
    // which could have acquired an unrelated file during installation.
    for file in &expected.files {
        fs::remove_file(root.join(&file.path))?;
    }
    let mut directories = expected.directories.clone();
    directories.sort_by_key(|path| std::cmp::Reverse(path.components().count()));
    for directory in directories {
        fs::remove_dir(root.join(directory))?;
    }
    fs::remove_dir(root)?;
    Ok(())
}

fn restore_reinstall(backup: &Option<PathBuf>, destination: &Path) -> Result<()> {
    if let Some(backup) = backup {
        fs::rename(backup.join("previous"), destination).with_context(|| {
            format!(
                "Cannot restore previous personal data; it remains safe at {}",
                backup.display()
            )
        })?;
        let _ = fs::remove_dir(backup);
    }
    Ok(())
}

pub fn install(
    release: &Release,
    destination: &Path,
    language: &str,
    cancel: &AtomicBool,
    report: impl FnMut(Progress),
) -> Result<()> {
    install_with_registration(release, destination, language, cancel, report, None)
}

pub struct InstallRegistration {
    pub environment: crate::integration::Environment,
    pub desktop_shortcut: bool,
}

pub fn upgrade_registered(
    release: &Release,
    destination: &Path,
    language: &str,
    control: &InstallControl,
    mut report: impl FnMut(Progress),
) -> Result<()> {
    release.manifest.validate()?;
    let cancel = control.cancel_token();
    check_cancel(cancel)?;
    let mut report_check = |phase, done, total| {
        report(Progress {
            phase,
            package: String::new(),
            done,
            total,
        })
    };
    let installed = crate::update::inspect_for_setup(destination, cancel, &mut report_check)?;
    ensure!(
        crate::update::version_is_newer(&installed.inventory.version, &release.manifest.version),
        "Setup can only upgrade to a newer version"
    );
    crate::update::process::assert_not_running(&destination.join("Pixel Museum.exe"))?;
    let app = release
        .manifest
        .packages
        .iter()
        .find(|p| p.kind == PackageKind::App)
        .context("Release has no application package")?;
    let available_locally = |p: &Package| {
        release.payload_dir.as_ref().map(|dir| dir.join(&p.filename))
            .filter(|path| path.is_file())
    };
    let inventory_sha = crate::update::inventory_sha256(destination)?;
    let delta = release.manifest.updates.iter().find(|update| {
        update.from_version == installed.inventory.version
            && update.base_inventory_sha256.eq_ignore_ascii_case(&inventory_sha)
            && (available_locally(&update.package).is_some() || update.package.url.is_some())
    });
    let environment = crate::integration::Environment::current_user()?;
    let mut apply = |package: &Package, delta| {
        let mut progress = |phase, done, total| {
            report(Progress { phase, package: package.id.clone(), done, total })
        };
        let temporary;
        let archive = if let Some(local) = available_locally(package) {
            local
        } else {
            temporary = tempfile::Builder::new()
                .prefix(".pixel-museum-upgrade-")
                .tempdir_in(destination.parent().context("Installation parent missing")?)?;
            let path = temporary.path().join(&package.filename);
            download(&client()?, package, &path, cancel, |done| {
                progress(Phase::Download, done, package.bytes)
            })?;
            path
        };
        crate::update::apply_from_setup(
            destination, &release.manifest.version, package, &archive, language,
            &environment, control, delta, progress,
        )
    };
    if let Some(delta) = delta {
        match apply(&delta.package, Some(delta)) {
            Err(error) if error.is::<crate::update::DeltaBaseUnavailable>() => {}
            result => return result,
        }
    }
    apply(app, None)
}

pub fn install_registered(
    release: &Release,
    destination: &Path,
    language: &str,
    desktop_shortcut: bool,
    control: &InstallControl,
    report: impl FnMut(Progress),
) -> Result<()> {
    let integration = InstallRegistration {
        environment: crate::integration::Environment::current_user()?,
        desktop_shortcut,
    };
    install_with_commit(
        release,
        destination,
        language,
        control.cancel_token(),
        report,
        Some(&integration),
        || control.begin_commit(),
    )
}

pub fn install_with_registration(
    release: &Release,
    destination: &Path,
    language: &str,
    cancel: &AtomicBool,
    report: impl FnMut(Progress),
    registration: Option<&InstallRegistration>,
) -> Result<()> {
    install_with_commit(
        release,
        destination,
        language,
        cancel,
        report,
        registration,
        || check_cancel(cancel),
    )
}

fn install_with_commit(
    release: &Release,
    destination: &Path,
    language: &str,
    cancel: &AtomicBool,
    mut report: impl FnMut(Progress),
    registration: Option<&InstallRegistration>,
    begin_commit: impl FnOnce() -> Result<()>,
) -> Result<()> {
    release.manifest.validate()?;
    check_cancel(cancel)?;
    let parent = validate_destination(destination)?;
    fs::create_dir_all(&parent).context("Cannot create the installation parent folder")?;
    ensure_no_links(&parent)?;
    // Same-volume cache and staging keep the final commit atomic, including removable drives.
    let cache = parent.join(".pixel-museum-setup");
    ensure_no_links(&cache)?;
    fs::create_dir_all(&cache)?;
    let lock = OpenOptions::new()
        .create(true)
        .truncate(false)
        .read(true)
        .write(true)
        .open(cache.join("setup.lock"))?;
    fs2::FileExt::try_lock_exclusive(&lock)
        .context("Another Pixel Museum installation is using this folder")?;
    let total = release.manifest.download_bytes()?;
    let installed = release.manifest.unpacked_bytes()?;
    let tar_bytes: u64 = release
        .manifest
        .packages
        .iter()
        .filter(|p| p.format == PackageFormat::Tar)
        .map(|p| p.bytes)
        .sum();
    // TARs are moved directly into staging; no second 10 GiB extracted collection is required.
    let required = total
        .checked_add(installed.saturating_sub(tar_bytes))
        .and_then(|n| n.checked_add(128 * 1024 * 1024))
        .context("Required disk space overflow")?;
    let cached: u64 = release
        .manifest
        .packages
        .iter()
        .map(|p| {
            let name = cached_path(&cache, p);
            fs::metadata(&name)
                .map(|m| m.len().min(p.bytes))
                .unwrap_or(0)
        })
        .sum();
    let available = fs2::available_space(&parent).context("Cannot check free disk space")?;
    ensure!(
        available >= required.saturating_sub(cached),
        "Not enough free disk space: {:.2} GiB required; {:.2} GiB available",
        required.saturating_sub(cached) as f64 / 1073741824.0,
        available as f64 / 1073741824.0
    );
    let stage = tempfile::Builder::new()
        .prefix(".pixel-museum-stage-")
        .tempdir_in(&parent)
        .context("Cannot create installation staging folder")?;
    let mut processed = 0;
    let mut seen_paths = HashSet::new();
    let net = client()?;
    let sources: Vec<_> = release
        .manifest
        .packages
        .iter()
        .map(|package| InstallSource {
            package,
            local: release
                .payload_dir
                .as_ref()
                .map(|directory| directory.join(&package.filename))
                .filter(|path| path.is_file()),
            cached: cached_path(&cache, package),
        })
        .collect();
    let mut downloaded = 0;
    for (index, item) in sources.iter().enumerate() {
        check_cancel(cancel)?;
        let InstallSource {
            package: p,
            local,
            cached,
        } = item;
        if index % 2 == 0 {
            let batch = &sources[index..(index + 2).min(sources.len())];
            download_install_batch(&net, batch, cancel, |package, bytes| {
                report(Progress {
                    phase: Phase::Download,
                    package: package.to_owned(),
                    done: processed + bytes,
                    total,
                })
            })?;
            downloaded = processed + batch.iter().map(|item| item.package.bytes).sum::<u64>();
        }
        let source = local.as_ref().unwrap_or(cached);
        report(Progress {
            phase: Phase::Verify,
            package: p.id.clone(),
            done: downloaded,
            total,
        });
        let mut verified = match verify_package(source, p, cancel) {
            Ok(file) => file,
            Err(error) => {
                if local.is_none() && !cancel.load(Ordering::Relaxed) {
                    let _ = fs::remove_file(cached);
                }
                return Err(error);
            }
        };
        report(Progress {
            phase: Phase::Install,
            package: p.id.clone(),
            done: downloaded,
            total,
        });
        if p.format == PackageFormat::Tar {
            let target = stage
                .path()
                .join(safe_relative_path(&p.target)?)
                .join(format!("{}.tar", p.sha256.to_ascii_lowercase()));
            fs::create_dir_all(target.parent().unwrap())?;
            // Only our private resume cache may share a TAR with staging. Caller-owned
            // payloads are copied so later source edits cannot modify installed data.
            let mut linked = false;
            if local.is_none() && fs::hard_link(source, &target).is_ok() {
                let link = open_archive(&target)?;
                linked = crate::update::process::same_file(&verified, &link)?;
                drop(link);
                if !linked {
                    fs::remove_file(&target)?;
                }
            }
            if !linked {
                ensure!(
                    fs2::available_space(stage.path())? >= p.bytes + 32 * 1024 * 1024,
                    "The destination filesystem needs extra temporary space to install {}",
                    p.filename
                );
                copy_cancellable(&mut verified, &target, cancel)?;
            }
        } else {
            let prefix = if p.kind == PackageKind::App {
                PathBuf::new()
            } else {
                safe_relative_path(&p.target)?
            };
            extract_zip(
                &mut verified,
                stage.path(),
                &prefix,
                p.unpacked_bytes,
                &mut seen_paths,
                cancel,
            )?;
            if p.kind == PackageKind::App && registration.is_some() {
                crate::integration::validate_helper(stage.path())?;
            }
        }
        processed += p.bytes;
        report(Progress {
            phase: Phase::Install,
            package: p.id.clone(),
            done: downloaded,
            total,
        });
    }
    check_cancel(cancel)?;
    let executable = stage
        .path()
        .join(safe_relative_path(&release.manifest.executable)?);
    ensure!(
        executable.is_file(),
        "The app package does not contain {}",
        release.manifest.executable
    );
    ensure!(
        stage.path().join("LICENSE").is_file()
            && stage.path().join("THIRD_PARTY_NOTICES.md").is_file(),
        "The app package must include LICENSE and THIRD_PARTY_NOTICES.md"
    );
    let windows = if let Some(options) = registration {
        crate::integration::validate_helper(stage.path())?;
        Some(crate::integration::registration(
            destination,
            language,
            options.desktop_shortcut,
        )?)
    } else {
        None
    };
    write_install_metadata(stage.path(), release, language)?;
    if let Some(windows) = &windows {
        let receipt = stage.path().join(crate::integration::RECEIPT);
        let mut value: serde_json::Value = serde_json::from_slice(&fs::read(&receipt)?)?;
        value["windows_integration"] = serde_json::to_value(windows)?;
        fs::write(receipt, serde_json::to_vec_pretty(&value)?)?;
    }
    validate_destination(destination)?;
    let previous = if destination.exists() && fs::read_dir(destination)?.next().is_some() {
        let previous = uninstalled_folder(destination, destination)?;
        preserve_personal_files(&previous, destination, stage.path(), cancel)?;
        ensure!(
            uninstalled_folder(destination, destination)? == previous,
            "Uninstalled folder changed during reinstall; original files were preserved"
        );
        Some(previous)
    } else {
        None
    };
    // This short final operation cannot be interrupted after the commit begins.
    begin_commit()?;
    report(Progress {
        phase: Phase::Finish,
        package: String::new(),
        done: total,
        total,
    });
    // Never give TempDir automatic recursive ownership of the original data.
    // A failed rollback must leave its recovery folder intact.
    let backup = if let Some(previous) = &previous {
        let backup = tempfile::Builder::new()
            .prefix(".pixel-museum-reinstall-")
            .tempdir_in(&parent)?
            .keep();
        if let Err(error) = fs::rename(destination, backup.join("previous")) {
            let _ = fs::remove_dir(&backup);
            return Err(error).context("Cannot retain the old installation for safe reinstall");
        }
        let backup = Some(backup);
        let checked = uninstalled_folder(&backup.as_ref().unwrap().join("previous"), destination)
            .and_then(|actual| {
                ensure!(
                    actual == *previous,
                    "Uninstalled folder changed during commit"
                );
                Ok(())
            });
        if let Err(error) = checked {
            restore_reinstall(&backup, destination)?;
            return Err(error);
        }
        backup
    } else {
        None
    };
    if destination.exists() {
        fs::remove_dir(destination).context("Cannot replace the empty destination folder")?;
    }
    let staging_path = stage.path().to_path_buf();
    if let Err(error) = fs::rename(&staging_path, destination) {
        restore_reinstall(&backup, destination)?;
        return Err(error).context("Cannot finish installation; previous files were preserved");
    }
    if let (Some(options), Some(windows)) = (registration, &windows) {
        if let Err(error) = crate::integration::register(
            destination,
            &release.manifest.version,
            release.manifest.unpacked_bytes()?,
            windows,
            &options.environment,
        ) {
            match fs::rename(destination, &staging_path) {
                Ok(()) => {
                    restore_reinstall(&backup, destination)?;
                    return Err(error);
                }
                Err(rollback) => bail!(
                    "Application files are installed at {}, but Windows registration failed: {error:#}. Rollback could not move the folder: {rollback}. Previous data recovery folder: {:?}",
                    destination.display(),
                    backup
                ),
            }
        }
    }
    if let (Some(backup), Some(previous)) = (&backup, &previous) {
        if let Err(error) = clean_retired_folder(&backup.join("previous"), destination, previous) {
            eprintln!(
                "Installation succeeded; previous data retained at {}: {error:#}",
                backup.display()
            );
        } else {
            let _ = fs::remove_dir(backup);
        }
    }
    // TempDir no longer owns a directory after rename. Its normal drop is harmless.
    drop(stage);
    for p in &release.manifest.packages {
        let _ = fs::remove_file(cached_path(&cache, p));
    }
    drop(lock);
    let _ = fs::remove_file(cache.join("setup.lock"));
    let _ = fs::remove_dir(&cache);
    Ok(())
}

struct InstallSource<'a> {
    package: &'a Package,
    local: Option<PathBuf>,
    cached: PathBuf,
}

fn download_install_batch(
    client: &Client,
    sources: &[InstallSource<'_>],
    cancel: &AtomicBool,
    mut report: impl FnMut(&str, u64),
) -> Result<()> {
    // A shared SHA produces a shared resume file. Only one writer may use that path.
    let mut remote = sources.iter().filter(|item| item.local.is_none());
    let Some(first) = remote.next() else {
        return Ok(());
    };
    let second = remote.next();
    let mut report_serial = |item: &InstallSource<'_>, prefix| {
        let mut peak = 0;
        download(client, item.package, &item.cached, cancel, |bytes| {
            peak = peak.max(bytes);
            report(&item.package.id, prefix + peak)
        })
    };
    let Some(second) = second else {
        return report_serial(first, 0);
    };
    if first.cached == second.cached {
        report_serial(first, 0)?;
        return report_serial(second, first.package.bytes);
    }

    enum DownloadEvent {
        Progress { index: usize, bytes: u64 },
        Finished(Result<()>),
    }

    let stop = AtomicBool::new(false);
    std::thread::scope(|scope| {
        let (sender, events) = std::sync::mpsc::channel();
        let pair = [first, second];
        for (index, item) in pair.iter().copied().enumerate() {
            let sender = sender.clone();
            let stop = &stop;
            scope.spawn(move || {
                let result = download_with_check(
                    client,
                    item.package,
                    &item.cached,
                    || {
                        check_cancel(cancel)?;
                        check_cancel(stop)
                    },
                    |bytes| {
                        let _ = sender.send(DownloadEvent::Progress { index, bytes });
                    },
                );
                let failed = result.is_err();
                let _ = sender.send(DownloadEvent::Finished(result));
                if failed {
                    stop.store(true, Ordering::Relaxed);
                }
            });
        }
        drop(sender);
        let mut progress = [0, 0];
        let mut outcome = Ok(());
        for event in events {
            match event {
                DownloadEvent::Progress { index, bytes } => {
                    progress[index] = progress[index].max(bytes);
                    report(&pair[index].package.id, progress.iter().sum());
                }
                DownloadEvent::Finished(Err(error)) if outcome.is_ok() => outcome = Err(error),
                DownloadEvent::Finished(_) => {}
            }
        }
        outcome
    })
}

fn cached_path(cache: &Path, p: &Package) -> PathBuf {
    cache.join(format!(
        "{}.{}.part",
        p.sha256.to_ascii_lowercase(),
        if p.format == PackageFormat::Zip {
            "zip"
        } else {
            "tar"
        }
    ))
}

fn download(
    client: &Client,
    package: &Package,
    target: &Path,
    cancel: &AtomicBool,
    progress: impl FnMut(u64),
) -> Result<()> {
    download_with_check(client, package, target, || check_cancel(cancel), progress)
}

fn download_with_check(
    client: &Client,
    package: &Package,
    target: &Path,
    check: impl Fn() -> Result<()>,
    mut progress: impl FnMut(u64),
) -> Result<()> {
    check()?;
    ensure_no_links(target)?;
    let mut out = writable_cache(target)?;
    let mut offset = out.metadata()?.len();
    if offset > package.bytes {
        out.set_len(0)?;
        offset = 0;
    }
    progress(offset);
    if offset == package.bytes {
        return Ok(());
    }
    let url = package.url.as_deref().with_context(|| {
        format!(
            "{} is missing. Put it beside the manifest or use a manifest with download URLs.",
            package.filename
        )
    })?;
    validate_release_url(url)?;
    check()?;
    let mut request = client.get(url).header(ACCEPT_ENCODING, "identity");
    if offset > 0 {
        request = request.header(RANGE, format!("bytes={offset}-"));
    }
    let mut response = request
        .send()
        .with_context(|| format!("Cannot download {}. Retry to resume.", package.id))?
        .error_for_status()?;
    let append = offset > 0 && response.status() == reqwest::StatusCode::PARTIAL_CONTENT;
    if append {
        let range = response
            .headers()
            .get(CONTENT_RANGE)
            .context("Resume response has no Content-Range")?
            .to_str()?;
        let expected =
            format!("bytes {offset}-{} /{}", package.bytes - 1, package.bytes).replace(" /", "/");
        ensure!(range == expected, "Invalid resume range for {}", package.id);
    } else {
        ensure!(
            response.status() == reqwest::StatusCode::OK,
            "Unexpected download response for {}",
            package.id
        );
        offset = 0;
    }
    if let Some(len) = response.content_length() {
        ensure!(
            len == package.bytes - offset,
            "Download size differs from the trusted manifest"
        );
    }
    check()?;
    if append {
        out.seek(SeekFrom::End(0))?;
    } else {
        out.set_len(0)?;
        out.seek(SeekFrom::Start(0))?;
    }
    let mut buffer = vec![0u8; 256 * 1024];
    let mut count = offset;
    let mut tick = Instant::now();
    loop {
        check()?;
        let n = response.read(&mut buffer).with_context(|| {
            format!("Download interrupted for {}. Retry to resume.", package.id)
        })?;
        if n == 0 {
            break;
        }
        count = count
            .checked_add(n as u64)
            .context("Download size overflow")?;
        ensure!(count <= package.bytes, "Download exceeds its trusted size");
        out.write_all(&buffer[..n])?;
        if tick.elapsed() > Duration::from_millis(80) {
            progress(count);
            tick = Instant::now();
        }
    }
    out.sync_all()?;
    ensure!(
        count == package.bytes,
        "Incomplete download for {}. Retry to resume.",
        package.id
    );
    progress(count);
    Ok(())
}

fn open_archive(path: &Path) -> Result<File> {
    ensure_no_links(path)?;
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt;
        options.share_mode(5).custom_flags(0x0020_0000);
    } // No writes; keep this verified object even if its name changes.
    let file = options
        .open(path)
        .with_context(|| format!("Cannot open {}", path.display()))?;
    crate::update::process::validate_regular_handle(&file, false)?;
    Ok(file)
}

fn writable_cache(path: &Path) -> Result<File> {
    ensure_no_links(path)?;
    let mut options = OpenOptions::new();
    options.read(true).write(true).create(true).truncate(false);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt;
        options.share_mode(1).custom_flags(0x0020_0000);
    }
    let file = options.open(path)?;
    crate::update::process::validate_regular_handle(&file, true)?;
    Ok(file)
}

pub fn verify_package(path: &Path, package: &Package, cancel: &AtomicBool) -> Result<File> {
    let mut file = open_archive(path)?;
    ensure!(
        file.metadata()?.len() == package.bytes,
        "Incorrect file size for {}",
        package.filename
    );
    let mut digest = Sha256::new();
    let mut buffer = vec![0u8; 1024 * 1024];
    loop {
        check_cancel(cancel)?;
        let n = file.read(&mut buffer)?;
        if n == 0 {
            break;
        }
        digest.update(&buffer[..n]);
    }
    ensure!(
        format!("{:x}", digest.finalize()).eq_ignore_ascii_case(&package.sha256),
        "SHA-256 verification failed for {}. The package has not been installed.",
        package.filename
    );
    file.seek(SeekFrom::Start(0))?;
    Ok(file)
}

fn copy_cancellable(source: &mut File, to: &Path, cancel: &AtomicBool) -> Result<()> {
    let mut out = OpenOptions::new().create_new(true).write(true).open(to)?;
    let mut buffer = vec![0u8; 1024 * 1024];
    loop {
        check_cancel(cancel)?;
        let n = source.read(&mut buffer)?;
        if n == 0 {
            break;
        }
        out.write_all(&buffer[..n])?;
    }
    out.sync_all()?;
    Ok(())
}

fn extract_zip(
    source: &mut File,
    stage: &Path,
    prefix: &Path,
    expected_size: u64,
    seen: &mut HashSet<String>,
    cancel: &AtomicBool,
) -> Result<()> {
    let mut archive = zip::ZipArchive::new(source).context("Cannot open verified ZIP archive")?;
    ensure!(
        archive.len() <= 200_000,
        "Archive contains too many entries"
    );
    let mut unpacked = 0u64;
    let mut buffer = vec![0u8; 256 * 1024];
    for index in 0..archive.len() {
        check_cancel(cancel)?;
        let mut item = archive.by_index(index)?;
        ensure!(
            !item.is_symlink(),
            "Symbolic links are not supported in installation archives"
        );
        // Older Windows ZIP writers use backslashes. Normalise separators before
        // applying the same traversal, drive-prefix and device-name checks.
        let name = item.name()?.replace('\\', "/");
        let relative = safe_relative_path(&name)?;
        ensure!(
            item.enclosed_name().is_some(),
            "Archive entry escapes installation folder"
        );
        let relative = prefix.join(relative);
        let key = relative.to_string_lossy().replace('\\', "/").to_lowercase();
        let target = stage.join(&relative);
        if item.is_dir() {
            fs::create_dir_all(&target)?;
            continue;
        }
        ensure!(item.is_file(), "Unsupported archive entry type");
        ensure!(
            seen.insert(key),
            "Archive contains duplicate or conflicting paths: {name}"
        );
        unpacked = unpacked
            .checked_add(item.size())
            .context("Unpacked size overflow")?;
        ensure!(
            unpacked <= expected_size,
            "Archive exceeds its trusted installed size"
        );
        ensure_no_links(&target)?;
        fs::create_dir_all(target.parent().context("Archive path has no parent")?)?;
        let mut output = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&target)
            .with_context(|| format!("Cannot create {}", target.display()))?;
        let expected_file_size = item.size();
        let mut copied = 0u64;
        loop {
            check_cancel(cancel)?;
            let n = item.read(&mut buffer)?;
            if n == 0 {
                break;
            }
            copied = copied
                .checked_add(n as u64)
                .context("Archive entry size overflow")?;
            ensure!(
                copied <= expected_file_size,
                "Archive entry exceeds its declared size"
            );
            output.write_all(&buffer[..n])?;
        }
        ensure!(
            copied == expected_file_size,
            "Archive entry is shorter than its declared size"
        );
        output.sync_all()?;
    }
    ensure!(
        unpacked == expected_size,
        "Archive installed size differs from the trusted manifest"
    );
    Ok(())
}

fn write_install_metadata(stage: &Path, release: &Release, language: &str) -> Result<()> {
    fs::create_dir_all(stage.join("collection"))?;
    fs::write(
        stage.join("pixel-museum-install.json"),
        serde_json::to_vec_pretty(&json!({
            "schema_version": 1, "version": release.manifest.version,
            "language": language, "executable": release.manifest.executable,
            "collection": "collection", "packages": release.manifest.packages,
        }))?,
    )?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Cursor;

    fn zip_bytes(entries: &[(&str, &[u8])]) -> Vec<u8> {
        let mut zip = zip::ZipWriter::new(Cursor::new(Vec::new()));
        for (name, bytes) in entries {
            zip.start_file(*name, zip::write::SimpleFileOptions::default())
                .unwrap();
            zip.write_all(bytes).unwrap();
        }
        zip.finish().unwrap().into_inner()
    }

    fn package(id: &str, kind: PackageKind, bytes: &[u8], size: u64) -> Package {
        Package {
            id: id.into(),
            kind,
            filename: format!("{id}.zip"),
            format: PackageFormat::Zip,
            url: None,
            sha256: format!("{:x}", Sha256::digest(bytes)),
            bytes: bytes.len() as u64,
            unpacked_bytes: size,
            target: if kind == PackageKind::App {
                "."
            } else {
                "collection"
            }
            .into(),
        }
    }

    #[test]
    fn installs_verified_local_payload_and_keeps_everything_together() {
        let folder = tempfile::tempdir().unwrap();
        let app = zip_bytes(&[
            ("Pixel Museum.exe", b"test"),
            ("LICENSE", b"GPL"),
            ("THIRD_PARTY_NOTICES.md", b"terms"),
        ]);
        let data = zip_bytes(&[("images/test.webp", b"image")]);
        fs::write(folder.path().join("app.zip"), &app).unwrap();
        fs::write(folder.path().join("images.zip"), &data).unwrap();
        let release = Release {
            manifest: Manifest {
                updates: Vec::new(),
                schema_version: 1,
                version: "test".into(),
                executable: "Pixel Museum.exe".into(),
                packages: vec![
                    package("app", PackageKind::App, &app, 12),
                    package("images", PackageKind::Collection, &data, 5),
                ],
            },
            payload_dir: Some(folder.path().to_path_buf()),
        };
        let root = folder.path().join("Pixel Museum");
        install(&release, &root, "it", &AtomicBool::new(false), |_| {}).unwrap();
        assert_eq!(
            fs::read(root.join("collection/images/test.webp")).unwrap(),
            b"image"
        );
        assert!(root.join("Pixel Museum.exe").is_file());
        assert!(root.join("pixel-museum-install.json").is_file());
        assert!(
            !root.join("preferences.json").exists(),
            "Installer language must not preselect the app language"
        );
        assert!(install(&release, &root, "it", &AtomicBool::new(false), |_| {}).is_err());
    }

    #[test]
    fn rejects_archive_escape_without_writing_outside_stage() {
        let folder = tempfile::tempdir().unwrap();
        let path = folder.path().join("bad.zip");
        fs::write(&path, zip_bytes(&[("../escape", b"bad")])).unwrap();
        let stage = folder.path().join("stage");
        fs::create_dir(&stage).unwrap();
        assert!(
            extract_zip(
                &mut open_archive(&path).unwrap(),
                &stage,
                Path::new(""),
                3,
                &mut HashSet::new(),
                &AtomicBool::new(false)
            )
            .is_err()
        );
        assert!(!folder.path().join("escape").exists());
    }

    #[test]
    fn registered_fixture_uses_verified_payload_helper_and_leaves_app_language_unselected() {
        let folder = tempfile::tempdir().unwrap();
        let executable = fs::read(
            PathBuf::from(std::env::var_os("SystemRoot").unwrap()).join("System32/whoami.exe"),
        )
        .unwrap();
        let mut payload_helper = executable.clone();
        payload_helper.extend_from_slice(crate::integration::HELPER_CAPABILITY);
        let entries = [
            ("Pixel Museum.exe", executable.as_slice()),
            ("LICENSE", b"GPL"),
            ("THIRD_PARTY_NOTICES.md", b"terms"),
            (crate::integration::HELPER, payload_helper.as_slice()),
        ];
        let inventory = crate::update::Inventory {
            schema_version: 1,
            application_id: "pixel-museum".into(),
            platform: "windows-x64".into(),
            version: "0.2.0".into(),
            files: entries
                .iter()
                .map(|(name, bytes)| crate::update::OwnedFile {
                    path: (*name).into(),
                    bytes: bytes.len() as u64,
                    sha256: format!("{:x}", Sha256::digest(bytes)),
                })
                .collect(),
        };
        let inventory = serde_json::to_vec(&inventory).unwrap();
        let app = zip_bytes(&[
            entries[0],
            entries[1],
            entries[2],
            entries[3],
            ("application-files.json", &inventory),
        ]);
        let data = zip_bytes(&[("fixture.json", b"ok")]);
        fs::write(folder.path().join("app.zip"), &app).unwrap();
        fs::write(folder.path().join("images.zip"), &data).unwrap();
        let release = Release {
            manifest: Manifest {
                updates: Vec::new(),
                schema_version: 1,
                version: "0.2.0".into(),
                executable: "Pixel Museum.exe".into(),
                packages: vec![
                    package(
                        "app",
                        PackageKind::App,
                        &app,
                        executable.len() as u64
                            + 8
                            + inventory.len() as u64
                            + payload_helper.len() as u64,
                    ),
                    package("images", PackageKind::Collection, &data, 2),
                ],
            },
            payload_dir: Some(folder.path().to_path_buf()),
        };
        let root = folder.path().join("Pixel Museum");
        let environment = crate::integration::Environment {
            programs: folder.path().join("Programs"),
            desktop: folder.path().join("Desktop"),
            registry_base: format!(
                r"Software\PixelMuseum\InstallerTests\{}",
                folder.path().file_name().unwrap().to_string_lossy()
            ),
        };
        fs::create_dir_all(&environment.desktop).unwrap();
        let context = InstallRegistration {
            environment: environment.clone(),
            desktop_shortcut: false,
        };
        install_with_registration(
            &release,
            &root,
            "it",
            &AtomicBool::new(false),
            |_| {},
            Some(&context),
        )
        .unwrap();
        assert!(environment.program_link().is_file());
        assert!(!environment.desktop_link().exists());
        assert!(!root.join("preferences.json").exists());
        let inventory: crate::update::Inventory =
            serde_json::from_slice(&fs::read(root.join("application-files.json")).unwrap())
                .unwrap();
        let helper = inventory
            .files
            .iter()
            .find(|f| f.path == crate::integration::HELPER)
            .unwrap();
        assert_eq!(
            crate::update::hash_file(&root.join(crate::integration::HELPER)).unwrap(),
            helper.sha256
        );
        assert_eq!(
            fs::read(root.join(crate::integration::HELPER)).unwrap(),
            payload_helper,
            "Setup must never replace the payload helper with its own image"
        );
        let mut receipt: serde_json::Value =
            serde_json::from_slice(&fs::read(root.join(crate::integration::RECEIPT)).unwrap())
                .unwrap();
        let registration: crate::integration::Registration =
            serde_json::from_value(receipt["windows_integration"].clone()).unwrap();
        assert!(!registration.desktop_shortcut);
        crate::integration::unregister(&root, &registration, &environment).unwrap();

        // Model only the exact V3 residue, with an older owned helper, all three
        // kinds of personal progress, and an empty framework lock.
        for name in [
            "Pixel Museum.exe",
            "LICENSE",
            "THIRD_PARTY_NOTICES.md",
            "application-files.json",
        ] {
            fs::remove_file(root.join(name)).unwrap();
        }
        fs::remove_file(root.join("collection/fixture.json")).unwrap();
        let old_helper = [payload_helper.as_slice(), b"previous owned version"].concat();
        fs::write(root.join(crate::integration::HELPER), &old_helper).unwrap();
        receipt["uninstalled"] = json!(true);
        receipt["windows_registered"] = json!(false);
        receipt["personal_data_preserved"] = json!(true);
        receipt["retained_maintenance_helper"] = json!(crate::integration::HELPER);
        receipt["retained_maintenance_helper_sha256"] =
            json!(format!("{:x}", Sha256::digest(&old_helper)));
        let receipt_bytes = serde_json::to_vec_pretty(&receipt).unwrap();
        fs::write(root.join(crate::integration::RECEIPT), &receipt_bytes).unwrap();
        for name in PERSONAL_FILES {
            fs::write(root.join(name), format!("original {name}\r\n\u{1a}")).unwrap();
        }
        fs::create_dir(root.join("application-updates")).unwrap();
        fs::write(root.join("application-updates/apply.lock"), []).unwrap();
        let original = uninstalled_folder(&root, &root).unwrap();
        assert!(validate_destination(&root).is_ok());

        fs::write(root.join("notes.txt"), b"unrelated").unwrap();
        assert!(validate_destination(&root).is_err());
        assert_eq!(fs::read(root.join("notes.txt")).unwrap(), b"unrelated");
        fs::remove_file(root.join("notes.txt")).unwrap();
        fs::write(root.join("application-updates/apply.lock"), b"busy").unwrap();
        assert!(validate_destination(&root).is_err());
        fs::write(root.join("application-updates/apply.lock"), []).unwrap();
        let alias = folder.path().join("progress-alias");
        fs::hard_link(root.join("preferences.json"), &alias).unwrap();
        assert!(validate_destination(&root).is_err());
        fs::remove_file(alias).unwrap();
        receipt["windows_integration"]["installation_id"] = json!("different-root");
        fs::write(
            root.join(crate::integration::RECEIPT),
            serde_json::to_vec(&receipt).unwrap(),
        )
        .unwrap();
        assert!(validate_destination(&root).is_err());
        fs::write(root.join(crate::integration::RECEIPT), &receipt_bytes).unwrap();
        fs::write(root.join(crate::integration::HELPER), b"changed").unwrap();
        assert!(validate_destination(&root).is_err());
        fs::write(root.join(crate::integration::HELPER), &old_helper).unwrap();

        let collision = tempfile::tempdir_in(folder.path()).unwrap();
        fs::write(
            collision.path().join("preferences.json"),
            b"package collision",
        )
        .unwrap();
        assert!(
            preserve_personal_files(&original, &root, collision.path(), &AtomicBool::new(false))
                .is_err()
        );
        assert_eq!(uninstalled_folder(&root, &root).unwrap(), original);

        // A foreign shortcut makes registration fail after the folder commit.
        // Both the old receipt/helper and every personal file must be restored.
        fs::create_dir_all(environment.program_link().parent().unwrap()).unwrap();
        fs::write(environment.program_link(), b"foreign shortcut").unwrap();
        assert!(
            install_with_registration(
                &release,
                &root,
                "it",
                &AtomicBool::new(false),
                |_| {},
                Some(&context)
            )
            .is_err()
        );
        assert_eq!(uninstalled_folder(&root, &root).unwrap(), original);
        assert_eq!(
            fs::read(environment.program_link()).unwrap(),
            b"foreign shortcut"
        );
        fs::remove_file(environment.program_link()).unwrap();

        install_with_registration(
            &release,
            &root,
            "it",
            &AtomicBool::new(false),
            |_| {},
            Some(&context),
        )
        .unwrap();
        for name in PERSONAL_FILES {
            assert_eq!(
                fs::read(root.join(name)).unwrap(),
                format!("original {name}\r\n\u{1a}").as_bytes()
            );
        }
        assert_eq!(
            fs::read(root.join(crate::integration::HELPER)).unwrap(),
            payload_helper
        );
        assert!(!root.join("application-updates/apply.lock").exists());
        assert!(root.join("Pixel Museum.exe").is_file());
        let fresh: serde_json::Value =
            serde_json::from_slice(&fs::read(root.join(crate::integration::RECEIPT)).unwrap())
                .unwrap();
        assert_ne!(fresh["uninstalled"], true);
        assert!(
            validate_destination(&root).is_err(),
            "An active installation cannot be merged"
        );
        assert!(!fs::read_dir(folder.path()).unwrap().any(|entry| {
            entry
                .unwrap()
                .file_name()
                .to_string_lossy()
                .starts_with(".pixel-museum-reinstall-")
        }));
        crate::integration::unregister(&root, &registration, &environment).unwrap();
        // Explicit full cleanup can leave only its mapped owned helper/receipt.
        let mut full = fresh;
        full["uninstalled"] = json!(true);
        full["windows_registered"] = json!(false);
        full["personal_data_preserved"] = json!(false);
        full["retained_maintenance_helper"] = json!(crate::integration::HELPER);
        full["retained_maintenance_helper_sha256"] =
            json!(format!("{:x}", Sha256::digest(&payload_helper)));
        for name in [
            "Pixel Museum.exe",
            "LICENSE",
            "THIRD_PARTY_NOTICES.md",
            "application-files.json",
        ] {
            fs::remove_file(root.join(name)).unwrap();
        }
        fs::remove_file(root.join("collection/fixture.json")).unwrap();
        fs::write(
            root.join(crate::integration::RECEIPT),
            serde_json::to_vec(&full).unwrap(),
        )
        .unwrap();
        assert!(
            validate_destination(&root).is_err(),
            "Full cleanup must be explicit"
        );
        full["full_folder_cleanup_requested"] = json!(true);
        fs::write(
            root.join(crate::integration::RECEIPT),
            serde_json::to_vec(&full).unwrap(),
        )
        .unwrap();
        assert!(
            validate_destination(&root).is_err(),
            "Full cleanup must contain zero progress files"
        );
        for name in PERSONAL_FILES {
            fs::remove_file(root.join(name)).unwrap();
        }
        assert!(validate_destination(&root).is_ok());
        install_with_registration(
            &release,
            &root,
            "it",
            &AtomicBool::new(false),
            |_| {},
            Some(&context),
        )
        .unwrap();
        for name in PERSONAL_FILES {
            assert!(!root.join(name).exists());
        }
        crate::integration::unregister(&root, &registration, &environment).unwrap();
        environment.cleanup_fixture();
    }

    #[test]
    fn rejects_hash_mismatch_and_cancellation() {
        let folder = tempfile::tempdir().unwrap();
        let path = folder.path().join("app.zip");
        fs::write(&path, b"bad").unwrap();
        let p = package("app", PackageKind::App, b"new", 3);
        assert!(verify_package(&path, &p, &AtomicBool::new(false)).is_err());
        assert!(verify_package(&path, &p, &AtomicBool::new(true)).is_err());
    }

    #[test]
    fn retained_tar_survives_failed_install_and_retry_commits_without_extraction() {
        let folder = tempfile::tempdir().unwrap();
        let app = zip_bytes(&[
            ("Pixel Museum.exe", b"test"),
            ("LICENSE", b"GPL"),
            ("THIRD_PARTY_NOTICES.md", b"terms"),
        ]);
        let tar = vec![0u8; 1024];
        let tail = zip_bytes(&[("receipt.json", b"ok")]);
        let mut retained = package("images-001", PackageKind::Collection, &tar, 1024);
        retained.format = PackageFormat::Tar;
        retained.filename = "images-001.tar".into();
        retained.target = "collection/test-ready/archives".into();
        let release = Release {
            manifest: Manifest {
                updates: Vec::new(),
                schema_version: 1,
                version: "test".into(),
                executable: "Pixel Museum.exe".into(),
                packages: vec![
                    package("app", PackageKind::App, &app, 12),
                    retained.clone(),
                    package("tail", PackageKind::Collection, &tail, 2),
                ],
            },
            payload_dir: None,
        };
        let cache = folder.path().join(".pixel-museum-setup");
        fs::create_dir(&cache).unwrap();
        for (p, data) in release.manifest.packages.iter().zip([&app, &tar, &tail]) {
            fs::write(cached_path(&cache, p), data).unwrap();
        }
        let tail_path = cached_path(&cache, &release.manifest.packages[2]);
        let mut corrupt = tail.clone();
        corrupt[0] ^= 1;
        fs::write(&tail_path, corrupt).unwrap();
        let destination = folder.path().join("Pixel Museum");
        assert!(
            install(
                &release,
                &destination,
                "en",
                &AtomicBool::new(false),
                |_| {}
            )
            .is_err()
        );
        assert!(!destination.exists());
        assert_eq!(fs::read(cached_path(&cache, &retained)).unwrap(), tar);
        fs::write(tail_path, &tail).unwrap();
        let mut progress = Vec::new();
        install(
            &release,
            &destination,
            "en",
            &AtomicBool::new(false),
            |event| progress.push((event.phase, event.done)),
        )
        .unwrap();
        assert!(progress.windows(2).all(|pair| pair[0].1 <= pair[1].1));
        assert_eq!(
            progress.iter().find(|(phase, _)| *phase == Phase::Verify),
            Some(&(Phase::Verify, (app.len() + tar.len()) as u64))
        );
        assert_eq!(
            fs::read(
                destination
                    .join(&retained.target)
                    .join(format!("{}.tar", retained.sha256))
            )
            .unwrap(),
            tar
        );
        assert!(!cache.exists());
    }

    #[test]
    fn extraction_consumes_verified_file_object_when_input_path_is_replaced() {
        let folder = tempfile::tempdir().unwrap();
        let path = folder.path().join("app.zip");
        let bytes = zip_bytes(&[("safe.txt", b"safe")]);
        fs::write(&path, &bytes).unwrap();
        let mut verified = verify_package(
            &path,
            &package("app", PackageKind::App, &bytes, 4),
            &AtomicBool::new(false),
        )
        .unwrap();
        let moved = folder.path().join("original.zip");
        fs::rename(&path, &moved).unwrap();
        fs::write(&path, zip_bytes(&[("../escape", b"bad")])).unwrap();
        assert!(
            OpenOptions::new().write(true).open(&moved).is_err(),
            "Verified bytes must remain immutable through any alias"
        );
        let stage = folder.path().join("stage");
        fs::create_dir(&stage).unwrap();
        extract_zip(
            &mut verified,
            &stage,
            Path::new(""),
            4,
            &mut HashSet::new(),
            &AtomicBool::new(false),
        )
        .unwrap();
        assert_eq!(fs::read(stage.join("safe.txt")).unwrap(), b"safe");
        assert!(!folder.path().join("escape").exists());
    }

    #[test]
    fn writable_download_cache_rejects_hardlinks_before_any_truncation_or_write() {
        let folder = tempfile::tempdir().unwrap();
        let outside = folder.path().join("personal.txt");
        let cache = folder.path().join("cached.part");
        fs::write(&outside, b"personal sentinel").unwrap();
        fs::hard_link(&outside, &cache).unwrap();
        assert!(writable_cache(&cache).is_err());
        let p = package("app", PackageKind::App, b"other", 5);
        assert!(
            download(
                &client().unwrap(),
                &p,
                &cache,
                &AtomicBool::new(false),
                |_| {}
            )
            .is_err()
        );
        assert_eq!(fs::read(&outside).unwrap(), b"personal sentinel");
    }

    #[test]
    fn caller_owned_tar_is_copied_without_a_mutable_source_alias() {
        let folder = tempfile::tempdir().unwrap();
        let app = zip_bytes(&[
            ("Pixel Museum.exe", b"test"),
            ("LICENSE", b"GPL"),
            ("THIRD_PARTY_NOTICES.md", b"terms"),
        ]);
        let tar = vec![0u8; 1024];
        let mut pack = package("images", PackageKind::Collection, &tar, 1024);
        pack.filename = "images.tar".into();
        pack.format = PackageFormat::Tar;
        pack.target = "collection/ready/archives".into();
        fs::write(folder.path().join("app.zip"), &app).unwrap();
        let source = folder.path().join("images.tar");
        fs::write(&source, &tar).unwrap();
        let release = Release {
            manifest: Manifest {
                updates: Vec::new(),
                schema_version: 1,
                version: "fixture".into(),
                executable: "Pixel Museum.exe".into(),
                packages: vec![package("app", PackageKind::App, &app, 12), pack.clone()],
            },
            payload_dir: Some(folder.path().to_path_buf()),
        };
        let destination = folder.path().join("Pixel Museum");
        install(
            &release,
            &destination,
            "it",
            &AtomicBool::new(false),
            |_| {},
        )
        .unwrap();
        let installed = destination
            .join(&pack.target)
            .join(format!("{}.tar", pack.sha256));
        let source_handle = open_archive(&source).unwrap();
        let installed_handle = open_archive(&installed).unwrap();
        assert!(!crate::update::process::same_file(&source_handle, &installed_handle).unwrap());
        drop(source_handle);
        drop(installed_handle);
        fs::write(&source, vec![7u8; 1024]).unwrap();
        assert_eq!(fs::read(installed).unwrap(), tar);
    }
}
