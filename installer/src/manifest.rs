use anyhow::{Context, Result, bail, ensure};
use serde::{Deserialize, Serialize};
use std::{
    collections::HashSet,
    path::{Component, Path, PathBuf},
};

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Manifest {
    pub schema_version: u32,
    pub version: String,
    pub executable: String,
    pub packages: Vec<Package>,
    /// Production setup installs the current trusted editorial snapshot before
    /// its first launch. Older/offline fixture manifests remain self-contained.
    #[serde(default)]
    pub install_current_database: bool,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub updates: Vec<UpdatePackage>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct UpdatePackage {
    pub from_version: String,
    pub base_inventory_sha256: String,
    pub package: Package,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Package {
    pub id: String,
    pub kind: PackageKind,
    pub filename: String,
    #[serde(default)]
    pub format: PackageFormat,
    #[serde(default)]
    pub url: Option<String>,
    pub sha256: String,
    pub bytes: u64,
    pub unpacked_bytes: u64,
    pub target: String,
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum PackageKind {
    App,
    Collection,
}

#[derive(Clone, Copy, Debug, Default, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum PackageFormat {
    #[default]
    Zip,
    Tar,
}

impl Manifest {
    pub fn parse(bytes: &[u8]) -> Result<Self> {
        ensure!(
            bytes.len() <= 1024 * 1024,
            "Manifest exceeds the 1 MiB limit"
        );
        let manifest: Self = serde_json::from_slice(bytes).context("Invalid release manifest")?;
        manifest.validate()?;
        Ok(manifest)
    }

    pub fn validate(&self) -> Result<()> {
        ensure!(
            self.schema_version == 1,
            "Unsupported manifest schema {}",
            self.schema_version
        );
        ensure!(
            !self.version.is_empty()
                && self.version.len() <= 100
                && !self.version.chars().any(char::is_control),
            "Invalid release version"
        );
        let exe = safe_relative_path(&self.executable)?;
        ensure!(
            exe.extension()
                .is_some_and(|e| e.eq_ignore_ascii_case("exe")),
            "Application executable must be an .exe"
        );
        ensure!(
            (2..=256).contains(&self.packages.len()),
            "A release needs app and collection packages (maximum 256)"
        );
        let mut ids = HashSet::new();
        let mut filenames = HashSet::new();
        let mut app_count = 0;
        let mut collection_count = 0;
        ensure!(self.updates.len() <= 32, "Too many incremental updates");
        let mut bases = HashSet::new();
        for update in &self.updates {
            ensure!(
                crate::update::version_is_newer(&update.from_version, &self.version)
                    && valid_sha256(&update.base_inventory_sha256)
                    && bases.insert(update.base_inventory_sha256.to_ascii_lowercase())
                    && update.package.kind == PackageKind::App,
                "Invalid incremental update base"
            );
        }
        for (p, is_update) in self.packages.iter().map(|p| (p, false)).chain(
            self.updates.iter().map(|update| (&update.package, true)),
        ) {
            ensure!(
                !p.id.is_empty()
                    && p.id.len() <= 100
                    && p.id
                        .chars()
                        .all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_'),
                "Invalid package id"
            );
            ensure!(
                ids.insert(p.id.to_ascii_lowercase()),
                "Duplicate package id"
            );
            let filename = safe_relative_path(&p.filename)?;
            let extension = match p.format {
                PackageFormat::Zip => "zip",
                PackageFormat::Tar => "tar",
            };
            ensure!(
                filename.components().count() == 1
                    && filename
                        .extension()
                        .is_some_and(|e| e.eq_ignore_ascii_case(extension)),
                "Package filename has the wrong archive extension"
            );
            ensure!(
                filenames.insert(p.filename.to_ascii_lowercase()),
                "Duplicate package filename"
            );
            ensure!(valid_sha256(&p.sha256), "Invalid SHA-256 for {}", p.id);
            ensure!(
                p.bytes > 0 && p.unpacked_bytes > 0 && p.bytes <= 100 * 1024 * 1024 * 1024,
                "Invalid size for {}",
                p.id
            );
            match p.kind {
                PackageKind::App => {
                    app_count += usize::from(!is_update);
                    ensure!(
                        p.target == "." && p.format == PackageFormat::Zip,
                        "App packages must be ZIPs targeting the installation root"
                    );
                }
                PackageKind::Collection => {
                    collection_count += 1;
                    let target = safe_relative_path(&p.target)?;
                    ensure!(
                        target.starts_with("collection"),
                        "Collection packages must remain under collection/"
                    );
                    ensure!(
                        p.format == PackageFormat::Zip
                            || (p.format == PackageFormat::Tar
                                && target.file_name().is_some_and(|n| n == "archives")
                                && p.unpacked_bytes == p.bytes),
                        "Retained TAR packages must target a collection archives folder and use unpacked_bytes = bytes"
                    );
                }
            }
            if let Some(url) = &p.url {
                validate_release_url(url)?;
            }
        }
        ensure!(
            app_count == 1 && collection_count > 0,
            "A release needs exactly one app package and at least one collection package"
        );
        self.download_bytes()?;
        self.unpacked_bytes()?;
        Ok(())
    }

    pub fn download_bytes(&self) -> Result<u64> {
        self.packages.iter().try_fold(0u64, |n, p| {
            n.checked_add(p.bytes).context("Download size overflow")
        })
    }
    pub fn unpacked_bytes(&self) -> Result<u64> {
        self.packages.iter().try_fold(0u64, |n, p| {
            n.checked_add(p.unpacked_bytes)
                .context("Installed size overflow")
        })
    }
}

pub fn valid_sha256(s: &str) -> bool {
    s.len() == 64 && s.bytes().all(|c| c.is_ascii_hexdigit())
}

/// Conservative Windows filename rules also applied when running tests on another OS.
pub fn safe_relative_path(name: &str) -> Result<PathBuf> {
    ensure!(
        !name.is_empty() && !name.contains('\\') && !name.starts_with('/'),
        "Unsafe archive path: {name}"
    );
    let mut result = PathBuf::new();
    for part in name.trim_end_matches('/').split('/') {
        ensure!(
            !part.is_empty()
                && part != "."
                && part != ".."
                && !part.ends_with(['.', ' '])
                && !part
                    .chars()
                    .any(|c| c.is_control() || "<>:\"|?*".contains(c)),
            "Unsafe Windows path: {name}"
        );
        let stem = part.split('.').next().unwrap_or("").to_ascii_uppercase();
        ensure!(
            !matches!(stem.as_str(), "CON" | "PRN" | "AUX" | "NUL")
                && !(stem.len() == 4
                    && (stem.starts_with("COM") || stem.starts_with("LPT"))
                    && matches!(stem.as_bytes()[3], b'1'..=b'9')),
            "Reserved Windows filename: {name}"
        );
        result.push(part);
    }
    ensure!(
        result
            .components()
            .all(|c| matches!(c, Component::Normal(_))),
        "Unsafe path: {name}"
    );
    Ok(result)
}

pub fn validate_release_url(value: &str) -> Result<reqwest::Url> {
    let url = reqwest::Url::parse(value).context("Invalid release URL")?;
    ensure!(
        url.scheme() == "https"
            && url.host_str() == Some("github.com")
            && url.username().is_empty()
            && url.password().is_none()
            && url.port().is_none()
            && url.query().is_none()
            && url.fragment().is_none(),
        "Downloads must use a direct HTTPS GitHub release URL"
    );
    let parts: Vec<_> = url.path().split('/').filter(|s| !s.is_empty()).collect();
    ensure!(
        parts.len() == 6
            && parts[0].eq_ignore_ascii_case("LoZazaMastro")
            && parts[1].eq_ignore_ascii_case("Pixel-Museum")
            && parts[2] == "releases"
            && parts[3] == "download"
            && !parts[4].is_empty()
            && !parts[5].is_empty(),
        "Only tagged LoZazaMastro/Pixel-Museum release assets are accepted"
    );
    Ok(url)
}

pub fn ensure_no_links(path: &Path) -> Result<()> {
    for ancestor in path.ancestors() {
        match std::fs::symlink_metadata(ancestor) {
            Ok(meta) => {
                ensure!(
                    !meta.file_type().is_symlink(),
                    "Symbolic links are not allowed in the installation path"
                );
                #[cfg(windows)]
                {
                    use std::os::windows::fs::MetadataExt;
                    ensure!(
                        meta.file_attributes() & 0x400 == 0,
                        "Reparse points are not allowed in the installation path"
                    );
                }
            }
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => (),
            Err(e) => bail!("Cannot inspect {}: {e}", ancestor.display()),
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejects_windows_escape_and_alias_paths() {
        for name in [
            "../escape",
            "a/../escape",
            "C:/escape",
            "a\\escape",
            "/escape",
            "a//b",
            "NUL.txt",
            "a/COM1",
            "file.",
            "file ",
            "a:stream",
            "./file",
        ] {
            assert!(safe_relative_path(name).is_err(), "{name}");
        }
        assert_eq!(
            safe_relative_path("assets/images/exhibit.webp").unwrap(),
            PathBuf::from("assets/images/exhibit.webp")
        );
    }
    #[test]
    fn only_accepts_tagged_project_release_urls() {
        assert!(
            validate_release_url(
                "https://github.com/LoZazaMastro/Pixel-Museum/releases/download/v1.0/app.zip"
            )
            .is_ok()
        );
        for url in [
            "http://github.com/LoZazaMastro/Pixel-Museum/releases/download/v1/app.zip",
            "https://github.com/other/repo/releases/download/v1/app.zip",
            "https://github.com/LoZazaMastro/Pixel-Museum/releases/latest/download/app.zip",
        ] {
            assert!(validate_release_url(url).is_err());
        }
    }
}
