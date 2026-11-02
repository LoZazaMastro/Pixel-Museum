use std::{env, fs, path::PathBuf};

fn main() {
    for key in [
        "PIXEL_MUSEUM_MANIFEST_URL",
        "PIXEL_MUSEUM_MANIFEST_SHA256",
        "PIXEL_MUSEUM_MANIFEST_PATH",
    ] {
        println!("cargo:rerun-if-env-changed={key}");
    }
    println!("cargo:rerun-if-changed=build.rs");
    let embedded = PathBuf::from(env::var_os("OUT_DIR").unwrap()).join("release-manifest.json");
    if let Some(path) = env::var_os("PIXEL_MUSEUM_MANIFEST_PATH") {
        println!("cargo:rerun-if-changed={}", PathBuf::from(&path).display());
        fs::copy(path, embedded).expect("embed release manifest");
    } else {
        fs::write(embedded, []).expect("write empty release manifest");
    }
    if env::var("CARGO_CFG_TARGET_OS").as_deref() != Ok("windows") {
        return;
    }
    // Native ICO constructed from the same pixel grid as website/assets/mark.svg.
    let mut ico = vec![0, 0, 1, 0, 1, 0, 32, 32, 0, 0, 1, 0, 32, 0];
    ico.extend_from_slice(&(40u32 + 32 * 32 * 4 + 32 * 4).to_le_bytes());
    ico.extend_from_slice(&22u32.to_le_bytes());
    ico.extend_from_slice(&40u32.to_le_bytes());
    ico.extend_from_slice(&32i32.to_le_bytes());
    ico.extend_from_slice(&64i32.to_le_bytes());
    ico.extend_from_slice(&1u16.to_le_bytes());
    ico.extend_from_slice(&32u16.to_le_bytes());
    ico.extend_from_slice(&[0; 24]);
    for y in (0..32).rev() {
        for x in 0..32 {
            let cx = x * 7 / 32;
            let cy = y * 7 / 32;
            let ink = (cx == 1 || cx == 5) && (1..=5).contains(&cy)
                || cy == 2 && (cx == 2 || cx == 4)
                || cy == 3 && cx == 3;
            ico.extend_from_slice(if ink {
                &[33, 37, 32, 255]
            } else {
                &[235, 242, 244, 255]
            });
        }
    }
    ico.extend_from_slice(&[0; 128]);
    let icon = PathBuf::from(env::var_os("OUT_DIR").unwrap()).join("pixel-museum.ico");
    fs::write(&icon, ico).expect("write installer icon");
    let mut resource = winresource::WindowsResource::new();
    resource
        .set_icon(icon.to_str().expect("icon path"))
        .set("ProductName", "Pixel Museum")
        .set("FileDescription", "Pixel Museum Setup")
        .set("LegalCopyright", "Andrea Sgarro / LoZazaMastro")
        .set_manifest(r#"<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0"><trustInfo xmlns="urn:schemas-microsoft-com:asm.v3"><security><requestedPrivileges><requestedExecutionLevel level="asInvoker" uiAccess="false"/></requestedPrivileges></security></trustInfo><application xmlns="urn:schemas-microsoft-com:asm.v3"><windowsSettings><longPathAware xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">true</longPathAware></windowsSettings></application></assembly>"#);
    resource
        .compile()
        .expect("compile Windows installer resources");
}
