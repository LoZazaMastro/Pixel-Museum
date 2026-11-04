use super::*;
use std::io::Cursor;

fn pe(marker: u8) -> Vec<u8> {
    let mut bytes = vec![0u8; 512];
    bytes[..2].copy_from_slice(b"MZ");
    bytes[60..64].copy_from_slice(&64u32.to_le_bytes());
    bytes[64..68].copy_from_slice(b"PE\0\0");
    bytes[68..70].copy_from_slice(&0x8664u16.to_le_bytes());
    bytes[88..90].copy_from_slice(&0x20bu16.to_le_bytes());
    bytes[511] = marker;
    bytes
}
fn inventory(files: &[(String, Vec<u8>)], version: &str) -> Inventory {
    Inventory {
        schema_version: 1,
        application_id: "pixel-museum".into(),
        platform: "windows-x64".into(),
        version: version.into(),
        files: files
            .iter()
            .map(|(path, bytes)| OwnedFile {
                path: path.clone(),
                bytes: bytes.len() as u64,
                sha256: format!("{:x}", Sha256::digest(bytes)),
            })
            .collect(),
    }
}
fn write(path: &Path, bytes: &[u8]) {
    fs::create_dir_all(path.parent().unwrap()).unwrap();
    fs::write(path, bytes).unwrap();
}
fn make_zip(files: &[(String, Vec<u8>)]) -> (Vec<u8>, u64) {
    let inv = serde_json::to_vec(&inventory(files, "0.2.0")).unwrap();
    let expanded = files.iter().map(|(_, b)| b.len() as u64).sum::<u64>() + inv.len() as u64;
    let mut writer = zip::ZipWriter::new(Cursor::new(Vec::new()));
    for (path, bytes) in files
        .iter()
        .cloned()
        .chain(std::iter::once((INVENTORY.into(), inv)))
    {
        writer
            .start_file(
                path,
                zip::write::SimpleFileOptions::default()
                    .compression_method(zip::CompressionMethod::Stored),
            )
            .unwrap();
        writer.write_all(&bytes).unwrap();
    }
    (writer.finish().unwrap().into_inner(), expanded)
}
struct Fixture {
    _temp: tempfile::TempDir,
    root: PathBuf,
    old: BTreeMap<String, OwnedFile>,
    new: Vec<(String, Vec<u8>)>,
    descriptor: Descriptor,
}
impl Fixture {
    fn new() -> Self {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path().join("Pixel Museum");
        fs::create_dir(&root).unwrap();
        let mut files = vec![
            (EXE.into(), pe(1)),
            ("LICENSE".into(), b"GPL fixture".to_vec()),
            ("THIRD_PARTY_NOTICES.md".into(), b"original rights".to_vec()),
            (
                "content/collection-packs.json".into(),
                b"unchanged pack manifest".to_vec(),
            ),
            (
                "content/collection-archive-index.json".into(),
                b"archive index".to_vec(),
            ),
            (
                "assets/images/manifest.json".into(),
                b"unchanged image registry".to_vec(),
            ),
            ("assets/replaced.bin".into(), b"old asset".to_vec()),
            (
                "tools/windows-updater/Pixel-Museum-Updater.exe".into(),
                pe(1),
            ),
            ("obsolete.dll".into(), b"old owned library".to_vec()),
        ];
        for (path, bytes) in &files {
            write(&root.join(path), bytes);
        }
        let old_inventory = inventory(&files, "0.1.0");
        let old = old_inventory.validate().unwrap();
        write(
            &root.join(INVENTORY),
            &serde_json::to_vec(&old_inventory).unwrap(),
        );
        write(
            &root.join("pixel-museum-install.json"),
            br#"{"schema_version":1,"executable":"Pixel Museum.exe","version":"0.1.0"}"#,
        );
        for path in [
            "preferences.json",
            "video-settings.json",
            "trophies.json",
            "trophies/custom.bin",
            "logs/session.log",
            "database/current/catalog.json",
            "collection/ready/archives/pack.tar",
            "assets/user-file.bin",
            "shortcut.lnk",
        ] {
            write(&root.join(path), b"keep user data");
        }
        fs::create_dir_all(root.join("application-updates/payloads")).unwrap();
        files.retain(|(p, _)| p != "obsolete.dll");
        files.iter_mut().find(|(p, _)| p == EXE).unwrap().1 = pe(2);
        files
            .iter_mut()
            .find(|(p, _)| p == "tools/windows-updater/Pixel-Museum-Updater.exe")
            .unwrap()
            .1 = pe(2);
        files
            .iter_mut()
            .find(|(p, _)| p == "assets/replaced.bin")
            .unwrap()
            .1 = b"new asset payload".to_vec();
        files.push(("added.dll".into(), b"new library".to_vec()));
        // Even a fully hash-valid protected ZIP entry must never replace user data.
        files.push((
            "preferences.json".into(),
            b"must never be installed".to_vec(),
        ));
        let descriptor = Descriptor {
            schema_version: 1,
            application_id: "pixel-museum".into(),
            platform: "windows-x64".into(),
            version: "0.2.0".into(),
            application_root: root.clone(),
            archive: PathBuf::new(),
            archive_sha256: String::new(),
            archive_bytes: 0,
            unpacked_bytes: 0,
            parent_pid: u32::MAX,
            parent_creation_time: 1,
            language: "it".into(),
            result_path: root.join("application-updates/result.json"),
            restart: true,
        };
        let mut fixture = Self {
            _temp: temp,
            root,
            old,
            new: files,
            descriptor,
        };
        fixture.repack();
        fixture
    }
    fn repack(&mut self) {
        let (bytes, expanded) = make_zip(&self.new);
        self.replace_archive(bytes, expanded);
    }
    fn replace_archive(&mut self, bytes: Vec<u8>, expanded: u64) {
        let sha = format!("{:x}", Sha256::digest(&bytes));
        let path = self
            .root
            .join("application-updates/payloads")
            .join(format!("{sha}.zip"));
        write(&path, &bytes);
        self.descriptor.archive = path;
        self.descriptor.archive_sha256 = sha;
        self.descriptor.archive_bytes = bytes.len() as u64;
        self.descriptor.unpacked_bytes = expanded;
    }
    fn unchanged(&self) {
        assert_eq!(fs::read(self.root.join(EXE)).unwrap(), pe(1));
        assert_eq!(
            fs::read(self.root.join("assets/replaced.bin")).unwrap(),
            b"old asset"
        );
        assert!(self.root.join("obsolete.dll").exists());
        assert!(!self.root.join("added.dll").exists());
        self.preserved();
    }
    fn preserved(&self) {
        for path in [
            "preferences.json",
            "video-settings.json",
            "trophies.json",
            "trophies/custom.bin",
            "logs/session.log",
            "database/current/catalog.json",
            "collection/ready/archives/pack.tar",
            "assets/user-file.bin",
            "shortcut.lnk",
        ] {
            assert_eq!(
                fs::read(self.root.join(path)).unwrap(),
                b"keep user data",
                "{path}"
            );
        }
    }
}

#[test]
fn applies_inventory_and_preserves_every_mutable_tree_without_admin() {
    let f = Fixture::new();
    f.descriptor.validate().unwrap();
    trusted_root(&f.descriptor).unwrap();
    let staged = prepare(&f.descriptor).unwrap();
    f.unchanged();
    let mut transaction = transaction::Transaction::new(&f.descriptor, &f.old, staged).unwrap();
    let (updated, removed) = transaction.apply(None).unwrap();
    assert!(updated >= 4);
    assert_eq!(removed, 1);
    assert_eq!(fs::read(f.root.join(EXE)).unwrap(), pe(2));
    assert_eq!(
        fs::read(f.root.join("assets/replaced.bin")).unwrap(),
        b"new asset payload"
    );
    assert!(!f.root.join("obsolete.dll").exists());
    assert!(f.root.join("added.dll").exists());
    f.preserved();
    let result = outcome(&f.descriptor, true, false, String::new(), updated, removed);
    atomic_json(&f.descriptor.result_path, &result).unwrap();
    let json: serde_json::Value =
        serde_json::from_slice(&fs::read(&f.descriptor.result_path).unwrap()).unwrap();
    assert_eq!(json["success"], true);
    assert_eq!(json["message"], "Pixel Museum è stato aggiornato.");
    transaction.finish().unwrap();
    let new: Inventory =
        serde_json::from_slice(&fs::read(f.root.join(INVENTORY)).unwrap()).unwrap();
    assert_eq!(new.version, "0.2.0");
}

#[test]
fn rollback_restores_original_files_after_each_backup_and_install_mutation() {
    for step in 1..=10 {
        let f = Fixture::new();
        let original_inventory = fs::read(f.root.join(INVENTORY)).unwrap();
        let staged = prepare(&f.descriptor).unwrap();
        let mut t = transaction::Transaction::new(&f.descriptor, &f.old, staged).unwrap();
        assert!(
            t.apply(Some(step)).is_err(),
            "failure point {step} was not reached"
        );
        t.rollback().unwrap();
        f.unchanged();
        assert_eq!(
            fs::read(f.root.join(INVENTORY)).unwrap(),
            original_inventory
        );
    }
}

#[test]
fn incomplete_rollback_retains_journal_and_recovery_files() {
    let f = Fixture::new();
    let staged = prepare(&f.descriptor).unwrap();
    let mut transaction = transaction::Transaction::new(&f.descriptor, &f.old, staged).unwrap();
    assert!(transaction.apply(Some(1)).is_err());
    let directory = transaction.path().to_path_buf();
    // Simulate damaged storage after the executable backup was made.
    fs::write(directory.join("backup/Pixel Museum.exe"), b"damaged backup").unwrap();
    assert!(transaction.rollback().is_err());
    drop(transaction);
    assert!(directory.join("journal.json").is_file());
    assert!(directory.join("backup/Pixel Museum.exe").is_file());
    f.preserved();
}

#[test]
fn rejects_bad_sha_traversal_aliases_inventory_and_expansion_before_swaps() {
    let mut f = Fixture::new();
    let mut corrupt = fs::read(&f.descriptor.archive).unwrap();
    corrupt[0] ^= 1;
    fs::write(&f.descriptor.archive, corrupt).unwrap();
    assert!(prepare(&f.descriptor).is_err());
    f.unchanged();
    for extras in [
        vec![("../escape".into(), b"bad".to_vec())],
        vec![
            ("assets/A.bin".into(), vec![1]),
            ("assets/a.bin".into(), vec![2]),
        ],
        vec![("C:/escape".into(), vec![1])],
        vec![("assets/CON.txt".into(), vec![1])],
    ] {
        let mut f = Fixture::new();
        f.new.extend(extras);
        f.repack();
        assert!(prepare(&f.descriptor).is_err());
        f.unchanged();
    }
    f = Fixture::new();
    f.descriptor.unpacked_bytes -= 1;
    assert!(prepare(&f.descriptor).is_err());
    f.unchanged();
    f = Fixture::new();
    let (mut bytes, expanded) = make_zip(&f.new);
    let pos = bytes
        .windows(b"new asset payload".len())
        .position(|b| b == b"new asset payload")
        .unwrap();
    bytes[pos] ^= 1;
    f.replace_archive(bytes, expanded);
    assert!(prepare(&f.descriptor).is_err());
    f.unchanged();
}

#[test]
fn rejects_resource_migrations_unowned_collisions_and_modified_obsolete_files() {
    let mut f = Fixture::new();
    f.new
        .iter_mut()
        .find(|(p, _)| p == "content/collection-packs.json")
        .unwrap()
        .1 = b"changed resources".to_vec();
    f.repack();
    assert!(prepare(&f.descriptor).is_err());
    f.unchanged();
    let f = Fixture::new();
    write(&f.root.join("added.dll"), b"user file collision");
    let p = prepare(&f.descriptor).unwrap();
    assert!(transaction::Transaction::new(&f.descriptor, &f.old, p).is_err());
    assert_eq!(
        fs::read(f.root.join("added.dll")).unwrap(),
        b"user file collision"
    );
    let f = Fixture::new();
    write(&f.root.join("obsolete.dll"), b"user modified owned file");
    let p = prepare(&f.descriptor).unwrap();
    assert!(transaction::Transaction::new(&f.descriptor, &f.old, p).is_err());
    assert_eq!(
        fs::read(f.root.join("obsolete.dll")).unwrap(),
        b"user modified owned file"
    );
}

#[test]
fn rejects_linked_destinations_and_non_app_descriptors() {
    let mut f = Fixture::new();
    for version in ["1.0", "01.0.0", "1.0.0-01", "1.0.0+", "v1.2.3", "1.2.3.4"] {
        f.descriptor.version = version.into();
        assert!(f.descriptor.validate().is_err());
    }
    for version in ["0.0.0", "1.2.3-alpha.1+001", "999.0.0-preview-r3"] {
        assert!(strict_semver(version));
    }
    f.descriptor.version = "0.2.0".into();
    f.descriptor.result_path = f.root.parent().unwrap().join("outside.json");
    assert!(f.descriptor.validate().is_err());
    let f = Fixture::new();
    fs::remove_file(f.root.join("assets/replaced.bin")).unwrap();
    let outside = f.root.parent().unwrap().join("outside.bin");
    write(&outside, b"outside user data");
    fs::hard_link(&outside, f.root.join("assets/replaced.bin")).unwrap();
    let p = prepare(&f.descriptor).unwrap();
    assert!(transaction::Transaction::new(&f.descriptor, &f.old, p).is_err());
    assert_eq!(fs::read(outside).unwrap(), b"outside user data");
}

#[test]
fn failed_helper_attempt_replaces_stale_success_atomically_but_never_writes_unsafe_result() {
    let mut f = Fixture::new();
    atomic_json(
        &f.descriptor.result_path,
        &outcome(&f.descriptor, true, false, String::new(), 1, 0),
    )
    .unwrap();
    let descriptor_path = f.root.join("application-updates/request.json");
    write(
        &descriptor_path,
        &serde_json::to_vec(&f.descriptor).unwrap(),
    );
    // This unit-test process is intentionally not a temporary updater runner.
    assert!(run_descriptor(&descriptor_path).is_err());
    let result: serde_json::Value =
        serde_json::from_slice(&fs::read(&f.descriptor.result_path).unwrap()).unwrap();
    assert_eq!(result["success"], false);
    assert_eq!(result["rolled_back"], false);
    assert!(
        result["message"]
            .as_str()
            .unwrap()
            .starts_with("Impossibile")
    );
    f.unchanged();
    let outside = f.root.parent().unwrap().join("untrusted-result.json");
    f.descriptor.result_path = outside.clone();
    write(
        &descriptor_path,
        &serde_json::to_vec(&f.descriptor).unwrap(),
    );
    assert!(run_descriptor(&descriptor_path).is_err());
    assert!(!outside.exists());
}

#[cfg(windows)]
#[test]
fn real_windows_file_lock_rolls_back_prior_moves() {
    use std::os::windows::fs::OpenOptionsExt;
    let f = Fixture::new();
    let locked = OpenOptions::new()
        .read(true)
        .share_mode(1)
        .open(f.root.join("assets/replaced.bin"))
        .unwrap();
    let p = prepare(&f.descriptor).unwrap();
    let mut t = transaction::Transaction::new(&f.descriptor, &f.old, p).unwrap();
    assert!(t.apply(None).is_err());
    drop(locked);
    t.rollback().unwrap();
    f.unchanged();
}

#[cfg(windows)]
#[test]
fn junction_destination_cannot_redirect_update_outside_root() {
    use std::os::windows::process::CommandExt;
    let f = Fixture::new();
    let outside = f.root.parent().unwrap().join("junction-target");
    fs::create_dir(&outside).unwrap();
    write(&outside.join("marker.bin"), b"outside stays");
    let link = f.root.join("assets/redirect");
    let status = std::process::Command::new("cmd.exe")
        .args(["/c", "mklink", "/J"])
        .arg(&link)
        .arg(&outside)
        .creation_flags(0x0800_0000)
        .output()
        .unwrap();
    assert!(
        status.status.success(),
        "{}",
        String::from_utf8_lossy(&status.stderr)
    );
    let mut f = f;
    f.new.push((
        "assets/redirect/marker.bin".into(),
        b"untrusted replacement".to_vec(),
    ));
    f.repack();
    let p = prepare(&f.descriptor).unwrap();
    assert!(transaction::Transaction::new(&f.descriptor, &f.old, p).is_err());
    assert_eq!(
        fs::read(outside.join("marker.bin")).unwrap(),
        b"outside stays"
    );
}

#[test]
fn setup_compares_prereleases_and_rejects_downgrades() {
    for (old, new) in [
        ("0.2.0-preview", "0.2.0-preview.9"),
        ("0.2.0-preview.9", "0.2.0-preview.10"),
        ("0.2.0-preview.10", "0.2.0"),
        ("0.2.9", "0.2.10"),
    ] {
        assert!(version_is_newer(old, new));
        assert!(!version_is_newer(new, old));
    }
    assert!(!version_is_newer("0.2.0+one", "0.2.0+two"));
    assert!(!version_is_newer("0.2.0", "unrecognized"));
}

#[test]
fn setup_upgrade_reuses_transaction_and_preserves_existing_progress() {
    let mut f = Fixture::new();
    f.new
        .iter_mut()
        .find(|(p, _)| p == crate::integration::HELPER)
        .unwrap()
        .1
        .extend_from_slice(crate::integration::HELPER_CAPABILITY);
    f.repack();
    let base = f._temp.path();
    let environment = crate::integration::Environment {
        programs: base.join("Programs"),
        desktop: base.join("Desktop"),
        registry_base: format!(
            r"Software\PixelMuseum\InstallerTests\{}",
            base.file_name().unwrap().to_string_lossy()
        ),
    };
    fs::create_dir_all(&environment.desktop).unwrap();
    let registration = crate::integration::registration(&f.root, "it", true).unwrap();
    let receipt_path = f.root.join(crate::integration::RECEIPT);
    let mut receipt: serde_json::Value =
        serde_json::from_slice(&fs::read(&receipt_path).unwrap()).unwrap();
    receipt["windows_integration"] = serde_json::to_value(&registration).unwrap();
    let saved_receipt = serde_json::to_vec(&receipt).unwrap();
    write(&receipt_path, &saved_receipt);
    crate::integration::register(&f.root, "0.1.0", 8192, &registration, &environment).unwrap();
    let d = &f.descriptor;
    let package = crate::manifest::Package {
        id: "app".into(),
        kind: crate::manifest::PackageKind::App,
        format: crate::manifest::PackageFormat::Zip,
        filename: "app.zip".into(),
        url: None,
        sha256: d.archive_sha256.clone(),
        bytes: d.archive_bytes,
        unpacked_bytes: d.unpacked_bytes,
        target: ".".into(),
    };
    for phase in [Phase::Check, Phase::Verify, Phase::Extract, Phase::Prepare] {
        let control = InstallControl::default();
        let result = apply_from_setup(
            &f.root,
            &d.version,
            &package,
            &d.archive,
            "fr",
            &environment,
            &control,
            None,
            |current, _, _| {
                assert_ne!(current, Phase::Finish);
                if current == phase {
                    control.request_cancel();
                }
            },
        );
        assert!(
            format!("{:#}", result.unwrap_err()).contains("Installation cancelled"),
            "{phase:?}"
        );
        assert_eq!(fs::read(f.root.join(EXE)).unwrap(), pe(1));
        assert_eq!(fs::read(&receipt_path).unwrap(), saved_receipt);
        let staging = f.root.join("application-updates/transactions");
        assert!(!staging.exists() || fs::read_dir(staging).unwrap().next().is_none());
    }

    let control = InstallControl::default();
    let mut progress = Vec::new();
    apply_from_setup(
        &f.root,
        &d.version,
        &package,
        &d.archive,
        "fr",
        &environment,
        &control,
        None,
        |phase, done, total| {
            progress.push((phase, done, total));
            if phase == Phase::Finish {
                assert!(control.is_committing());
                control.request_cancel();
                assert!(check_cancel(control.cancel_token()).is_ok());
            }
        },
    )
    .unwrap();
    for (phase, size) in [
        (Phase::Verify, package.bytes),
        (Phase::Extract, package.unpacked_bytes),
    ] {
        assert!(progress.contains(&(phase, 0, size)));
        assert!(progress.contains(&(phase, size, size)));
    }
    assert!(
        progress.iter().any(|(phase, done, total)| {
            *phase == Phase::Prepare && *total > 0 && done == total
        })
    );
    assert_eq!(fs::read(f.root.join(EXE)).unwrap(), pe(2));
    for path in [
        "preferences.json",
        "video-settings.json",
        "trophies/custom.bin",
        "database/current/catalog.json",
        "collection/ready/archives/pack.tar",
    ] {
        assert_eq!(
            fs::read(f.root.join(path)).unwrap(),
            b"keep user data",
            "{path}"
        );
    }
    assert_eq!(fs::read(&receipt_path).unwrap(), saved_receipt);
    assert!(environment.desktop_link().is_file());
    crate::integration::verify_registered(&f.root, &d.version, &registration, &environment)
        .unwrap();
    assert!(
        apply_from_setup(
            &f.root,
            &d.version,
            &package,
            &d.archive,
            "fr",
            &environment,
            &InstallControl::default(),
            None,
            |phase, _, _| assert_ne!(phase, Phase::Finish, "same version attempted to commit")
        )
        .is_err()
    );
    crate::integration::unregister(&f.root, &registration, &environment).unwrap();
}

#[test]
#[ignore = "requires a local release ZIP and a disposable, unregistered installation clone"]
fn setup_upgrade_real_release_in_sandbox() -> Result<()> {
    let root = PathBuf::from(
        std::env::var_os("PIXEL_MUSEUM_TEST_UPGRADE_ROOT").context("Missing clone path")?,
    );
    let local = PathBuf::from(std::env::var_os("LOCALAPPDATA").context("Missing LOCALAPPDATA")?);
    let sandbox = local.join("PixelMuseumBuild");
    ensure!(
        root.starts_with(&sandbox) && root != sandbox,
        "Clone must be inside PixelMuseumBuild"
    );
    ensure_no_links(&root)?;
    ensure!(
        crate::uninstall::inspect(&root)?.registration.is_none(),
        "Use an unregistered clone"
    );
    let manifest_path = PathBuf::from(
        std::env::var_os("PIXEL_MUSEUM_TEST_UPGRADE_MANIFEST").context("Missing manifest path")?,
    );
    let manifest: crate::manifest::Manifest = serde_json::from_slice(&fs::read(&manifest_path)?)?;
    manifest.validate()?;
    let full = manifest
        .packages
        .iter()
        .find(|package| package.kind == crate::manifest::PackageKind::App)
        .context("Missing application package")?;
    let inventory_sha = inventory_sha256(&root)?;
    let delta = manifest.updates.iter().find(|update| {
        update.base_inventory_sha256.eq_ignore_ascii_case(&inventory_sha)
    });
    let package = delta.map_or(full, |update| &update.package);
    let archive = manifest_path
        .parent()
        .context("Missing package folder")?
        .join(&package.filename);
    let temp = tempfile::tempdir()?;
    let environment = crate::integration::Environment {
        programs: temp.path().join("Programs"),
        desktop: temp.path().join("Desktop"),
        registry_base: format!(
            r"Software\PixelMuseum\InstallerTests\{}",
            temp.path().file_name().unwrap().to_string_lossy()
        ),
    };
    let before = hash_file(&root.join(EXE))?;
    let start = std::time::Instant::now();
    let control = InstallControl::default();
    let cancel_phase = std::env::var("PIXEL_MUSEUM_TEST_CANCEL_PHASE").ok();
    let outcome = apply_from_setup(
        &root,
        &manifest.version,
        package,
        &archive,
        "it",
        &environment,
        &control,
        delta,
        |phase, done, total| {
            println!(
                "{:.2}s {phase:?} {done}/{total}",
                start.elapsed().as_secs_f64()
            );
            if cancel_phase.as_deref() == Some(&format!("{phase:?}")) {
                control.request_cancel();
            }
        },
    );
    if cancel_phase.is_some() {
        ensure!(
            format!("{:#}", outcome.unwrap_err()).contains("Installation cancelled"),
            "Setup did not cancel safely"
        );
        ensure!(
            hash_file(&root.join(EXE))? == before,
            "Installed executable changed on cancellation"
        );
    } else {
        outcome?;
        let installed = crate::uninstall::inspect(&root)?;
        let registration = installed
            .registration
            .context("Missing test registration")?;
        let result = crate::integration::verify_registered(
            &root,
            &manifest.version,
            &registration,
            &environment,
        );
        crate::integration::unregister(&root, &registration, &environment)?;
        result?;
    }
    Ok(())
}
