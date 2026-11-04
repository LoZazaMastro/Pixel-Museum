// Current editorial snapshot installed before the first application launch.
use crate::{engine::{self, Phase, Progress}, manifest::{Package, PackageFormat, PackageKind, ensure_no_links, safe_relative_path, valid_sha256, validate_release_url}};
use anyhow::{Context, Result, ensure};
use serde::{Deserialize, Serialize};
use std::{collections::HashSet, fs, io::Read, path::Path, sync::{Mutex, atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering}}};

const FEED: &str = "https://lozazamastro.github.io/Pixel-Museum/database-update.json";
const LIMIT: u64 = 4 << 30;

#[derive(Clone, Deserialize, Serialize)]
struct File { path: String, url: String, sha256: String, bytes: u64 }
#[derive(Deserialize, Serialize)]
struct Snapshot {
    schema_version: u32, database_id: String, revision: u64, version: String,
    #[serde(default)] minimum_reader: u32,
    #[serde(default)] notes: serde_json::Value,
    files: Vec<File>,
}

fn allowed(path: &str) -> bool {
    if safe_relative_path(path).is_err() { return false; }
    if ["content/catalog.json", "content/human-history.json", "content/culture-memories.json", "content/credits.json", "content/collection-image-supplements.json"].contains(&path) { return true; }
    for language in ["en", "it", "es", "fr", "de"] {
        for group in ["locales", "ui-locales"] {
            if path == format!("content/{group}/{language}.json") { return true; }
        }
    }
    (path.starts_with("assets/image-supplements/") && [".jpg", ".jpeg", ".png", ".webp"].iter().any(|ext|path.ends_with(ext)))
        || (path.starts_with("assets/culture-audio/") && path.ends_with(".wav"))
}

fn validate(snapshot: &Snapshot) -> Result<()> {
    ensure!(snapshot.schema_version == 1 && snapshot.database_id == "pixel-museum" && snapshot.minimum_reader <= 1 && snapshot.revision > 0, "Unsupported database snapshot");
    ensure!(!snapshot.version.is_empty() && snapshot.version.len() <= 80 && snapshot.files.len() <= 16384, "Invalid database snapshot");
    let mut paths = HashSet::new(); let mut total = 0u64;
    for file in &snapshot.files {
        ensure!(allowed(&file.path) && paths.insert(file.path.to_lowercase()) && valid_sha256(&file.sha256) && file.bytes > 0 && file.bytes <= 64 << 20, "Invalid database file");
        validate_release_url(&file.url)?;
        total = total.checked_add(file.bytes).context("Database size overflow")?;
        ensure!(total <= LIMIT, "Database snapshot is too large");
    }
    Ok(())
}

pub fn install_current(stage: &Path, cancel: &AtomicBool, report: &mut impl FnMut(Progress)) -> Result<()> {
    engine::check_cancel(cancel)?;
    let bundled: serde_json::Value = serde_json::from_slice(&fs::read(stage.join("content/database-version.json"))?)?;
    let revision = bundled["revision"].as_u64().context("Missing bundled database revision")?;
    report(Progress { phase: Phase::Check, package: String::new(), done: 0, total: 0 });
    // This fixed publisher endpoint is deliberately separate from the GitHub
    // asset client. Redirects stay disabled; all payload URLs are validated.
    let client = reqwest::blocking::Client::builder().user_agent("Pixel-Museum-Setup")
        .connect_timeout(std::time::Duration::from_secs(15)).timeout(std::time::Duration::from_secs(20))
        .redirect(reqwest::redirect::Policy::none()).build()?;
    let mut response = client.get(FEED).header("Cache-Control", "no-cache").send()?.error_for_status()?;
    let mut bytes = Vec::new(); let mut buffer = [0u8; 32768];
    loop {
        engine::check_cancel(cancel)?;
        let n = response.read(&mut buffer)?; if n == 0 { break; }
        ensure!(bytes.len() + n <= 4 << 20, "Database feed exceeds 4 MiB"); bytes.extend_from_slice(&buffer[..n]);
    }
    install_snapshot(stage, revision, &bytes, cancel, report)
}

fn install_snapshot(stage: &Path, bundled_revision: u64, bytes: &[u8], cancel: &AtomicBool, report: &mut impl FnMut(Progress)) -> Result<()> {
    let snapshot: Snapshot = serde_json::from_slice(bytes).context("Invalid current database feed")?;
    validate(&snapshot)?;
    if snapshot.revision <= bundled_revision { return Ok(()); }
    ensure!(!snapshot.files.is_empty(), "The current database has no content files");
    let database = stage.join("database"); let blobs = database.join("blobs");
    ensure_no_links(&blobs)?; fs::create_dir_all(&blobs)?;
    let mut hashes = HashSet::new();
    let files: Vec<_> = snapshot.files.iter().filter(|file| {
        if hashes.contains(&file.sha256) { return false; }
        let package = Package { id:"database".into(), kind:PackageKind::App, filename:String::new(), format:PackageFormat::Zip, url:None, sha256:file.sha256.clone(), bytes:file.bytes, unpacked_bytes:file.bytes, target:String::new() };
        let bundled=stage.join(&file.path);
        // The native overlay also accepts a hash-verified bundled file. A
        // cumulative snapshot must not redownload resources present in setup.
        if engine::verify_package(&bundled,&package,cancel).is_ok() { return false; }
        hashes.insert(&file.sha256);
        true
    }).collect();
    let total = files.iter().map(|file|file.bytes).sum();
    ensure!(fs2::available_space(stage)? >= total + 64 * 1024 * 1024, "Not enough space for the current database");
    let done = AtomicU64::new(0); let next = AtomicUsize::new(0);
    let (send, receive) = std::sync::mpsc::channel();
    let error = Mutex::new(None::<anyhow::Error>);
    let net = engine::client()?;
    std::thread::scope(|scope| {
        for _ in 0..files.len().min(4) {
            let send = send.clone(); let files = &files; let next = &next;
            let done = &done; let error = &error; let net = &net; let blobs = &blobs;
            scope.spawn(move || {
                loop {
                    if cancel.load(Ordering::Relaxed) || error.lock().unwrap().is_some() { break; }
                    let index = next.fetch_add(1, Ordering::Relaxed); if index >= files.len() { break; }
                    let file = files[index]; let target = blobs.join(&file.sha256);
                    let package = Package { id: "database".into(), kind: PackageKind::App, filename: format!("{}.blob",file.sha256), format: PackageFormat::Zip, url: Some(file.url.clone()), sha256: file.sha256.clone(), bytes: file.bytes, unpacked_bytes: file.bytes, target: "database/blobs".into() };
                    let mut previous = 0;
                    let result = engine::download(&net, &package, &target, cancel, |received| {
                        let increment = received.saturating_sub(previous); previous = received;
                        let current = done.fetch_add(increment, Ordering::Relaxed) + increment;
                        let _ = send.send(Progress { phase: Phase::Download, package: String::new(), done: current.min(total), total });
                    }).and_then(|_|engine::verify_package(&target, &package, cancel).map(|_|()));
                    if let Err(problem) = result { *error.lock().unwrap() = Some(problem); break; }
                }
            });
        }
        drop(send);
        for progress in receive { report(progress); }
    });
    if let Some(problem) = error.into_inner().unwrap() { return Err(problem).context("Cannot finish installing the current database"); }
    engine::check_cancel(cancel)?;
    // Staging is not yet visible to the app. Publishing the pointer last means
    // no cancelled or failed install can expose a partial content snapshot.
    fs::write(database.join("active.json"), serde_json::to_vec_pretty(&snapshot)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn database_paths_cannot_change_executables_or_escape_the_installation() {
        for path in ["../escape.jpg", "content/../../evil.exe", "Pixel Museum.exe", "content/preferences.json", "database/active.json", "assets/image-supplements/evil.exe"] { assert!(!allowed(path), "{path}"); }
        assert!(allowed("content/catalog.json")); assert!(allowed("content/locales/it.json")); assert!(allowed("assets/image-supplements/example.jpg"));
    }
    #[test]
    fn rejects_duplicate_paths_and_untrusted_payloads() {
        let file = File { path:"content/catalog.json".into(), url:"https://github.com/LoZazaMastro/Pixel-Museum/releases/download/database-r7/catalog.json".into(), sha256:"a".repeat(64), bytes:2 };
        let mut snapshot = Snapshot { schema_version:1, database_id:"pixel-museum".into(), revision:7, version:"test".into(), minimum_reader:1, notes:serde_json::json!({}), files:vec![file.clone()] };
        assert!(validate(&snapshot).is_ok()); snapshot.files.push(file); assert!(validate(&snapshot).is_err());
        snapshot.files.pop(); snapshot.files[0].url="https://example.org/catalog.json".into(); assert!(validate(&snapshot).is_err());
    }
    #[test]
    fn already_current_install_does_not_create_an_overlay() {
        let stage = tempfile::tempdir().unwrap(); let cancel = AtomicBool::new(false);
        let feed=br#"{"schema_version":1,"database_id":"pixel-museum","revision":6,"version":"test","files":[]}"#;
        install_snapshot(stage.path(),6,feed,&cancel,&mut |_|{}).unwrap(); assert!(!stage.path().join("database").exists());
    }
    #[test]
    fn current_snapshot_reuses_identical_bundled_files_without_network_downloads() {
        use sha2::{Digest,Sha256};
        let stage=tempfile::tempdir().unwrap(); let cancel=AtomicBool::new(false);
        fs::create_dir_all(stage.path().join("content")).unwrap();
        let bytes=b"{}"; let hash=format!("{:x}",Sha256::digest(bytes));
        for name in ["catalog.json","human-history.json"] { fs::write(stage.path().join("content").join(name),bytes).unwrap(); }
        let files:Vec<_>=["content/catalog.json","content/human-history.json"].iter().map(|path|serde_json::json!({"path":path,"url":"https://github.com/LoZazaMastro/Pixel-Museum/releases/download/database-r7/unreachable.json","sha256":hash,"bytes":2})).collect();
        let feed=serde_json::to_vec(&serde_json::json!({"schema_version":1,"database_id":"pixel-museum","revision":7,"version":"test","files":files})).unwrap();
        let mut download_reported=false;
        install_snapshot(stage.path(),1,&feed,&cancel,&mut |p|{if matches!(p.phase,Phase::Download){download_reported=true;}}).unwrap();
        assert!(!download_reported);
        assert_eq!(fs::read_dir(stage.path().join("database/blobs")).unwrap().count(),0);
        let active:serde_json::Value=serde_json::from_slice(&fs::read(stage.path().join("database/active.json")).unwrap()).unwrap();
        assert_eq!(active["revision"],7); assert_eq!(active["files"].as_array().unwrap().len(),2);
    }
}
