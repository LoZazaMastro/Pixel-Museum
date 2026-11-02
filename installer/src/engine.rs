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
    sync::atomic::{AtomicBool, Ordering},
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
    Verify,
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
            destination.is_dir() && fs::read_dir(destination)?.next().is_none(),
            "The destination already contains files. Choose a new, empty Pixel Museum folder."
        );
    }
    Ok(parent.to_path_buf())
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

pub fn install_registered(
    release: &Release,
    destination: &Path,
    language: &str,
    desktop_shortcut: bool,
    cancel: &AtomicBool,
    report: impl FnMut(Progress),
) -> Result<()> {
    let integration = InstallRegistration {
        environment: crate::integration::Environment::current_user()?,
        desktop_shortcut,
    };
    install_with_registration(
        release,
        destination,
        language,
        cancel,
        report,
        Some(&integration),
    )
}

pub fn install_with_registration(
    release: &Release,
    destination: &Path,
    language: &str,
    cancel: &AtomicBool,
    mut report: impl FnMut(Progress),
    registration: Option<&InstallRegistration>,
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
    for p in &release.manifest.packages {
        check_cancel(cancel)?;
        let local = release
            .payload_dir
            .as_ref()
            .map(|d| d.join(&p.filename))
            .filter(|p| p.is_file());
        let cached = cached_path(&cache, p);
        let source = if let Some(local) = &local {
            local
        } else {
            download(&net, p, &cached, cancel, |n| {
                report(Progress {
                    phase: Phase::Download,
                    package: p.id.clone(),
                    done: processed + n,
                    total,
                })
            })?;
            &cached
        };
        report(Progress {
            phase: Phase::Verify,
            package: p.id.clone(),
            done: processed + p.bytes,
            total,
        });
        let mut verified = match verify_package(source, p, cancel) {
            Ok(file) => file,
            Err(error) => {
                if local.is_none() && !cancel.load(Ordering::Relaxed) {
                    let _ = fs::remove_file(&cached);
                }
                return Err(error);
            }
        };
        report(Progress {
            phase: Phase::Install,
            package: p.id.clone(),
            done: processed + p.bytes,
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
            done: processed,
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
    // This short final operation cannot be interrupted after the commit begins.
    report(Progress {
        phase: Phase::Finish,
        package: String::new(),
        done: total,
        total,
    });
    validate_destination(destination)?;
    if destination.exists() {
        fs::remove_dir(destination).context("Cannot replace the empty destination folder")?;
    }
    let staging_path = stage.path().to_path_buf();
    fs::rename(&staging_path, destination)
        .context("Cannot finish installation; no existing application files have been replaced")?;
    if let (Some(options), Some(windows)) = (registration, &windows) {
        if let Err(error) = crate::integration::register(
            destination,
            &release.manifest.version,
            release.manifest.unpacked_bytes()?,
            windows,
            &options.environment,
        ) {
            match fs::rename(destination, &staging_path) {
                Ok(()) => return Err(error),
                Err(rollback) => bail!(
                    "Application files are installed at {}, but Windows registration failed: {error:#}. Rollback could not move the folder: {rollback}",
                    destination.display()
                ),
            }
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
    mut progress: impl FnMut(u64),
) -> Result<()> {
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
    check_cancel(cancel)?;
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
        check_cancel(cancel)?;
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
        let mut buffer = vec![0u8; 256 * 1024];
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
        let receipt: serde_json::Value =
            serde_json::from_slice(&fs::read(root.join(crate::integration::RECEIPT)).unwrap())
                .unwrap();
        let registration: crate::integration::Registration =
            serde_json::from_value(receipt["windows_integration"].clone()).unwrap();
        assert!(!registration.desktop_shortcut);
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
        install(
            &release,
            &destination,
            "en",
            &AtomicBool::new(false),
            |_| {},
        )
        .unwrap();
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
