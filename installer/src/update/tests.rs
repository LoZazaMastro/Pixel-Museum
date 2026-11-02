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
