use super::*;

#[derive(Clone, Debug, Serialize, Deserialize)]
struct Entry {
    path: String,
    original: bool,
    original_sha256: Option<String>,
    new_sha256: Option<String>,
    backup_done: bool,
    installed: bool,
}
#[derive(Serialize, Deserialize)]
struct Journal {
    schema_version: u32,
    application_id: String,
    version: String,
    archive_sha256: String,
    phase: String,
    entries: Vec<Entry>,
}
pub(super) struct Transaction {
    root: PathBuf,
    directory: Option<tempfile::TempDir>,
    journal: Journal,
    started: bool,
    finalized: bool,
}

fn target(root: &Path, name: &str) -> Result<PathBuf> {
    ensure!(
        allowed(name) && !protected(name),
        "Update cannot replace a protected or unowned path"
    );
    let path = root.join(safe_relative_path(name)?);
    ensure_no_links(&path)?;
    for ancestor in path.parent().unwrap().ancestors() {
        if ancestor.exists() {
            ensure!(ancestor.is_dir(), "A parent path is not a directory");
        }
        if path_key(ancestor) == path_key(root) {
            break;
        }
    }
    if path.exists() {
        let _ = process::open_regular(&path)?;
    }
    Ok(path)
}

impl Transaction {
    pub(super) fn new(
        d: &Descriptor,
        old: &BTreeMap<String, OwnedFile>,
        prepared: Prepared,
    ) -> Result<Self> {
        let stage = prepared.directory.path().join("new");
        let mut files = prepared.files;
        let inventory_path = stage.join(INVENTORY);
        files.insert(
            INVENTORY.into(),
            OwnedFile {
                path: INVENTORY.into(),
                bytes: fs::metadata(&inventory_path)?.len(),
                sha256: hash_file(&inventory_path)?,
            },
        );
        let mut entries = Vec::new();
        for (k, file) in &files {
            if protected(&file.path) {
                continue;
            }
            let path = target(&d.application_root, &file.path)?;
            let original = path.exists();
            ensure!(
                !original || old.contains_key(k) || k == INVENTORY,
                "Refusing to overwrite a pre-existing unowned file: {}",
                file.path
            );
            let original_sha256 = if original {
                Some(hash_file(&path)?)
            } else {
                None
            };
            // The executable always moves out first and returns last, preventing
            // a new launch while its libraries are being replaced.
            if k != "pixel museum.exe"
                && k != INVENTORY
                && original_sha256.as_ref() == Some(&file.sha256)
            {
                continue;
            }
            entries.push(Entry {
                path: file.path.clone(),
                original,
                original_sha256,
                new_sha256: Some(file.sha256.clone()),
                backup_done: false,
                installed: false,
            });
        }
        for (k, file) in old {
            if files.contains_key(k) || protected(&file.path) {
                continue;
            }
            let path = target(&d.application_root, &file.path)?;
            if !path.exists() {
                continue;
            }
            ensure!(
                fs::metadata(&path)?.len() == file.bytes && hash_file(&path)? == file.sha256,
                "Obsolete owned file has changed; it was preserved: {}",
                file.path
            );
            entries.push(Entry {
                path: file.path.clone(),
                original: true,
                original_sha256: Some(file.sha256.clone()),
                new_sha256: None,
                backup_done: false,
                installed: false,
            });
        }
        ensure!(
            prepared.inventory.version == d.version,
            "Prepared inventory version changed"
        );
        let transaction = Self {
            root: d.application_root.clone(),
            directory: Some(prepared.directory),
            journal: Journal {
                schema_version: 1,
                application_id: "pixel-museum".into(),
                version: d.version.clone(),
                archive_sha256: d.archive_sha256.clone(),
                phase: "prepared".into(),
                entries,
            },
            started: false,
            finalized: false,
        };
        transaction.save()?;
        Ok(transaction)
    }
    pub(super) fn path(&self) -> &Path {
        self.directory.as_ref().unwrap().path()
    }
    fn save(&self) -> Result<()> {
        atomic_json(&self.path().join("journal.json"), &self.journal)
    }
    fn backup_path(&self, name: &str) -> Result<PathBuf> {
        Ok(self.path().join("backup").join(safe_relative_path(name)?))
    }
    fn fail(count: usize, at: Option<usize>) -> Result<()> {
        ensure!(
            at != Some(count),
            "Injected update transaction failure after filesystem mutation {count}"
        );
        Ok(())
    }

    pub(super) fn apply(&mut self, fail_after: Option<usize>) -> Result<(usize, usize)> {
        self.started = true;
        self.journal.phase = "applying".into();
        self.save()?;
        let mut indices: Vec<_> = (0..self.journal.entries.len()).collect();
        indices.sort_by_key(|i| key(&self.journal.entries[*i].path) != "pixel museum.exe");
        let mut mutations = 0;
        for &i in &indices {
            let entry = self.journal.entries[i].clone();
            if !entry.original {
                continue;
            }
            let from = target(&self.root, &entry.path)?;
            ensure!(
                Some(hash_file(&from)?) == entry.original_sha256,
                "Application file changed after preflight"
            );
            let backup = self.backup_path(&entry.path)?;
            ensure_no_links(&backup)?;
            fs::create_dir_all(backup.parent().unwrap())?;
            fs::rename(&from, &backup).with_context(|| {
                format!(
                    "Cannot back up {}; close applications using this file",
                    entry.path
                )
            })?;
            self.journal.entries[i].backup_done = true;
            self.save()?;
            mutations += 1;
            Self::fail(mutations, fail_after)?;
        }
        indices.sort_by_key(|i| key(&self.journal.entries[*i].path) == "pixel museum.exe");
        for &i in &indices {
            let entry = self.journal.entries[i].clone();
            if entry.new_sha256.is_none() {
                continue;
            }
            let destination = target(&self.root, &entry.path)?;
            ensure!(
                !destination.exists(),
                "A file appeared in an update destination"
            );
            fs::create_dir_all(destination.parent().unwrap())?;
            ensure_no_links(&destination)?;
            let source = self
                .path()
                .join("new")
                .join(safe_relative_path(&entry.path)?);
            fs::rename(&source, &destination)
                .with_context(|| format!("Cannot install {}", entry.path))?;
            self.journal.entries[i].installed = true;
            self.save()?;
            mutations += 1;
            Self::fail(mutations, fail_after)?;
        }
        self.journal.phase = "applied".into();
        self.save()?;
        Ok((
            self.journal.entries.iter().filter(|e| e.installed).count(),
            self.journal
                .entries
                .iter()
                .filter(|e| e.new_sha256.is_none())
                .count(),
        ))
    }

    pub(super) fn rollback(&mut self) -> Result<()> {
        self.journal.phase = "rolling_back".into();
        let _ = self.save();
        let mut indices: Vec<_> = (0..self.journal.entries.len()).collect();
        indices.sort_by_key(|i| key(&self.journal.entries[*i].path) == "pixel museum.exe");
        let mut errors = Vec::new();
        for i in indices {
            let entry = self.journal.entries[i].clone();
            if key(&entry.path) == "pixel museum.exe" && !errors.is_empty() {
                continue;
            }
            let restored = (|| -> Result<()> {
                let destination = target(&self.root, &entry.path)?;
                if entry.installed && destination.exists() {
                    ensure!(
                        Some(hash_file(&destination)?) == entry.new_sha256,
                        "Updated file changed before rollback; preserved it"
                    );
                    fs::remove_file(&destination)?;
                }
                if entry.backup_done {
                    let backup = self.backup_path(&entry.path)?;
                    ensure!(
                        backup.is_file() && Some(hash_file(&backup)?) == entry.original_sha256,
                        "Rollback backup is missing or damaged"
                    );
                    ensure!(
                        !destination.exists(),
                        "Rollback would overwrite an unrelated file"
                    );
                    fs::rename(&backup, &destination)?;
                }
                if entry.original {
                    ensure!(
                        Some(hash_file(&destination)?) == entry.original_sha256,
                        "Original file was not restored"
                    );
                } else {
                    ensure!(
                        !destination.exists(),
                        "New file was not removed during rollback"
                    );
                }
                Ok(())
            })();
            if let Err(error) = restored {
                errors.push(format!("{}: {error:#}", entry.path));
            }
        }
        ensure!(
            errors.is_empty(),
            "Rollback requires recovery from {}: {}",
            self.path().display(),
            errors.join("; ")
        );
        self.journal.phase = "rolled_back".into();
        let _ = self.save();
        self.finalized = true;
        if let Some(directory) = self.directory.take() {
            let _ = directory.close();
        }
        Ok(())
    }
    pub(super) fn finish(&mut self) -> Result<()> {
        self.journal.phase = "committed".into();
        self.save()?;
        self.finalized = true;
        if let Some(directory) = self.directory.take() {
            directory
                .close()
                .context("Update succeeded; backup cleanup was deferred")?;
        }
        Ok(())
    }
}
impl Drop for Transaction {
    fn drop(&mut self) {
        // Never let RAII delete the only surviving old executable/backups after
        // an incomplete rollback, unwinding panic or an error recording state.
        if self.started && !self.finalized {
            if let Some(directory) = self.directory.take() {
                let _ = directory.keep();
            }
        }
    }
}
