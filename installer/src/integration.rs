//! Current-user Windows integration. Tests provide private folders/registry roots.
use crate::manifest::ensure_no_links;
use anyhow::{Context, Result, ensure};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    fs,
    path::{Path, PathBuf},
};
use windows::{
    Win32::{
        Foundation::{ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND},
        System::{
            Com::{
                CLSCTX_INPROC_SERVER, COINIT_APARTMENTTHREADED, CoCreateInstance, CoInitializeEx,
                CoTaskMemFree, CoUninitialize, IPersistFile, STGM_READ,
            },
            Registry::*,
        },
        UI::{
            Shell::{
                FOLDERID_Desktop, FOLDERID_Programs, IShellLinkW, KF_FLAG_DEFAULT,
                SHGetKnownFolderPath, ShellLink,
            },
            WindowsAndMessaging::SW_SHOWNORMAL,
        },
    },
    core::{Interface, PCWSTR},
};

pub const HELPER: &str = "tools/windows-updater/Pixel-Museum-Updater.exe";
pub const HELPER_CAPABILITY: &[u8] = b"PIXEL_MUSEUM_HELPER_V2_UNINSTALL_PRESERVE_DATA_NO_BOOTSTRAP";
pub const RECEIPT: &str = "pixel-museum-install.json";
const UNINSTALL_BASE: &str = r"Software\Microsoft\Windows\CurrentVersion\Uninstall";

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Registration {
    pub schema_version: u32,
    pub installation_id: String,
    pub installer_language: String,
    pub desktop_shortcut: bool,
    pub uninstaller: String,
}
#[derive(Clone, Debug)]
pub struct Environment {
    pub programs: PathBuf,
    pub desktop: PathBuf,
    pub registry_base: String,
}
fn wide(value: impl AsRef<std::ffi::OsStr>) -> Vec<u16> {
    use std::os::windows::ffi::OsStrExt;
    value.as_ref().encode_wide().chain(Some(0)).collect()
}
fn key(path: &Path) -> String {
    crate::update::path_key(path).trim_end_matches('/').into()
}
pub fn installation_id(root: &Path) -> Result<String> {
    let normalized = if root.exists() {
        fs::canonicalize(root)?
    } else {
        fs::canonicalize(root.parent().context("Missing install parent")?)?
            .join(root.file_name().context("Missing install name")?)
    };
    Ok(format!("{:x}", Sha256::digest(key(&normalized).as_bytes()))[..24].into())
}
pub fn registration(root: &Path, language: &str, desktop: bool) -> Result<Registration> {
    ensure!(
        ["en", "it", "fr", "de", "es"].contains(&language),
        "Invalid installer language"
    );
    Ok(Registration {
        schema_version: 1,
        installation_id: installation_id(root)?,
        installer_language: language.into(),
        desktop_shortcut: desktop,
        uninstaller: HELPER.into(),
    })
}
pub fn validate(root: &Path, r: &Registration) -> Result<()> {
    ensure!(
        r.schema_version == 1
            && r.installation_id == installation_id(root)?
            && r.uninstaller == HELPER
            && ["en", "it", "fr", "de", "es"].contains(&r.installer_language.as_str()),
        "Invalid Windows installation registration"
    );
    Ok(())
}
impl Environment {
    pub fn current_user() -> Result<Self> {
        unsafe fn folder(id: &windows::core::GUID) -> Result<PathBuf> {
            let value = unsafe { SHGetKnownFolderPath(id, KF_FLAG_DEFAULT, None) }?;
            let text = unsafe { value.to_string() };
            unsafe { CoTaskMemFree(Some(value.0.cast())) };
            let path = PathBuf::from(text?);
            ensure!(path.is_absolute(), "Invalid Windows known folder");
            Ok(path)
        }
        Ok(Self {
            programs: unsafe { folder(&FOLDERID_Programs) }?,
            desktop: unsafe { folder(&FOLDERID_Desktop) }?,
            registry_base: UNINSTALL_BASE.into(),
        })
    }
    fn registry_key(&self, r: &Registration) -> String {
        format!(r"{}\PixelMuseum_{}", self.registry_base, r.installation_id)
    }
    pub fn program_link(&self) -> PathBuf {
        self.programs.join("Pixel Museum/Pixel Museum.lnk")
    }
    pub fn desktop_link(&self) -> PathBuf {
        self.desktop.join("Pixel Museum.lnk")
    }
    #[cfg(test)]
    pub fn cleanup_fixture(&self) {
        assert!(
            self.registry_base
                .starts_with(r"Software\PixelMuseum\InstallerTests\")
        );
        remove_key(&self.registry_base).unwrap();
    }
}

struct Apartment;
impl Apartment {
    fn enter() -> Result<Self> {
        unsafe { CoInitializeEx(None, COINIT_APARTMENTTHREADED) }.ok()?;
        Ok(Self)
    }
}
impl Drop for Apartment {
    fn drop(&mut self) {
        unsafe { CoUninitialize() }
    }
}
fn save_shortcut(path: &Path, target: &Path, root: &Path, arguments: &str) -> Result<()> {
    ensure_no_links(path)?;
    fs::create_dir_all(path.parent().unwrap())?;
    if path.exists() {
        let _ = crate::update::process::open_regular(path)?;
    }
    let temporary = tempfile::NamedTempFile::new_in(path.parent().unwrap())?.into_temp_path();
    let _apartment = Apartment::enter()?;
    unsafe {
        let link: IShellLinkW = CoCreateInstance(&ShellLink, None, CLSCTX_INPROC_SERVER)?;
        let target = wide(target);
        let working = wide(root);
        let args = wide(arguments);
        let description = wide("Pixel Museum");
        link.SetPath(PCWSTR(target.as_ptr()))
            .context("Cannot assign Windows shortcut target")?;
        link.SetWorkingDirectory(PCWSTR(working.as_ptr()))?;
        link.SetArguments(PCWSTR(args.as_ptr()))?;
        link.SetDescription(PCWSTR(description.as_ptr()))?;
        link.SetIconLocation(PCWSTR(target.as_ptr()), 0)?;
        link.SetShowCmd(SW_SHOWNORMAL)?;
        let persist: IPersistFile = link.cast()?;
        let output = wide(temporary.as_os_str());
        persist
            .Save(PCWSTR(output.as_ptr()), true)
            .context("Cannot write Windows shortcut")?;
    }
    temporary
        .persist(path)
        .context("Cannot save Windows shortcut")?;
    Ok(())
}
pub fn shortcut_target(path: &Path) -> Result<(PathBuf, String)> {
    let _ = crate::update::process::open_regular(path)?;
    let _apartment = Apartment::enter()?;
    unsafe {
        let link: IShellLinkW = CoCreateInstance(&ShellLink, None, CLSCTX_INPROC_SERVER)?;
        let persist: IPersistFile = link.cast()?;
        let path = wide(path);
        persist.Load(PCWSTR(path.as_ptr()), STGM_READ)?;
        let mut target = vec![0u16; 32768];
        let mut args = vec![0u16; 32768];
        link.GetPath(&mut target, std::ptr::null_mut(), 4)?;
        link.GetArguments(&mut args)?;
        let decode = |text: &[u16]| {
            String::from_utf16(&text[..text.iter().position(|c| *c == 0).unwrap_or(text.len())])
        };
        Ok((PathBuf::from(decode(&target)?), decode(&args)?))
    }
}

struct RegistryKey(HKEY);
impl Drop for RegistryKey {
    fn drop(&mut self) {
        let _ = unsafe { RegCloseKey(self.0) };
    }
}
impl RegistryKey {
    fn open(path: &str, write: bool) -> Result<Option<Self>> {
        let mut result = HKEY::default();
        let path = wide(path);
        let code = unsafe {
            RegOpenKeyExW(
                HKEY_CURRENT_USER,
                PCWSTR(path.as_ptr()),
                None,
                if write {
                    KEY_READ | KEY_WRITE | KEY_WOW64_64KEY
                } else {
                    KEY_READ | KEY_WOW64_64KEY
                },
                &mut result,
            )
        };
        if code == ERROR_FILE_NOT_FOUND || code == ERROR_PATH_NOT_FOUND {
            return Ok(None);
        }
        code.ok()?;
        Ok(Some(Self(result)))
    }
    fn create(path: &str) -> Result<Self> {
        let mut result = HKEY::default();
        let path = wide(path);
        unsafe {
            RegCreateKeyExW(
                HKEY_CURRENT_USER,
                PCWSTR(path.as_ptr()),
                None,
                PCWSTR::null(),
                REG_OPTION_NON_VOLATILE,
                KEY_READ | KEY_WRITE | KEY_WOW64_64KEY,
                None,
                &mut result,
                None,
            )
        }
        .ok()?;
        Ok(Self(result))
    }
    fn raw(&self, name: &str) -> Result<Option<(REG_VALUE_TYPE, Vec<u8>)>> {
        let name = wide(name);
        let mut kind = REG_VALUE_TYPE::default();
        let mut bytes = 0u32;
        let code = unsafe {
            RegQueryValueExW(
                self.0,
                PCWSTR(name.as_ptr()),
                None,
                Some(&mut kind),
                None,
                Some(&mut bytes),
            )
        };
        if code == ERROR_FILE_NOT_FOUND {
            return Ok(None);
        }
        code.ok()?;
        ensure!(bytes <= 128 * 1024, "Registry value is too large");
        let mut data = vec![0u8; bytes as usize];
        unsafe {
            RegQueryValueExW(
                self.0,
                PCWSTR(name.as_ptr()),
                None,
                Some(&mut kind),
                Some(data.as_mut_ptr()),
                Some(&mut bytes),
            )
        }
        .ok()?;
        data.truncate(bytes as usize);
        Ok(Some((kind, data)))
    }
    fn string(&self, name: &str) -> Result<Option<String>> {
        let Some((kind, data)) = self.raw(name)? else {
            return Ok(None);
        };
        ensure!(
            kind == REG_SZ && data.len() % 2 == 0,
            "Unexpected registry value type"
        );
        let words: Vec<_> = data
            .chunks_exact(2)
            .map(|p| u16::from_le_bytes([p[0], p[1]]))
            .take_while(|w| *w != 0)
            .collect();
        Ok(Some(String::from_utf16(&words)?))
    }
    fn set(&self, name: &str, kind: REG_VALUE_TYPE, data: &[u8]) -> Result<()> {
        let name = wide(name);
        unsafe { RegSetValueExW(self.0, PCWSTR(name.as_ptr()), None, kind, Some(data)) }.ok()?;
        Ok(())
    }
    fn set_string(&self, name: &str, value: &str) -> Result<()> {
        let data: Vec<u8> = wide(value).iter().flat_map(|w| w.to_le_bytes()).collect();
        self.set(name, REG_SZ, &data)
    }
    fn set_dword(&self, name: &str, value: u32) -> Result<()> {
        self.set(name, REG_DWORD, &value.to_le_bytes())
    }
}
fn remove_key(path: &str) -> Result<()> {
    let path = wide(path);
    let code = unsafe { RegDeleteTreeW(HKEY_CURRENT_USER, PCWSTR(path.as_ptr())) };
    if code != ERROR_FILE_NOT_FOUND && code != ERROR_PATH_NOT_FOUND {
        code.ok()?;
    }
    Ok(())
}
fn command(root: &Path, quiet: bool) -> String {
    // Windows CommandLineToArgvW doubles trailing backslashes inside quotes.
    let text = root.to_string_lossy();
    let trailing = text.chars().rev().take_while(|c| *c == '\\').count();
    format!(
        "\"{}\" --uninstall \"{}{}\"{}",
        root.join(HELPER).display(),
        root.display(),
        "\\".repeat(trailing),
        if quiet { " --quiet" } else { "" }
    )
}
const MANAGED: &[&str] = &[
    "DisplayName",
    "DisplayVersion",
    "Publisher",
    "InstallLocation",
    "DisplayIcon",
    "UninstallString",
    "URLInfoAbout",
    "EstimatedSize",
    "NoModify",
    "NoRepair",
];

pub fn register(
    root: &Path,
    version: &str,
    bytes: u64,
    r: &Registration,
    environment: &Environment,
) -> Result<()> {
    validate(root, r)?;
    let registry_path = environment.registry_key(r);
    let previous = RegistryKey::open(&registry_path, false)?;
    if let Some(previous) = &previous {
        ensure!(
            previous
                .string("InstallLocation")?
                .is_some_and(|s| key(Path::new(&s)) == key(root)),
            "Another installation owns this Windows registration"
        );
    }
    let old_registry = if let Some(previous) = &previous {
        Some(
            MANAGED
                .iter()
                .map(|n| Ok(((*n).to_owned(), previous.raw(n)?)))
                .collect::<Result<Vec<_>>>()?,
        )
    } else {
        None
    };
    drop(previous);
    let paths = if r.desktop_shortcut {
        vec![environment.program_link(), environment.desktop_link()]
    } else {
        vec![environment.program_link()]
    };
    let mut old_links = Vec::new();
    for path in &paths {
        ensure_no_links(path)?;
        old_links.push((
            path.clone(),
            if path.exists() {
                let _ = crate::update::process::open_regular(path)?;
                Some(fs::read(path)?)
            } else {
                None
            },
        ));
        if path.exists() {
            let (target, args) = shortcut_target(path)?;
            ensure!(
                key(&target) == key(&root.join("Pixel Museum.exe")) && args.is_empty(),
                "A shortcut at {} belongs to another application or installation",
                path.display()
            );
        }
    }
    let operation = (|| -> Result<()> {
        for path in &paths {
            save_shortcut(path, &root.join("Pixel Museum.exe"), root, "")?;
        }
        let registry = RegistryKey::create(&registry_path)?;
        for (name, value) in [
            ("DisplayName", "Pixel Museum".to_owned()),
            ("DisplayVersion", version.into()),
            ("Publisher", "Andrea Sgarro / LoZazaMastro".into()),
            ("InstallLocation", root.to_string_lossy().into_owned()),
            (
                "DisplayIcon",
                format!("\"{}\",0", root.join("Pixel Museum.exe").display()),
            ),
            ("UninstallString", command(root, false)),
            (
                "URLInfoAbout",
                "https://lozazamastro.github.io/Pixel-Museum/".into(),
            ),
        ] {
            registry.set_string(name, &value)?;
        }
        registry.set_dword(
            "EstimatedSize",
            bytes.div_ceil(1024).min(u32::MAX as u64) as u32,
        )?;
        registry.set_dword("NoModify", 1)?;
        registry.set_dword("NoRepair", 1)?;
        Ok(())
    })();
    if let Err(error) = operation {
        for (path, old) in old_links {
            if let Some(bytes) = old {
                let _ = fs::write(path, bytes);
            } else {
                let _ = fs::remove_file(path);
            }
        }
        if let Some(values) = old_registry {
            if let Ok(registry) = RegistryKey::create(&registry_path) {
                for (name, value) in values {
                    if let Some((kind, data)) = value {
                        let _ = registry.set(&name, kind, &data);
                    } else {
                        let name = wide(name);
                        let _ = unsafe { RegDeleteValueW(registry.0, PCWSTR(name.as_ptr())) };
                    }
                }
            }
        } else {
            let _ = remove_key(&registry_path);
        }
        return Err(error.context("Cannot register Pixel Museum in Windows"));
    }
    Ok(())
}

pub fn unregister(root: &Path, r: &Registration, environment: &Environment) -> Result<()> {
    validate(root, r)?;
    let registry_path = environment.registry_key(r);
    let registered = if let Some(registry) = RegistryKey::open(&registry_path, false)? {
        ensure!(
            registry
                .string("InstallLocation")?
                .is_some_and(|s| key(Path::new(&s)) == key(root)),
            "Windows registration belongs to another installation"
        );
        true
    } else {
        false
    };
    let mut links = vec![environment.program_link()];
    if r.desktop_shortcut {
        links.push(environment.desktop_link());
    }
    let mut owned_links = Vec::new();
    for path in links {
        if !path.exists() {
            continue;
        }
        if let Ok((target, args)) = shortcut_target(&path) {
            if key(&target) == key(&root.join("Pixel Museum.exe")) && args.is_empty() {
                owned_links.push((path.clone(), fs::read(&path)?));
            }
        }
    }
    let operation = (|| -> Result<()> {
        for (path, _) in &owned_links {
            fs::remove_file(path)?;
        }
        if registered {
            let path = wide(&registry_path);
            // Refuse unexpected subkeys instead of recursively deleting registry content.
            unsafe {
                RegDeleteKeyExW(
                    HKEY_CURRENT_USER,
                    PCWSTR(path.as_ptr()),
                    KEY_WOW64_64KEY.0,
                    None,
                )
            }
            .ok()?;
        }
        Ok(())
    })();
    if let Err(error) = operation {
        let mut restoration = Vec::new();
        for (path, bytes) in &owned_links {
            if !path.exists() {
                if let Err(e) = fs::write(path, bytes) {
                    restoration.push(format!("{}: {e}", path.display()));
                }
            }
        }
        ensure!(
            restoration.is_empty(),
            "{error:#}; shortcut restoration failed: {}",
            restoration.join("; ")
        );
        return Err(error.context("Cannot remove Windows registration; shortcuts restored"));
    }
    if owned_links
        .iter()
        .any(|(p, _)| p == &environment.program_link())
    {
        let _ = fs::remove_dir(environment.program_link().parent().unwrap());
    }
    Ok(())
}
pub fn refresh_version(root: &Path, version: &str) -> Result<()> {
    let receipt: serde_json::Value = serde_json::from_slice(&fs::read(root.join(RECEIPT))?)?;
    let Some(value) = receipt.get("windows_integration") else {
        return Ok(());
    };
    let r: Registration = serde_json::from_value(value.clone())?;
    validate(root, &r)?;
    refresh_version_with(root, version, &r, &Environment::current_user()?)
}
fn refresh_version_with(
    root: &Path,
    version: &str,
    r: &Registration,
    environment: &Environment,
) -> Result<()> {
    if let Some(registry) = RegistryKey::open(&environment.registry_key(r), true)? {
        ensure!(
            registry
                .string("InstallLocation")?
                .is_some_and(|s| key(Path::new(&s)) == key(root)),
            "Windows registration root mismatch"
        );
        registry.set_string("DisplayVersion", version)?;
    }
    Ok(())
}

pub fn validate_helper(stage: &Path) -> Result<()> {
    let helper = stage.join(HELPER);
    crate::update::process::executable_header(&helper)?;
    let inventory_path = stage.join("application-files.json");
    let inventory: crate::update::Inventory = serde_json::from_slice(
        &fs::read(&inventory_path).context("App package must contain application-files.json")?,
    )?;
    inventory.validate()?;
    let entry = inventory
        .files
        .iter()
        .find(|f| f.path.eq_ignore_ascii_case(HELPER))
        .context("The app payload does not inventory its maintenance helper")?;
    let bytes = crate::update::read_limited(&helper, 64 * 1024 * 1024)?;
    ensure!(
        bytes.len() as u64 == entry.bytes
            && format!("{:x}", Sha256::digest(&bytes)) == entry.sha256,
        "Payload maintenance helper does not match its inventory"
    );
    ensure!(
        bytes
            .windows(HELPER_CAPABILITY.len())
            .any(|part| part == HELPER_CAPABILITY),
        "This app payload needs the current r5 maintenance helper. Older r4 packages cannot be installed by this setup."
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn private_user_registration_roundtrip_and_version_refresh() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path().join("Pixel Museum");
        fs::create_dir(&root).unwrap();
        fs::write(root.join("Pixel Museum.exe"), b"fixture target").unwrap();
        let environment = Environment {
            programs: temp.path().join("Programs"),
            desktop: temp.path().join("Desktop"),
            registry_base: format!(
                r"Software\PixelMuseum\InstallerTests\{}",
                temp.path().file_name().unwrap().to_string_lossy()
            ),
        };
        fs::create_dir_all(&environment.programs).unwrap();
        fs::create_dir_all(&environment.desktop).unwrap();
        let r = registration(&root, "it", true).unwrap();
        register(&root, "0.2.0", 123456, &r, &environment).unwrap();
        for path in [environment.program_link(), environment.desktop_link()] {
            let (target, args) = shortcut_target(&path).unwrap();
            assert_eq!(key(&target), key(&root.join("Pixel Museum.exe")));
            assert!(args.is_empty());
        }
        let registry = RegistryKey::open(&environment.registry_key(&r), false)
            .unwrap()
            .unwrap();
        assert_eq!(
            registry.string("DisplayName").unwrap().unwrap(),
            "Pixel Museum"
        );
        assert_eq!(registry.string("DisplayVersion").unwrap().unwrap(), "0.2.0");
        assert!(
            registry
                .string("UninstallString")
                .unwrap()
                .unwrap()
                .contains(" --uninstall \"")
        );
        drop(registry);
        refresh_version_with(&root, "0.2.1", &r, &environment).unwrap();
        assert_eq!(
            RegistryKey::open(&environment.registry_key(&r), false)
                .unwrap()
                .unwrap()
                .string("DisplayVersion")
                .unwrap()
                .unwrap(),
            "0.2.1"
        );
        unregister(&root, &r, &environment).unwrap();
        assert!(
            RegistryKey::open(&environment.registry_key(&r), false)
                .unwrap()
                .is_none()
        );
        assert!(!environment.program_link().exists());
        assert!(!environment.desktop_link().exists());
        environment.cleanup_fixture();
    }
    #[test]
    fn shortcuts_owned_by_another_install_are_never_replaced_or_removed() {
        let temp = tempfile::tempdir().unwrap();
        let first = temp.path().join("first");
        let second = temp.path().join("second");
        fs::create_dir(&first).unwrap();
        fs::create_dir(&second).unwrap();
        fs::write(first.join("Pixel Museum.exe"), b"fixture one").unwrap();
        fs::write(second.join("Pixel Museum.exe"), b"fixture two").unwrap();
        let environment = Environment {
            programs: temp.path().join("Programs"),
            desktop: temp.path().join("Desktop"),
            registry_base: format!(
                r"Software\PixelMuseum\InstallerTests\{}",
                temp.path().file_name().unwrap().to_string_lossy()
            ),
        };
        fs::create_dir_all(&environment.desktop).unwrap();
        let a = registration(&first, "en", true).unwrap();
        let b = registration(&second, "it", true).unwrap();
        register(&first, "0.2.0", 10, &a, &environment).unwrap();
        let before = fs::read(environment.program_link()).unwrap();
        assert!(register(&second, "0.2.0", 10, &b, &environment).is_err());
        assert_eq!(fs::read(environment.program_link()).unwrap(), before);
        unregister(&second, &b, &environment).unwrap();
        assert!(environment.program_link().exists());
        unregister(&first, &a, &environment).unwrap();
        environment.cleanup_fixture();
    }
    #[test]
    fn uninstall_registration_failure_restores_the_removed_shortcuts() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path().join("Pixel Museum");
        fs::create_dir(&root).unwrap();
        fs::write(root.join("Pixel Museum.exe"), b"fixture").unwrap();
        let environment = Environment {
            programs: temp.path().join("Programs"),
            desktop: temp.path().join("Desktop"),
            registry_base: format!(
                r"Software\PixelMuseum\InstallerTests\{}",
                temp.path().file_name().unwrap().to_string_lossy()
            ),
        };
        fs::create_dir_all(&environment.desktop).unwrap();
        let r = registration(&root, "it", true).unwrap();
        register(&root, "0.2.0", 100, &r, &environment).unwrap();
        let before = fs::read(environment.program_link()).unwrap();
        let child = format!(r"{}\Unexpected", environment.registry_key(&r));
        drop(RegistryKey::create(&child).unwrap());
        assert!(unregister(&root, &r, &environment).is_err());
        assert_eq!(fs::read(environment.program_link()).unwrap(), before);
        assert!(environment.desktop_link().exists());
        remove_key(&child).unwrap();
        unregister(&root, &r, &environment).unwrap();
        environment.cleanup_fixture();
    }
}
