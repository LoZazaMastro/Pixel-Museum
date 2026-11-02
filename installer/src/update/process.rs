use anyhow::{Context, Result, ensure};
use std::{
    fs::{File, OpenOptions},
    path::Path,
    time::Duration,
};

pub fn open_regular(path: &Path) -> Result<File> {
    crate::manifest::ensure_no_links(path)?;
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt;
        options.share_mode(1); // Keep verified bytes immutable while this handle is open.
    }
    let file = options
        .open(path)
        .with_context(|| format!("Cannot read {}", path.display()))?;
    validate_regular_handle(&file, true)?;
    Ok(file)
}

/// Verify the actual opened object before any writes. Read-only archives may have
/// immutable input aliases; writable cache files must have exactly one link.
pub fn validate_regular_handle(file: &File, single_link: bool) -> Result<()> {
    ensure!(file.metadata()?.is_file(), "Expected an ordinary file");
    #[cfg(windows)]
    {
        use std::os::windows::io::AsRawHandle;
        let mut info = FileInformation::default();
        ensure!(
            unsafe { GetFileInformationByHandle(file.as_raw_handle(), &mut info) } != 0,
            "Cannot inspect file identity"
        );
        ensure!(
            info.attributes & 0x400 == 0 && (!single_link || info.links == 1),
            "Reparse points or writable hardlinks are not allowed"
        );
    }
    Ok(())
}

pub fn same_file(first: &File, second: &File) -> Result<bool> {
    #[cfg(windows)]
    {
        use std::os::windows::io::AsRawHandle;
        let mut a = FileInformation::default();
        let mut b = FileInformation::default();
        ensure!(
            unsafe { GetFileInformationByHandle(first.as_raw_handle(), &mut a) } != 0
                && unsafe { GetFileInformationByHandle(second.as_raw_handle(), &mut b) } != 0,
            "Cannot inspect archive file identity"
        );
        Ok(a.volume == b.volume && a.index_high == b.index_high && a.index_low == b.index_low)
    }
    #[cfg(not(windows))]
    {
        let _ = (first, second);
        Ok(false)
    }
}

pub fn executable_header(path: &Path) -> Result<()> {
    use std::io::{Read, Seek, SeekFrom};
    let mut file = open_regular(path)?;
    let mut dos = [0u8; 64];
    file.read_exact(&mut dos)?;
    ensure!(
        &dos[..2] == b"MZ",
        "Application is not a Windows executable"
    );
    let offset = u32::from_le_bytes(dos[60..64].try_into().unwrap()) as u64;
    ensure!(
        offset >= 64 && offset <= file.metadata()?.len().saturating_sub(26),
        "Invalid executable header offset"
    );
    file.seek(SeekFrom::Start(offset))?;
    let mut pe = [0u8; 26];
    file.read_exact(&mut pe)?;
    ensure!(
        &pe[..4] == b"PE\0\0"
            && u16::from_le_bytes(pe[4..6].try_into().unwrap()) == 0x8664
            && u16::from_le_bytes(pe[24..26].try_into().unwrap()) == 0x20b,
        "Application must be a Windows x64 executable"
    );
    Ok(())
}

#[cfg(windows)]
#[repr(C)]
#[derive(Default)]
struct FileTime {
    low: u32,
    high: u32,
}
#[cfg(windows)]
#[repr(C)]
#[derive(Default)]
struct FileInformation {
    attributes: u32,
    creation: FileTime,
    access: FileTime,
    write: FileTime,
    volume: u32,
    size_high: u32,
    size_low: u32,
    links: u32,
    index_high: u32,
    index_low: u32,
}

#[cfg(windows)]
#[link(name = "kernel32")]
unsafe extern "system" {
    fn OpenProcess(access: u32, inherit: i32, pid: u32) -> *mut std::ffi::c_void;
    fn CloseHandle(handle: *mut std::ffi::c_void) -> i32;
    fn GetProcessTimes(
        handle: *mut std::ffi::c_void,
        creation: *mut FileTime,
        exit: *mut FileTime,
        kernel: *mut FileTime,
        user: *mut FileTime,
    ) -> i32;
    fn QueryFullProcessImageNameW(
        handle: *mut std::ffi::c_void,
        flags: u32,
        buffer: *mut u16,
        count: *mut u32,
    ) -> i32;
    fn WaitForSingleObject(handle: *mut std::ffi::c_void, milliseconds: u32) -> u32;
    fn GetFileInformationByHandle(handle: *mut std::ffi::c_void, info: *mut FileInformation)
    -> i32;
    fn K32EnumProcesses(processes: *mut u32, bytes: u32, needed: *mut u32) -> i32;
}

pub fn assert_not_running(expected: &Path) -> Result<()> {
    #[cfg(windows)]
    {
        let mut ids = vec![0u32; 65536];
        let mut bytes = 0u32;
        ensure!(
            unsafe { K32EnumProcesses(ids.as_mut_ptr(), (ids.len() * 4) as u32, &mut bytes) } != 0
                && (bytes as usize) < ids.len() * 4,
            "Cannot confirm that Pixel Museum is closed"
        );
        for pid in &ids[..bytes as usize / 4] {
            let handle = unsafe { OpenProcess(0x1000, 0, *pid) };
            if handle.is_null() {
                continue;
            } // System processes need no access.
            let owner = Parent {
                handle: Some(handle),
            };
            let mut buffer = vec![0u16; 32768];
            let mut count = buffer.len() as u32;
            if unsafe { QueryFullProcessImageNameW(handle, 0, buffer.as_mut_ptr(), &mut count) }
                != 0
            {
                let actual =
                    std::path::PathBuf::from(String::from_utf16(&buffer[..count as usize])?);
                ensure!(
                    super::path_key(&actual) != super::path_key(expected),
                    "Close Pixel Museum before uninstalling it. The running application was left untouched."
                );
            }
            drop(owner);
        }
        Ok(())
    }
    #[cfg(not(windows))]
    {
        let _ = expected;
        anyhow::bail!("Windows uninstaller requires Windows")
    }
}

pub struct Parent {
    #[cfg(windows)]
    handle: Option<*mut std::ffi::c_void>,
}
impl Parent {
    pub fn open(pid: u32, creation: u64, expected: &Path) -> Result<Self> {
        ensure!(
            pid != 0 && pid != std::process::id() && creation != 0,
            "Invalid parent identity"
        );
        #[cfg(windows)]
        {
            let handle = unsafe { OpenProcess(0x0010_0000 | 0x1000, 0, pid) };
            if handle.is_null() {
                let error = std::io::Error::last_os_error();
                ensure!(
                    error.raw_os_error() == Some(87),
                    "Cannot inspect the parent process: {error}"
                );
                return Ok(Self { handle: None }); // The verified app already exited.
            }
            let parent = Self {
                handle: Some(handle),
            };
            let (mut started, mut ended, mut kernel, mut user) = (
                FileTime::default(),
                FileTime::default(),
                FileTime::default(),
                FileTime::default(),
            );
            ensure!(
                unsafe {
                    GetProcessTimes(handle, &mut started, &mut ended, &mut kernel, &mut user)
                } != 0,
                "Cannot read parent creation time"
            );
            ensure!(
                (u64::from(started.high) << 32 | u64::from(started.low)) == creation,
                "Parent PID was reused"
            );
            let mut buffer = vec![0u16; 32768];
            let mut count = buffer.len() as u32;
            ensure!(
                unsafe { QueryFullProcessImageNameW(handle, 0, buffer.as_mut_ptr(), &mut count) }
                    != 0,
                "Cannot identify parent executable"
            );
            let actual = std::path::PathBuf::from(String::from_utf16(&buffer[..count as usize])?);
            ensure!(
                super::path_key(&std::fs::canonicalize(actual)?)
                    == super::path_key(&std::fs::canonicalize(expected)?),
                "Parent process is not this installation's Pixel Museum.exe"
            );
            Ok(parent)
        }
        #[cfg(not(windows))]
        {
            let _ = (pid, creation, expected);
            anyhow::bail!("Windows update helper requires Windows");
        }
    }
    pub fn wait(&self, timeout: Duration) -> Result<()> {
        #[cfg(windows)]
        if let Some(handle) = self.handle {
            let code =
                unsafe { WaitForSingleObject(handle, timeout.as_millis().min(120_000) as u32) };
            ensure!(
                code == 0,
                "Pixel Museum did not exit within 120 seconds (wait result {code:#x})"
            );
        }
        Ok(())
    }
}
impl Drop for Parent {
    fn drop(&mut self) {
        #[cfg(windows)]
        if let Some(handle) = self.handle {
            unsafe {
                CloseHandle(handle);
            }
        }
    }
}

#[cfg(all(test, windows))]
mod tests {
    use super::*;
    use std::os::windows::{io::AsRawHandle, process::CommandExt};
    #[test]
    fn checks_real_parent_creation_path_and_bounded_wait() {
        let executable = std::path::PathBuf::from(std::env::var_os("SystemRoot").unwrap())
            .join("System32/WindowsPowerShell/v1.0/powershell.exe");
        let mut child = std::process::Command::new(&executable)
            .args([
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "Start-Sleep -Milliseconds 700",
            ])
            .creation_flags(0x0800_0000)
            .spawn()
            .unwrap();
        let (mut creation, mut exit, mut kernel, mut user) = (
            FileTime::default(),
            FileTime::default(),
            FileTime::default(),
            FileTime::default(),
        );
        assert_ne!(
            unsafe {
                GetProcessTimes(
                    child.as_raw_handle(),
                    &mut creation,
                    &mut exit,
                    &mut kernel,
                    &mut user,
                )
            },
            0
        );
        let started = u64::from(creation.high) << 32 | u64::from(creation.low);
        assert!(
            Parent::open(child.id(), started + 1, &executable)
                .unwrap_err_text()
                .contains("reused")
        );
        assert!(Parent::open(child.id(), started, &std::env::current_exe().unwrap()).is_err());
        let parent = Parent::open(child.id(), started, &executable).unwrap();
        assert!(parent.wait(Duration::from_millis(1)).is_err());
        parent.wait(Duration::from_secs(10)).unwrap();
        child.wait().unwrap();
        assert!(
            Parent::open(u32::MAX, 1, &executable)
                .unwrap()
                .wait(Duration::from_millis(1))
                .is_ok()
        );
    }
    trait ErrorText {
        fn unwrap_err_text(self) -> String;
    }
    impl ErrorText for Result<Parent> {
        fn unwrap_err_text(self) -> String {
            match self {
                Err(e) => format!("{e:#}"),
                Ok(_) => panic!("Parent identity mismatch accepted"),
            }
        }
    }
}
