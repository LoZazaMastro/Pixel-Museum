//! Bounded, current-user uninstall. Personal data and unrecognized files are retained.
use crate::{
    integration,
    update::{self, Inventory, process},
};
use anyhow::{Context, Result, bail, ensure};
use serde::Serialize;
use std::{
    fs::{self, OpenOptions},
    path::Path,
};

const INVENTORY: &str = "application-files.json";
const EXE: &str = "Pixel Museum.exe";

pub struct Installation {
    pub language: String,
    pub registration: Option<integration::Registration>,
    inventory: Inventory,
    receipt: serde_json::Value,
    receipt_bytes: Vec<u8>,
}

pub fn inspect(root: &Path) -> Result<Installation> {
    update::ordinary_absolute(root)?;
    ensure!(root.is_dir(), "Installation folder does not exist");
    let receipt_bytes = update::read_limited(&root.join(integration::RECEIPT), 1024 * 1024)?;
    let receipt: serde_json::Value = serde_json::from_slice(&receipt_bytes)?;
    ensure!(
        receipt["schema_version"] == 1
            && receipt["executable"] == EXE
            && receipt["uninstalled"] != true,
        "This folder is not an active Pixel Museum installation"
    );
    let inventory: Inventory = serde_json::from_slice(&update::read_limited(
        &root.join(INVENTORY),
        16 * 1024 * 1024,
    )?)?;
    let files = inventory.validate()?;
    let executable = files
        .get("pixel museum.exe")
        .context("Installed application is missing from its inventory")?;
    process::executable_header(&root.join(EXE))?;
    ensure!(
        fs::metadata(root.join(EXE))?.len() == executable.bytes
            && update::hash_file(&root.join(EXE))? == executable.sha256,
        "The installed application does not match its inventory. Finish any application update before uninstalling."
    );
    let registration = receipt
        .get("windows_integration")
        .map(|r| serde_json::from_value::<integration::Registration>(r.clone()))
        .transpose()?;
    if let Some(r) = &registration {
        integration::validate(root, r)?;
    }
    let language = registration
        .as_ref()
        .map(|r| r.installer_language.as_str())
        .or_else(|| receipt["language"].as_str())
        .filter(|s| ["en", "it", "fr", "de", "es"].contains(s))
        .unwrap_or("en")
        .to_owned();
    Ok(Installation {
        language,
        registration,
        inventory,
        receipt,
        receipt_bytes,
    })
}

#[derive(Debug, Serialize)]
pub struct Outcome {
    pub schema_version: u32,
    pub removed_files: usize,
    pub retained_modified_files: Vec<String>,
    pub personal_data_preserved: bool,
    pub retained_maintenance_helper: Option<String>,
    pub cleanup_warning: Option<String>,
}

pub fn remove(root: &Path) -> Result<Outcome> {
    let installation = inspect(root)?;
    let environment = installation
        .registration
        .as_ref()
        .map(|_| integration::Environment::current_user())
        .transpose()?;
    remove_with_environment(root, environment.as_ref(), None)
}

fn remove_with_environment(
    root: &Path,
    environment: Option<&integration::Environment>,
    fail_after: Option<usize>,
) -> Result<Outcome> {
    remove_files(root, environment, fail_after, &std::env::current_exe()?)
}

pub fn retains_running_helper(root: &Path) -> bool {
    std::env::current_exe().is_ok_and(|current| {
        update::path_key(&current) == update::path_key(&root.join(integration::HELPER))
    })
}

fn remove_files(
    root: &Path,
    environment: Option<&integration::Environment>,
    fail_after: Option<usize>,
    executing: &Path,
) -> Result<Outcome> {
    let _ = inspect(root)?;
    let cache = root.join("application-updates");
    crate::manifest::ensure_no_links(&cache)?;
    fs::create_dir_all(&cache)?;
    let lock_path = cache.join("apply.lock");
    crate::manifest::ensure_no_links(&lock_path)?;
    if lock_path.exists() {
        let _ = process::open_regular(&lock_path)?;
    }
    let lock = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .open(&lock_path)?;
    fs2::FileExt::try_lock_exclusive(&lock)
        .context("An application update or uninstall is already active")?;
    let installation = inspect(root)?;
    process::assert_not_running(&root.join(EXE))?;
    ensure!(
        installation.registration.is_none() || environment.is_some(),
        "Missing current-user Windows registration environment"
    );
    let mut paths = Vec::new();
    let mut modified = Vec::new();
    let retained_helper =
        if update::path_key(executing) == update::path_key(&root.join(integration::HELPER)) {
            Some(integration::HELPER.to_owned())
        } else {
            None
        };
    for entry in &installation.inventory.files {
        // Never derive removal authority from protected or unknown inventory paths.
        if !update::allowed(&entry.path) {
            continue;
        }
        let path = root.join(crate::manifest::safe_relative_path(&entry.path)?);
        crate::manifest::ensure_no_links(&path)?;
        if !path.exists() {
            continue;
        }
        let file = process::open_regular(&path)?;
        if file.metadata()?.len() != entry.bytes || update::hash_file(&path)? != entry.sha256 {
            modified.push(entry.path.clone());
            continue;
        }
        // Keep our mapped maintenance image beside the retained personal data.
        // Do not copy, relaunch, schedule or unlink our running executable.
        if retained_helper
            .as_deref()
            .is_some_and(|p| p.eq_ignore_ascii_case(&entry.path))
        {
            continue;
        }
        paths.push(entry.path.clone());
    }
    paths.push(INVENTORY.into());
    paths.sort_by_key(|p| (p != EXE, p.clone()));
    let quarantine = tempfile::Builder::new()
        .prefix(".pixel-museum-uninstall-")
        .tempdir_in(root.parent().context("Cannot uninstall a drive root")?)?;
    let mut moved = Vec::<String>::new();
    let operation = (|| -> Result<()> {
        for path in &paths {
            if fail_after == Some(moved.len()) {
                bail!("Injected uninstall failure");
            }
            let source = root.join(path);
            let target = quarantine.path().join(path);
            crate::manifest::ensure_no_links(&source)?;
            fs::create_dir_all(target.parent().unwrap())?;
            fs::rename(&source, &target).with_context(|| {
                format!(
                    "Cannot remove {}. Close Pixel Museum and try again.",
                    source.display()
                )
            })?;
            moved.push(path.clone());
            update::atomic_json(
                &quarantine.path().join("uninstall-journal.json"),
                &serde_json::json!({"schema_version":1,"application_root":root,"files":moved}),
            )?;
        }
        let mut receipt = installation.receipt.clone();
        receipt["uninstalled"] = true.into();
        receipt["windows_registered"] = false.into();
        receipt["personal_data_preserved"] = true.into();
        receipt["retained_maintenance_helper"] = serde_json::to_value(&retained_helper)?;
        update::atomic_json(&root.join(integration::RECEIPT), &receipt)?;
        if let (Some(registration), Some(environment)) = (&installation.registration, environment) {
            integration::unregister(root, registration, environment)?;
        }
        Ok(())
    })();
    if let Err(error) = operation {
        let mut errors = Vec::new();
        if let Err(e) = atomic_bytes(
            &root.join(integration::RECEIPT),
            &installation.receipt_bytes,
        ) {
            errors.push(format!("Restore installation receipt: {e:#}"));
        }
        for path in moved.iter().rev() {
            let source = quarantine.path().join(path);
            let destination = root.join(path);
            if destination.exists() {
                errors.push(format!(
                    "Refusing to replace {} during rollback",
                    destination.display()
                ));
                continue;
            }
            if let Err(e) = fs::rename(source, &destination) {
                errors.push(format!("Restore {path}: {e}"));
            }
        }
        if !errors.is_empty() {
            let recovery = quarantine.keep();
            bail!(
                "{error:#}\nUninstall rollback needs attention. Keep recovery files at {}.\n{}",
                recovery.display(),
                errors.join("\n")
            );
        }
        return Err(error.context("Uninstall cancelled; application files restored"));
    }
    let cleanup_warning = quarantine
        .close()
        .err()
        .map(|e| format!("Application removed; temporary owned-file cleanup failed: {e}"));
    let mut directories = std::collections::BTreeSet::new();
    for path in &moved {
        let mut parent = Path::new(path).parent();
        while let Some(relative) = parent {
            if relative.as_os_str().is_empty() {
                break;
            }
            directories.insert(relative.to_path_buf());
            parent = relative.parent();
        }
    }
    let mut directories: Vec<_> = directories.into_iter().collect();
    directories.sort_by_key(|p| std::cmp::Reverse(p.components().count()));
    for directory in directories {
        let path = root.join(directory);
        if crate::manifest::ensure_no_links(&path).is_ok() {
            let _ = fs::remove_dir(path);
        }
    }
    Ok(Outcome {
        schema_version: 1,
        removed_files: moved.len(),
        retained_modified_files: modified,
        personal_data_preserved: true,
        retained_maintenance_helper: retained_helper,
        cleanup_warning,
    })
}

fn atomic_bytes(path: &Path, bytes: &[u8]) -> Result<()> {
    use std::io::Write;
    crate::manifest::ensure_no_links(path)?;
    let mut file = tempfile::NamedTempFile::new_in(path.parent().unwrap())?;
    file.write_all(bytes)?;
    file.as_file().sync_all()?;
    file.persist(path)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use sha2::{Digest, Sha256};
    use std::path::PathBuf;
    fn fixture() -> (tempfile::TempDir, PathBuf, integration::Environment) {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path().join("Pixel Museum");
        fs::create_dir(&root).unwrap();
        let pe = fs::read(
            PathBuf::from(std::env::var_os("SystemRoot").unwrap()).join("System32/whoami.exe"),
        )
        .unwrap();
        let mut inventory = Inventory {
            schema_version: 1,
            application_id: "pixel-museum".into(),
            platform: "windows-x64".into(),
            version: "0.2.0".into(),
            files: Vec::new(),
        };
        for (name, bytes) in [
            (EXE, pe.as_slice()),
            (integration::HELPER, pe.as_slice()),
            ("assets/owned.txt", b"asset"),
            ("LICENSE", b"GPL"),
            ("preferences.json", b"packaged poison"),
        ] {
            let path = root.join(name);
            fs::create_dir_all(path.parent().unwrap()).unwrap();
            fs::write(&path, bytes).unwrap();
            inventory.files.push(update::OwnedFile {
                path: name.into(),
                bytes: bytes.len() as u64,
                sha256: format!("{:x}", Sha256::digest(bytes)),
            });
        }
        update::atomic_json(&root.join(INVENTORY), &inventory).unwrap();
        let environment = integration::Environment {
            programs: temp.path().join("Programs"),
            desktop: temp.path().join("Desktop"),
            registry_base: format!(
                r"Software\PixelMuseum\InstallerTests\{}",
                temp.path().file_name().unwrap().to_string_lossy()
            ),
        };
        fs::create_dir(&environment.programs).unwrap();
        fs::create_dir(&environment.desktop).unwrap();
        let r = integration::registration(&root, "it", true).unwrap();
        update::atomic_json(
            &root.join(integration::RECEIPT),
            &serde_json::json!({"schema_version":1,"executable":EXE,"windows_integration":r}),
        )
        .unwrap();
        integration::register(&root, "0.2.0", 1234, &r, &environment).unwrap();
        for (name, bytes) in [
            (
                "preferences.json",
                b"personal language not chosen".as_slice(),
            ),
            ("video-settings.json", b"video"),
            ("trophies-v1.dat", b"trophies"),
            ("collection/archives/sentinel.tar", b"TAR"),
            ("database/receipt.json", b"DB"),
            ("logs/session.log", b"LOG"),
            ("assets/personal-photo.jpg", b"unknown"),
            ("notes.txt", b"user"),
        ] {
            let path = root.join(name);
            fs::create_dir_all(path.parent().unwrap()).unwrap();
            fs::write(path, bytes).unwrap();
        }
        (temp, root, environment)
    }
    #[test]
    fn private_uninstall_removes_registered_app_and_preserves_all_personal_data() {
        let (_temp, root, environment) = fixture();
        let outcome = remove_with_environment(&root, Some(&environment), None).unwrap();
        assert!(outcome.personal_data_preserved);
        assert_eq!(outcome.removed_files, 5);
        assert!(!root.join(EXE).exists());
        assert!(!root.join(integration::HELPER).exists());
        assert!(!environment.program_link().exists());
        assert!(!environment.desktop_link().exists());
        for name in [
            "preferences.json",
            "video-settings.json",
            "trophies-v1.dat",
            "collection/archives/sentinel.tar",
            "database/receipt.json",
            "logs/session.log",
            "assets/personal-photo.jpg",
            "notes.txt",
        ] {
            assert!(root.join(name).is_file(), "Lost {name}");
        }
        assert_eq!(
            fs::read(root.join("preferences.json")).unwrap(),
            b"personal language not chosen"
        );
        let receipt: serde_json::Value =
            serde_json::from_slice(&fs::read(root.join(integration::RECEIPT)).unwrap()).unwrap();
        assert_eq!(receipt["uninstalled"], true);
        environment.cleanup_fixture();
    }
    #[test]
    fn failed_uninstall_restores_inventory_app_shortcuts_and_receipt() {
        let (_temp, root, environment) = fixture();
        let original = fs::read(root.join(integration::RECEIPT)).unwrap();
        assert!(remove_with_environment(&root, Some(&environment), Some(2)).is_err());
        assert!(root.join(EXE).exists());
        assert!(root.join(INVENTORY).exists());
        assert!(root.join(integration::HELPER).exists());
        assert_eq!(fs::read(root.join(integration::RECEIPT)).unwrap(), original);
        assert!(environment.program_link().is_file());
        remove_with_environment(&root, Some(&environment), None).unwrap();
        environment.cleanup_fixture();
    }
    #[test]
    fn modified_files_retained_and_linked_files_rejected_before_any_removal() {
        let (_temp, root, environment) = fixture();
        fs::write(root.join("assets/owned.txt"), b"user modification").unwrap();
        let outside = root.parent().unwrap().join("outside-license");
        fs::hard_link(root.join("LICENSE"), &outside).unwrap();
        assert!(remove_with_environment(&root, Some(&environment), None).is_err());
        assert!(root.join(EXE).exists());
        assert!(outside.exists());
        fs::remove_file(&outside).unwrap();
        let outcome = remove_with_environment(&root, Some(&environment), None).unwrap();
        assert_eq!(outcome.retained_modified_files, vec!["assets/owned.txt"]);
        assert_eq!(
            fs::read(root.join("assets/owned.txt")).unwrap(),
            b"user modification"
        );
        environment.cleanup_fixture();
    }
    #[test]
    fn registered_direct_uninstall_explicitly_retains_its_running_helper() {
        let (_temp, root, environment) = fixture();
        let helper = fs::read(root.join(integration::HELPER)).unwrap();
        let outcome = remove_files(
            &root,
            Some(&environment),
            None,
            &root.join(integration::HELPER),
        )
        .unwrap();
        assert_eq!(
            outcome.retained_maintenance_helper,
            Some(integration::HELPER.into())
        );
        assert!(!root.join(EXE).exists());
        assert!(!environment.program_link().exists());
        assert!(!environment.desktop_link().exists());
        assert_eq!(fs::read(root.join(integration::HELPER)).unwrap(), helper);
        let receipt: serde_json::Value =
            serde_json::from_slice(&fs::read(root.join(integration::RECEIPT)).unwrap()).unwrap();
        assert_eq!(receipt["retained_maintenance_helper"], integration::HELPER);
        assert_eq!(receipt["uninstalled"], true);
        environment.cleanup_fixture();
    }
}
