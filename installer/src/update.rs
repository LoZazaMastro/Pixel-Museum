//! Offline, user-scope Windows application update application. No GUI or HTTP code.
pub(crate) mod process;
mod transaction;

use crate::manifest::{ensure_no_links, safe_relative_path};
use anyhow::{Context, Result, bail, ensure};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::{self, OpenOptions},
    io::{Read, Seek, SeekFrom, Write},
    path::{Component, Path, PathBuf},
    time::Duration,
};

const INVENTORY: &str = "application-files.json";
const EXE: &str = "Pixel Museum.exe";
const MAX_ARCHIVE: u64 = 2 * 1024 * 1024 * 1024;
const MAX_EXPANDED: u64 = 4 * 1024 * 1024 * 1024;
const MAX_INVENTORY: u64 = 16 * 1024 * 1024;

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Descriptor {
    pub schema_version: u32,
    pub application_id: String,
    pub platform: String,
    pub version: String,
    pub application_root: PathBuf,
    pub archive: PathBuf,
    pub archive_sha256: String,
    pub archive_bytes: u64,
    pub unpacked_bytes: u64,
    pub parent_pid: u32,
    pub parent_creation_time: u64,
    pub language: String,
    pub result_path: PathBuf,
    pub restart: bool,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Inventory {
    pub schema_version: u32,
    pub application_id: String,
    pub platform: String,
    pub version: String,
    pub files: Vec<OwnedFile>,
}
#[derive(Clone, Debug, Deserialize, Serialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct OwnedFile {
    pub path: String,
    pub bytes: u64,
    pub sha256: String,
}

#[derive(Debug, Serialize)]
pub struct Outcome {
    pub schema_version: u32,
    pub application_id: &'static str,
    pub version: String,
    pub success: bool,
    pub rolled_back: bool,
    pub message: String,
    pub details: String,
    pub updated_files: usize,
    pub removed_files: usize,
}

pub(super) fn path_key(path: &Path) -> String {
    path.to_string_lossy()
        .trim_start_matches(r"\\?\")
        .replace('\\', "/")
        .to_lowercase()
}
fn key(path: &str) -> String {
    path.to_lowercase()
}
fn lower_sha(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
}

fn strict_semver(value: &str) -> bool {
    if value.is_empty() || value.len() > 100 {
        return false;
    }
    let (version, build) = value
        .split_once('+')
        .map_or((value, None), |(a, b)| (a, Some(b)));
    let identifiers = |part: &str, numeric_rule: bool| {
        !part.is_empty()
            && part.split('.').all(|s| {
                !s.is_empty()
                    && s.bytes().all(|c| c.is_ascii_alphanumeric() || c == b'-')
                    && (!numeric_rule
                        || !s.bytes().all(|c| c.is_ascii_digit())
                        || s.len() == 1
                        || !s.starts_with('0'))
            })
    };
    if build.is_some_and(|b| !identifiers(b, false)) {
        return false;
    }
    let (core, pre) = version
        .split_once('-')
        .map_or((version, None), |(a, b)| (a, Some(b)));
    let numbers: Vec<_> = core.split('.').collect();
    numbers.len() == 3
        && numbers.iter().all(|s| {
            !s.is_empty()
                && s.bytes().all(|c| c.is_ascii_digit())
                && (s.len() == 1 || !s.starts_with('0'))
        })
        && pre.is_none_or(|p| identifiers(p, true))
}

pub(crate) fn version_is_newer(current: &str, candidate: &str) -> bool {
    use std::cmp::Ordering;
    if !strict_semver(current) || !strict_semver(candidate) {
        return false;
    }
    fn parts(version: &str) -> (&str, Option<&str>) {
        let version = version.split('+').next().unwrap();
        version
            .split_once('-')
            .map_or((version, None), |(core, pre)| (core, Some(pre)))
    }
    fn numeric(a: &str, b: &str) -> Ordering {
        a.len().cmp(&b.len()).then_with(|| a.cmp(b))
    }
    let (old_core, old_pre) = parts(current);
    let (new_core, new_pre) = parts(candidate);
    for (new, old) in new_core.split('.').zip(old_core.split('.')) {
        let order = numeric(new, old);
        if order != Ordering::Equal {
            return order == Ordering::Greater;
        }
    }
    match (new_pre, old_pre) {
        (None, Some(_)) => true,
        (Some(new), Some(old)) => {
            let mut old = old.split('.');
            for new in new.split('.') {
                let Some(old) = old.next() else { return true };
                let order = match (
                    new.bytes().all(|c| c.is_ascii_digit()),
                    old.bytes().all(|c| c.is_ascii_digit()),
                ) {
                    (true, true) => numeric(new, old),
                    (true, false) => Ordering::Less,
                    (false, true) => Ordering::Greater,
                    (false, false) => new.cmp(old),
                };
                if order != Ordering::Equal {
                    return order == Ordering::Greater;
                }
            }
            false
        }
        _ => false,
    }
}

pub(crate) fn ordinary_absolute(path: &Path) -> Result<()> {
    ensure!(path.is_absolute(), "An absolute ordinary path is required");
    #[cfg(windows)]
    {
        use std::path::Prefix;
        ensure!(
            matches!(path.components().next(),Some(Component::Prefix(p)) if matches!(p.kind(),Prefix::Disk(_))),
            "Device, verbatim and UNC paths are not accepted"
        );
        let text = path
            .to_str()
            .context("Path is not valid Unicode")?
            .replace('\\', "/");
        ensure!(
            text.len() > 3 && text.as_bytes().get(2) == Some(&b'/'),
            "Cannot use a drive root"
        );
        safe_relative_path(&text[3..])?;
    }
    ensure!(
        path.components().all(|c| matches!(
            c,
            Component::Prefix(_) | Component::RootDir | Component::Normal(_)
        )),
        "Path contains traversal components"
    );
    ensure_no_links(path)
}

fn protected(name: &str) -> bool {
    let value = key(name);
    let first = value.split('/').next().unwrap_or("");
    matches!(
        first,
        "collection"
            | "database"
            | "application-updates"
            | "logs"
            | "log"
            | "preferences.json"
            | "video-settings.json"
            | "pixel-museum-install.json"
    ) || first.starts_with("troph")
        || value.ends_with(".lnk")
        || value.ends_with(".log")
}
pub(crate) fn allowed(name: &str) -> bool {
    let value = key(name);
    if protected(name) {
        return false;
    }
    if [
        "pixel museum.exe",
        "license",
        "third_party_notices.md",
        "windows guide.md",
        INVENTORY,
    ]
    .contains(&value.as_str())
    {
        return true;
    }
    if !value.contains('/') && value.ends_with(".dll") {
        return true;
    }
    [
        "assets/",
        "content/",
        "music/",
        "licenses/",
        "models/",
        "tools/windows-media/",
        "tools/windows-updater/",
    ]
    .iter()
    .any(|p| value.starts_with(p))
}

impl Descriptor {
    fn validate(&self) -> Result<()> {
        ensure!(
            self.schema_version == 1
                && self.application_id == "pixel-museum"
                && self.platform == "windows-x64",
            "Unsupported update descriptor"
        );
        ensure!(
            strict_semver(&self.version),
            "Update version is not strict SemVer"
        );
        ensure!(
            lower_sha(&self.archive_sha256)
                && (1..=MAX_ARCHIVE).contains(&self.archive_bytes)
                && (1..=MAX_EXPANDED).contains(&self.unpacked_bytes),
            "Invalid update hash or archive size"
        );
        ensure!(
            ["en", "it", "fr", "de", "es"].contains(&self.language.as_str())
                && self.restart
                && self.parent_pid != 0
                && self.parent_creation_time != 0,
            "Invalid update language, restart or parent fields"
        );
        for path in [&self.application_root, &self.archive, &self.result_path] {
            ordinary_absolute(path)?;
        }
        ensure!(
            path_key(&self.archive)
                == path_key(
                    &self
                        .application_root
                        .join("application-updates/payloads")
                        .join(format!("{}.zip", self.archive_sha256))
                ),
            "Archive must be the pinned payload in this installation"
        );
        ensure!(
            path_key(&self.result_path)
                == path_key(
                    &self
                        .application_root
                        .join("application-updates/result.json")
                ),
            "Unsafe update result path"
        );
        Ok(())
    }
}
impl Inventory {
    pub(crate) fn validate(&self) -> Result<BTreeMap<String, OwnedFile>> {
        ensure!(
            self.schema_version == 1
                && self.application_id == "pixel-museum"
                && self.platform == "windows-x64"
                && strict_semver(&self.version),
            "Unrecognized application inventory"
        );
        ensure!(
            (1..=100_000).contains(&self.files.len()),
            "Invalid inventory entry count"
        );
        let mut files = BTreeMap::new();
        let mut total = 0u64;
        for file in &self.files {
            safe_relative_path(&file.path)?;
            ensure!(
                !file.path.ends_with('/')
                    && key(&file.path) != INVENTORY
                    && (allowed(&file.path) || protected(&file.path)),
                "Inventory path is not application-owned: {}",
                file.path
            );
            ensure!(lower_sha(&file.sha256), "Invalid inventory file hash");
            total = total
                .checked_add(file.bytes)
                .context("Inventory size overflow")?;
            ensure!(
                total <= MAX_EXPANDED && files.insert(key(&file.path), file.clone()).is_none(),
                "Inventory size or case-alias conflict"
            );
        }
        ensure!(
            files.contains_key("pixel museum.exe"),
            "Inventory does not identify Pixel Museum.exe"
        );
        Ok(files)
    }
}

pub(crate) fn read_limited(path: &Path, limit: u64) -> Result<Vec<u8>> {
    let mut file = process::open_regular(path)?;
    ensure!(
        file.metadata()?.len() <= limit,
        "File exceeds its size limit"
    );
    let mut bytes = Vec::new();
    Read::by_ref(&mut file)
        .take(limit + 1)
        .read_to_end(&mut bytes)?;
    ensure!(bytes.len() as u64 <= limit, "File grew beyond size limit");
    Ok(bytes)
}
fn hash_reader(reader: &mut impl Read) -> Result<String> {
    hash_reader_progress(reader, |_| Ok(()))
}

fn hash_reader_progress(
    reader: &mut impl Read,
    mut progress: impl FnMut(u64) -> Result<()>,
) -> Result<String> {
    let mut hash = Sha256::new();
    let mut buffer = vec![0u8; 256 * 1024];
    let mut done = 0;
    progress(done)?;
    loop {
        let n = reader.read(&mut buffer)?;
        if n == 0 {
            break;
        }
        hash.update(&buffer[..n]);
        done += n as u64;
        progress(done)?;
    }
    Ok(format!("{:x}", hash.finalize()))
}
pub(crate) fn hash_file(path: &Path) -> Result<String> {
    hash_reader(&mut process::open_regular(path)?)
}

pub(super) fn atomic_json(path: &Path, value: &impl Serialize) -> Result<()> {
    ensure_no_links(path)?;
    let bytes = serde_json::to_vec_pretty(value)?;
    let mut temporary =
        tempfile::NamedTempFile::new_in(path.parent().context("Missing JSON parent")?)?;
    temporary.write_all(&bytes)?;
    temporary.as_file().sync_all()?;
    temporary
        .persist(path)
        .with_context(|| format!("Cannot atomically write {}", path.display()))?;
    Ok(())
}

fn trusted_root(d: &Descriptor) -> Result<()> {
    ensure!(d.application_root.is_dir(), "Application folder is missing");
    let receipt: serde_json::Value = serde_json::from_slice(&read_limited(
        &d.application_root.join("pixel-museum-install.json"),
        1024 * 1024,
    )?)?;
    ensure!(
        receipt["schema_version"] == 1 && receipt["executable"] == EXE,
        "This is not a recognized Pixel Museum installation"
    );
    process::executable_header(&d.application_root.join(EXE))?;
    ensure_no_links(&d.application_root.join("application-updates"))?;
    ensure!(
        d.application_root.join("application-updates").is_dir(),
        "Application update folder is missing"
    );
    Ok(())
}

struct Prepared {
    directory: tempfile::TempDir,
    inventory: Inventory,
    files: BTreeMap<String, OwnedFile>,
    reused: BTreeSet<String>,
}

use crate::engine::{InstallControl, Phase, check_cancel};
use std::sync::atomic::AtomicBool;

#[derive(Debug)]
pub(crate) struct DeltaBaseUnavailable;

impl std::fmt::Display for DeltaBaseUnavailable {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("Installed files do not match the incremental update base")
    }
}

impl std::error::Error for DeltaBaseUnavailable {}

pub(crate) fn inventory_sha256(root: &Path) -> Result<String> {
    Ok(format!(
        "{:x}",
        Sha256::digest(read_limited(&root.join(INVENTORY), MAX_INVENTORY)?)
    ))
}

struct UpdateWork<'a> {
    cancel: &'a AtomicBool,
    report: &'a mut dyn FnMut(Phase, u64, u64),
    last: Option<(Phase, std::time::Instant)>,
}

impl<'a> UpdateWork<'a> {
    fn new(cancel: &'a AtomicBool, report: &'a mut dyn FnMut(Phase, u64, u64)) -> Self {
        Self {
            cancel,
            report,
            last: None,
        }
    }

    fn check(&self) -> Result<()> {
        check_cancel(self.cancel)
    }

    fn advance(&mut self, phase: Phase, done: u64, total: u64) -> Result<()> {
        self.check()?;
        let now = std::time::Instant::now();
        if done == total
            || self.last.is_none_or(|(previous, instant)| {
                phase != previous || now.duration_since(instant).as_millis() >= 100
            })
        {
            (self.report)(phase, done, total);
            self.last = Some((phase, now));
        }
        Ok(())
    }

    fn hash_file(&self, path: &Path) -> Result<String> {
        hash_reader_progress(&mut process::open_regular(path)?, |_| self.check())
    }
}

pub(crate) fn inspect_for_setup(
    root: &Path,
    cancel: &AtomicBool,
    report: &mut dyn FnMut(Phase, u64, u64),
) -> Result<crate::uninstall::Installation> {
    let mut work = UpdateWork::new(cancel, report);
    work.advance(Phase::Check, 0, 0)?;
    crate::uninstall::inspect_with_hash(root, |path, total| {
        hash_reader_progress(&mut process::open_regular(path)?, |done| {
            work.advance(Phase::Check, done, total)
        })
    })
}

fn prepare(d: &Descriptor) -> Result<Prepared> {
    prepare_archive(
        &d.application_root,
        &d.version,
        &d.archive,
        &d.archive_sha256,
        d.archive_bytes,
        d.unpacked_bytes,
        None,
        &mut UpdateWork::new(&AtomicBool::new(false), &mut |_, _, _| {}),
    )
}

fn prepare_archive(
    root: &Path,
    version: &str,
    archive_path: &Path,
    archive_sha256: &str,
    archive_bytes: u64,
    unpacked_bytes: u64,
    delta_base: Option<&BTreeMap<String, OwnedFile>>,
    work: &mut UpdateWork<'_>,
) -> Result<Prepared> {
    work.check()?;
    ensure!(
        strict_semver(version)
            && lower_sha(archive_sha256)
            && (1..=MAX_ARCHIVE).contains(&archive_bytes)
            && (1..=MAX_EXPANDED).contains(&unpacked_bytes),
        "Invalid application update version, hash or size"
    );
    let mut file = process::open_regular(archive_path)?;
    ensure!(
        file.metadata()?.len() == archive_bytes,
        "Archive length differs from the descriptor"
    );
    ensure!(
        hash_reader_progress(&mut file, |done| work.advance(
            Phase::Verify,
            done,
            archive_bytes
        ))? == archive_sha256,
        "Archive SHA-256 differs from the descriptor"
    );
    file.seek(SeekFrom::Start(0))?;
    let mut archive =
        zip::ZipArchive::new(std::io::BufReader::with_capacity(256 * 1024, file))
            .context("Cannot read update ZIP")?;
    ensure!(
        (1..=100_001).contains(&archive.len()),
        "Too many ZIP members"
    );
    let mut headers = BTreeMap::new();
    let mut all = BTreeSet::new();
    let mut expanded = 0u64;
    for i in 0..archive.len() {
        work.check()?;
        let mut item = archive.by_index(i)?;
        let name = item.name()?.to_string();
        safe_relative_path(&name)?;
        ensure!(
            item.enclosed_name().is_some() && !item.is_symlink(),
            "ZIP path escapes or links are forbidden"
        );
        ensure!(
            all.insert(key(name.trim_end_matches('/'))),
            "ZIP repeats a path or case alias"
        );
        if item.is_dir() {
            ensure!(
                item.size() == 0
                    && item
                        .unix_mode()
                        .is_none_or(|m| matches!(m & 0xf000, 0 | 0x4000)),
                "ZIP contains a special or nonempty directory entry"
            );
            let mut empty = [0u8; 1];
            ensure!(item.read(&mut empty)? == 0, "ZIP directory CRC is invalid");
            continue;
        }
        ensure!(
            item.is_file()
                && item
                    .unix_mode()
                    .is_none_or(|m| matches!(m & 0xf000, 0 | 0x8000)),
            "ZIP contains a special file"
        );
        ensure!(
            allowed(&name) || protected(&name),
            "ZIP contains a non-application path: {name}"
        );
        expanded = expanded
            .checked_add(item.size())
            .context("ZIP expansion overflow")?;
        ensure!(
            expanded <= unpacked_bytes && expanded <= MAX_EXPANDED,
            "ZIP exceeds its trusted expansion limit"
        );
        headers.insert(key(&name), (name, item.size()));
    }
    ensure!(
        expanded == unpacked_bytes,
        "ZIP expanded size does not match descriptor"
    );
    for name in headers.keys() {
        work.check()?;
        let parts: Vec<_> = name.split('/').collect();
        ensure!(
            (1..parts.len()).all(|i| !headers.contains_key(&parts[..i].join("/"))),
            "ZIP file/directory path collision"
        );
    }
    let (_, inventory_size) = headers
        .get(INVENTORY)
        .context("Update ZIP lacks application-files.json")?;
    ensure!(*inventory_size <= MAX_INVENTORY, "Inventory is too large");
    let mut inventory_bytes = Vec::new();
    archive
        .by_name(INVENTORY)?
        .take(MAX_INVENTORY + 1)
        .read_to_end(&mut inventory_bytes)?;
    ensure!(
        inventory_bytes.len() as u64 == *inventory_size
            && inventory_bytes.len() as u64 <= MAX_INVENTORY,
        "Inventory expanded beyond its declared size"
    );
    let inventory: Inventory =
        serde_json::from_slice(&inventory_bytes).context("Invalid new inventory")?;
    let files = inventory.validate()?;
    ensure!(inventory.version == version, "ZIP inventory version does not match");
    ensure!(headers.contains_key("pixel museum.exe"), "ZIP lacks Pixel Museum.exe");
    for required in [
        "pixel museum.exe",
        "license",
        "third_party_notices.md",
        "content/collection-packs.json",
        "content/collection-archive-index.json",
        "assets/images/manifest.json",
        "tools/windows-updater/pixel-museum-updater.exe",
    ] {
        ensure!(
            files.contains_key(required),
            "Update inventory lacks required application file: {required}"
        );
    }
    for (k, (name, bytes)) in &headers {
        work.check()?;
        if k == INVENTORY {
            continue;
        }
        let entry = files.get(k).context("ZIP entry is absent from inventory")?;
        ensure!(
            name == &entry.path && *bytes == entry.bytes,
            "ZIP entry does not match inventory"
        );
    }
    let mut reused = BTreeSet::new();
    let missing = files.iter().filter(|(k, _)| !headers.contains_key(*k));
    let mut checked = 0;
    let reusable_bytes: u64 = missing.clone().map(|(_, entry)| entry.bytes).sum();
    if reusable_bytes > 0 {
        work.advance(Phase::Check, 0, reusable_bytes)?;
    }
    for (k, entry) in missing {
        work.check()?;
        let base = delta_base.context("Inventory entry is absent from ZIP")?;
        ensure!(base.get(k) == Some(entry), "ZIP omits a changed inventory entry");
        let path = root.join(safe_relative_path(&entry.path)?);
        let mut existing = process::open_regular(&path).map_err(|_| DeltaBaseUnavailable)?;
        if existing.metadata()?.len() != entry.bytes {
            return Err(DeltaBaseUnavailable.into());
        }
        let digest = hash_reader_progress(&mut existing, |done| {
            work.advance(Phase::Check, checked + done, reusable_bytes)
        })?;
        if digest != entry.sha256 {
            return Err(DeltaBaseUnavailable.into());
        }
        checked += entry.bytes;
        reused.insert(k.clone());
    }
    ensure!(
        fs2::available_space(root)? >= unpacked_bytes + 64 * 1024 * 1024,
        "Insufficient free space to stage the application update"
    );
    let transactions = root.join("application-updates/transactions");
    ensure_no_links(&transactions)?;
    fs::create_dir_all(&transactions)?;
    ensure_no_links(&transactions)?;
    let directory = tempfile::Builder::new()
        .prefix("update-")
        .tempdir_in(&transactions)?;
    let stage = directory.path().join("new");
    fs::create_dir(&stage)?;
    let mut extracted = 0;
    work.advance(Phase::Extract, extracted, unpacked_bytes)?;
    let mut buffer = vec![0u8; 256 * 1024];
    for i in 0..archive.len() {
        work.check()?;
        let mut item = archive.by_index(i)?;
        if item.is_dir() {
            continue;
        }
        let name = item.name()?.to_string();
        let expected = files.get(&key(&name));
        let mut output = if protected(&name) {
            None
        } else {
            let target = stage.join(safe_relative_path(&name)?);
            ensure_no_links(&target)?;
            fs::create_dir_all(target.parent().unwrap())?;
            Some(
                OpenOptions::new()
                    .write(true)
                    .create_new(true)
                    .open(&target)?,
            )
        };
        let mut hash = Sha256::new();
        let mut copied = 0u64;
        loop {
            work.check()?;
            let n = item
                .read(&mut buffer)
                .context("ZIP CRC or decompression failure")?;
            if n == 0 {
                break;
            }
            copied = copied.checked_add(n as u64).context("ZIP size overflow")?;
            ensure!(
                copied <= item.size(),
                "ZIP member exceeds its declared length"
            );
            hash.update(&buffer[..n]);
            if let Some(output) = &mut output {
                output.write_all(&buffer[..n])?;
            }
            extracted += n as u64;
            work.advance(Phase::Extract, extracted, unpacked_bytes)?;
        }
        ensure!(copied == item.size(), "ZIP member ended early");
        if let Some(expected) = expected {
            ensure!(
                format!("{:x}", hash.finalize()) == expected.sha256,
                "ZIP file SHA-256 mismatch: {name}"
            );
        }
        if let Some(output) = output {
            output.sync_all()?;
        }
    }
    process::executable_header(&stage.join(EXE))?;
    let helper = "tools/windows-updater/Pixel-Museum-Updater.exe";
    let helper_root = if reused.contains(&key(helper)) { root } else { &stage };
    process::executable_header(&helper_root.join(helper))?;
    for name in [
        "content/collection-packs.json",
        "assets/images/manifest.json",
    ] {
        ensure!(
            reused.contains(name) || work.hash_file(&root.join(name))? == files[name].sha256,
            "Update changes installed collection resources: {name}"
        );
    }
    Ok(Prepared {
        directory,
        inventory,
        files,
        reused,
    })
}

pub(crate) fn apply_from_setup(
    root: &Path,
    version: &str,
    package: &crate::manifest::Package,
    archive: &Path,
    language: &str,
    environment: &crate::integration::Environment,
    control: &InstallControl,
    delta: Option<&crate::manifest::UpdatePackage>,
    mut report: impl FnMut(Phase, u64, u64),
) -> Result<()> {
    let cancel = control.cancel_token();
    check_cancel(cancel)?;
    ordinary_absolute(root)?;
    let cache = root.join("application-updates");
    ensure_no_links(&cache)?;
    fs::create_dir_all(&cache)?;
    let lock_path = cache.join("apply.lock");
    ensure_no_links(&lock_path)?;
    if lock_path.exists() {
        let _ = process::open_regular(&lock_path)?;
    }
    let lock = OpenOptions::new()
        .create(true)
        .truncate(false)
        .read(true)
        .write(true)
        .open(lock_path)?;
    fs2::FileExt::try_lock_exclusive(&lock)
        .context("Another application update or uninstall is active")?;
    let installed = inspect_for_setup(root, cancel, &mut report)?;
    ensure!(
        version_is_newer(&installed.inventory.version, version),
        "Setup can only upgrade to a newer version"
    );
    process::assert_not_running(&root.join(EXE))?;
    let old_files = installed.inventory.validate()?;
    if let Some(delta) = delta {
        if installed.inventory.version != delta.from_version
            || !inventory_sha256(root)?.eq_ignore_ascii_case(&delta.base_inventory_sha256)
        {
            return Err(DeltaBaseUnavailable.into());
        }
    }
    let archive_sha256 = package.sha256.to_ascii_lowercase();
    let mut work = UpdateWork::new(cancel, &mut report);
    let prepared = prepare_archive(
        root,
        version,
        archive,
        &archive_sha256,
        package.bytes,
        package.unpacked_bytes,
        delta.map(|_| &old_files),
        &mut work,
    )?;
    let stage = prepared.directory.path().join("new");
    let app_bytes = prepared.files.values().map(|file| file.bytes).sum::<u64>()
        + fs::metadata(stage.join(INVENTORY))?.len();
    let helper_root = if prepared.reused.contains(&key(crate::integration::HELPER)) {
        root
    } else {
        &stage
    };
    crate::integration::validate_helper_at(&stage, &helper_root.join(crate::integration::HELPER))?;
    let previous_receipt = installed.receipt;
    let registration = installed.registration;
    let needs_registration = registration.is_none();
    let registration = match registration {
        Some(registration) => registration,
        None => crate::integration::registration(root, language, false)?,
    };
    let mut transaction = transaction::Transaction::for_installation(
        root,
        version,
        &archive_sha256,
        &old_files,
        prepared,
        &mut work,
    )?;
    process::assert_not_running(&root.join(EXE))?;
    control.begin_commit()?;
    report(Phase::Finish, 0, 0);
    let receipt_path = root.join(crate::integration::RECEIPT);
    let mut receipt_changed = false;
    let result = (|| -> Result<()> {
        transaction.apply(None)?;
        if needs_registration {
            let mut receipt = previous_receipt.clone();
            receipt["windows_integration"] = serde_json::to_value(&registration)?;
            atomic_json(&receipt_path, &receipt)?;
            receipt_changed = true;
        }
        // Use registration's own rollback for shortcuts and registry on failure.
        let installed_bytes = previous_receipt["packages"]
            .as_array()
            .into_iter()
            .flatten()
            .filter(|p| p["kind"] == "collection")
            .filter_map(|p| p["unpacked_bytes"].as_u64())
            .fold(app_bytes, u64::saturating_add);
        crate::integration::register(root, version, installed_bytes, &registration, environment)
    })();
    if let Err(error) = result {
        let binary_rollback = transaction.rollback();
        let receipt_rollback = if receipt_changed {
            atomic_json(&receipt_path, &previous_receipt)
        } else {
            Ok(())
        };
        binary_rollback.with_context(|| format!("{error:#}. Application rollback failed"))?;
        receipt_rollback
            .with_context(|| format!("{error:#}. Installation record rollback failed"))?;
        return Err(
            error.context("Pixel Museum upgrade did not complete; previous installation restored")
        );
    }
    if let Err(error) = transaction.finish() {
        eprintln!("Pixel Museum was upgraded, but its backup could not be retired: {error:#}");
    }
    Ok(())
}

fn localized(language: &str, success: bool, rolled_back: bool) -> String {
    let index = ["en", "it", "fr", "de", "es"]
        .iter()
        .position(|l| *l == language)
        .unwrap_or(0);
    if success {
        return [
            "Pixel Museum has been updated.",
            "Pixel Museum è stato aggiornato.",
            "Pixel Museum a été mis à jour.",
            "Pixel Museum wurde aktualisiert.",
            "Pixel Museum se ha actualizado.",
        ][index]
            .into();
    }
    let base = [
        "The update could not be applied. Close Pixel Museum and retry. Check free space and write access to the application folder.",
        "Impossibile applicare l'aggiornamento. Chiudi Pixel Museum e riprova. Controlla lo spazio libero e i permessi di scrittura della cartella dell'app.",
        "La mise à jour a échoué. Fermez Pixel Museum et réessayez. Vérifiez l'espace libre et les droits d'écriture du dossier de l'application.",
        "Das Update konnte nicht angewendet werden. Schließe Pixel Museum und versuche es erneut. Prüfe freien Speicherplatz und Schreibrechte im App-Ordner.",
        "No se pudo aplicar la actualización. Cierra Pixel Museum e inténtalo de nuevo. Comprueba el espacio libre y los permisos de escritura de la carpeta.",
    ][index];
    let restored = [
        "The previous version was restored.",
        "La versione precedente è stata ripristinata.",
        "La version précédente a été restaurée.",
        "Die vorherige Version wurde wiederhergestellt.",
        "Se ha restaurado la versión anterior.",
    ][index];
    if rolled_back {
        format!("{restored} {base}")
    } else {
        base.into()
    }
}

fn outcome(
    d: &Descriptor,
    success: bool,
    rolled_back: bool,
    details: String,
    updated: usize,
    removed: usize,
) -> Outcome {
    Outcome {
        schema_version: 1,
        application_id: "pixel-museum",
        version: d.version.clone(),
        success,
        rolled_back,
        message: localized(&d.language, success, rolled_back),
        details,
        updated_files: updated,
        removed_files: removed,
    }
}
fn launch(root: &Path) -> Result<()> {
    process::executable_header(&root.join(EXE))?;
    let mut child = std::process::Command::new(root.join(EXE))
        .current_dir(root)
        .spawn()
        .context("Cannot restart Pixel Museum")?;
    let deadline = std::time::Instant::now() + Duration::from_secs(2);
    loop {
        if let Some(status) = child.try_wait()? {
            ensure!(
                status.success(),
                "Pixel Museum exited during startup: {status}"
            );
            break;
        }
        if std::time::Instant::now() >= deadline {
            break;
        }
        std::thread::sleep(Duration::from_millis(40));
    }
    Ok(())
}

pub fn run_descriptor(path: &Path) -> Result<()> {
    ordinary_absolute(path)?;
    let d: Descriptor = serde_json::from_slice(&read_limited(path, 64 * 1024)?)
        .context("Invalid update descriptor JSON")?;
    d.validate()?;
    trusted_root(&d)?;
    let mut failure_receipt_written = false;
    let result = run_installed(&d, &mut failure_receipt_written);
    if let Err(error) = result {
        // Unsafe descriptors never get to this point: this is a verified install/result path.
        let receipt = outcome(&d, false, false, format!("{error:#}"), 0, 0);
        if !failure_receipt_written {
            let _ = atomic_json(&d.result_path, &receipt);
        }
        return Err(error);
    }
    Ok(())
}

fn run_installed(d: &Descriptor, failure_receipt_written: &mut bool) -> Result<()> {
    let cache = d.application_root.join("application-updates");
    let lock_path = cache.join("apply.lock");
    ensure_no_links(&lock_path)?;
    let lock = OpenOptions::new()
        .create(true)
        .truncate(false)
        .read(true)
        .write(true)
        .open(lock_path)?;
    fs2::FileExt::try_lock_exclusive(&lock).context("Another application update is active")?;
    let runner = std::env::current_exe()?;
    ensure!(
        path_key(runner.parent().context("Missing updater runner parent")?)
            == path_key(&cache.join("runner")),
        "Updater must run from a temporary copy under application-updates/runner"
    );
    ensure_no_links(&runner)?;
    let old_inventory: Inventory = serde_json::from_slice(&read_limited(
        &d.application_root.join(INVENTORY),
        MAX_INVENTORY,
    )?)?;
    let old_files = old_inventory.validate()?;
    let old_exe = old_files.get("pixel museum.exe").unwrap();
    ensure!(
        fs::metadata(d.application_root.join(EXE))?.len() == old_exe.bytes
            && hash_file(&d.application_root.join(EXE))? == old_exe.sha256,
        "Installed executable does not match its application inventory"
    );
    let parent = process::Parent::open(
        d.parent_pid,
        d.parent_creation_time,
        &d.application_root.join(EXE),
    )?;
    let prepared = match prepare(d) {
        Ok(p) => p,
        Err(error) => {
            let receipt = outcome(d, false, false, format!("{error:#}"), 0, 0);
            atomic_json(&d.result_path, &receipt)?;
            *failure_receipt_written = true;
            if parent.wait(Duration::from_secs(120)).is_ok() {
                let _ = launch(&d.application_root);
            }
            return Err(error);
        }
    };
    parent.wait(Duration::from_secs(120))?;
    let mut transaction = match transaction::Transaction::new(d, &old_files, prepared) {
        Ok(t) => t,
        Err(error) => {
            atomic_json(
                &d.result_path,
                &outcome(d, false, false, format!("{error:#}"), 0, 0),
            )?;
            *failure_receipt_written = true;
            let _ = launch(&d.application_root);
            return Err(error);
        }
    };
    match transaction.apply(None) {
        Ok((updated, removed)) => {
            let mut receipt = outcome(d, true, false, String::new(), updated, removed);
            if let Err(error) =
                atomic_json(&d.result_path, &receipt).and_then(|_| launch(&d.application_root))
            {
                let restored = transaction.rollback().is_ok();
                let receipt = outcome(d, false, restored, format!("{error:#}"), 0, 0);
                *failure_receipt_written = atomic_json(&d.result_path, &receipt).is_ok();
                if restored {
                    let _ = launch(&d.application_root);
                }
                bail!("{error:#}");
            }
            // Only an existing, ownership-checked current-user registration is refreshed.
            // The application is already running successfully, so an OS metadata failure
            // is reported without rolling back its working binaries.
            if let Err(error) = crate::integration::refresh_version(&d.application_root, &d.version)
            {
                receipt.details = format!(
                    "Application updated; Windows version registration could not be refreshed: {error:#}"
                );
                let _ = atomic_json(&d.result_path, &receipt);
            }
            if let Err(cleanup) = transaction.finish() {
                receipt.details.push_str(&format!("\n{cleanup:#}"));
                let _ = atomic_json(&d.result_path, &receipt);
            }
            Ok(())
        }
        Err(error) => {
            let rollback = transaction.rollback();
            let restored = rollback.is_ok();
            let details = if let Err(rollback) = rollback {
                format!(
                    "{error:#}\nRollback incomplete; keep backups at {}.\n{rollback:#}",
                    transaction.path().display()
                )
            } else {
                format!("{error:#}")
            };
            atomic_json(&d.result_path, &outcome(d, false, restored, details, 0, 0))?;
            *failure_receipt_written = true;
            if restored {
                let _ = launch(&d.application_root);
            }
            Err(error)
        }
    }
}

#[cfg(test)]
mod tests;
