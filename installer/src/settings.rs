use crate::manifest::ensure_no_links;
use anyhow::{Context, Result, ensure};
use serde_json::{Value, json};
use std::{fs, io::Write, path::Path};

#[derive(Clone, Debug)]
pub struct InitialSettings {
    pub width: u32,
    pub height: u32,
    pub fullscreen: bool,
    pub borderless: bool,
    pub vsync: bool,
    pub frame_limit: u32,
    pub master: f32,
    pub sfx: f32,
    pub ambient: f32,
    pub culture: f32,
    pub pad: f32,
    pub culture_on_pad: bool,
}

impl Default for InitialSettings {
    fn default() -> Self {
        let (width, height) = preferred_window_size();
        Self {
            width,
            height,
            fullscreen: false,
            borderless: false,
            vsync: true,
            frame_limit: 60,
            master: 1.0,
            sfx: 1.0,
            ambient: 0.48,
            culture: 1.0,
            pad: 1.0,
            culture_on_pad: false,
        }
    }
}

impl InitialSettings {
    pub fn load(root: &Path) -> Result<Self> {
        let mut value = Self::default();
        let prefs = read_object(&root.join("preferences.json"), 1024 * 1024)?;
        let video = read_object(&root.join("video-settings.json"), 16 * 1024)?;
        value.master = level(&prefs, "master_volume", 1.0);
        value.sfx = level(&prefs, "sfx_volume", 1.0);
        value.ambient = level(&prefs, "music_volume", level(&prefs, "volume", 0.48));
        value.culture = level(&prefs, "culture_volume", 1.0);
        value.pad = level(&prefs, "pad_volume", 1.0);
        value.culture_on_pad = prefs["culture_audio_on_pad"].as_bool().unwrap_or(false);
        value.width = video["width"]
            .as_u64()
            .map(|v| v.clamp(960, 7680) as u32)
            .unwrap_or(value.width);
        value.height = video["height"]
            .as_u64()
            .map(|v| v.clamp(540, 4320) as u32)
            .unwrap_or(value.height);
        value.fullscreen = video["fullscreen"].as_bool().unwrap_or(false);
        value.borderless = value.fullscreen && video["borderless"].as_bool().unwrap_or(false);
        value.vsync = video["vsync"].as_bool().unwrap_or(true);
        value.frame_limit = video["frame_limit"]
            .as_u64()
            .map(|v| v.min(360) as u32)
            .unwrap_or(60);
        Ok(value)
    }

    pub fn save(&self, root: &Path) -> Result<()> {
        ensure!(
            root.is_absolute() && root.is_dir() && root.join("pixel-museum-install.json").is_file(),
            "Settings can only be saved into a completed Pixel Museum installation"
        );
        ensure_no_links(root)?;
        ensure!(
            (960..=7680).contains(&self.width)
                && (540..=4320).contains(&self.height)
                && self.frame_limit <= 360,
            "Invalid initial video settings"
        );
        for level in [self.master, self.sfx, self.ambient, self.culture, self.pad] {
            ensure!(
                level.is_finite() && (0.0..=1.0).contains(&level),
                "Invalid initial audio setting"
            );
        }
        let prefs_path = root.join("preferences.json");
        let video_path = root.join("video-settings.json");
        let mut prefs = read_object(&prefs_path, 1024 * 1024)?;
        let mut video = read_object(&video_path, 16 * 1024)?;
        prefs["master_volume"] = json!(self.master);
        prefs["sfx_volume"] = json!(self.sfx);
        prefs["music_volume"] = json!(self.ambient);
        prefs["volume"] = json!(self.ambient);
        prefs["culture_volume"] = json!(self.culture);
        prefs["pad_volume"] = json!(self.pad);
        prefs["culture_audio_on_pad"] = json!(self.culture_on_pad);
        video["width"] = json!(self.width);
        video["height"] = json!(self.height);
        video["fullscreen"] = json!(self.fullscreen);
        video["borderless"] = json!(self.fullscreen && self.borderless);
        video["vsync"] = json!(self.vsync);
        video["frame_limit"] = json!(self.frame_limit);
        // Fully serialise both objects before replacing either file. Existing
        // language, onboarding and other preferences are preserved verbatim.
        let prefs_bytes = serde_json::to_vec_pretty(&prefs)?;
        let video_bytes = serde_json::to_vec_pretty(&video)?;
        write_atomic(&video_path, &video_bytes)?;
        write_atomic(&prefs_path, &prefs_bytes)?;
        Ok(())
    }
}

fn level(object: &Value, key: &str, fallback: f32) -> f32 {
    object[key]
        .as_f64()
        .filter(|n| n.is_finite())
        .map(|n| n.clamp(0.0, 1.0) as f32)
        .unwrap_or(fallback)
}

fn read_object(path: &Path, limit: u64) -> Result<Value> {
    ensure_no_links(path)?;
    if !path.exists() {
        return Ok(json!({}));
    }
    ensure!(
        fs::metadata(path)?.len() <= limit,
        "Preference file is too large: {}",
        path.display()
    );
    let value: Value = serde_json::from_slice(&fs::read(path)?)
        .with_context(|| format!("Cannot read preferences from {}", path.display()))?;
    ensure!(
        value.is_object(),
        "Preferences must contain an object: {}",
        path.display()
    );
    Ok(value)
}

fn write_atomic(path: &Path, bytes: &[u8]) -> Result<()> {
    ensure_no_links(path)?;
    let mut staged =
        tempfile::NamedTempFile::new_in(path.parent().context("Preference file has no parent")?)?;
    staged.write_all(bytes)?;
    staged.as_file().sync_all()?;
    staged
        .persist(path)
        .with_context(|| format!("Cannot save {}", path.display()))?;
    Ok(())
}

pub fn preferred_window_size() -> (u32, u32) {
    #[cfg(windows)]
    {
        #[repr(C)]
        #[derive(Default)]
        struct Rect {
            left: i32,
            top: i32,
            right: i32,
            bottom: i32,
        }
        #[link(name = "user32")]
        unsafe extern "system" {
            fn SystemParametersInfoW(
                action: u32,
                parameter: u32,
                data: *mut std::ffi::c_void,
                flags: u32,
            ) -> i32;
        }
        let mut area = Rect::default();
        // SPI_GETWORKAREA mirrors SDL_GetDisplayUsableBounds for the primary display.
        if unsafe { SystemParametersInfoW(0x0030, 0, (&mut area as *mut Rect).cast(), 0) } != 0 {
            return (
                (area.right - area.left - 120).clamp(960, 1600) as u32,
                (area.bottom - area.top - 120).clamp(540, 900) as u32,
            );
        }
    }
    (1600, 900)
}

pub fn desktop_size() -> Option<(u32, u32)> {
    #[cfg(windows)]
    {
        #[link(name = "user32")]
        unsafe extern "system" {
            fn GetSystemMetrics(index: i32) -> i32;
        }
        let width = unsafe { GetSystemMetrics(0) };
        let height = unsafe { GetSystemMetrics(1) };
        if width > 0 && height > 0 {
            return Some((width as u32, height as u32));
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn finish_writes_real_settings_and_preserves_language_appearance_and_onboarding() {
        let root = tempfile::tempdir().unwrap();
        fs::write(root.path().join("pixel-museum-install.json"), "{}").unwrap();
        fs::write(root.path().join("preferences.json"), r#"{"language":"it","language_chosen":true,"dark_theme":true,"theme_chosen":false,"onboarding_complete":false,"exhibit":"keep"}"#).unwrap();
        let mut settings = InitialSettings::load(root.path()).unwrap();
        assert_eq!(settings.ambient, 0.48);
        settings.width = 2560;
        settings.height = 1440;
        settings.fullscreen = true;
        settings.frame_limit = 120;
        settings.master = 0.7;
        settings.culture_on_pad = true;
        settings.save(root.path()).unwrap();
        let prefs = read_object(&root.path().join("preferences.json"), 1024 * 1024).unwrap();
        assert_eq!(prefs["language"], "it");
        assert_eq!(prefs["language_chosen"], true);
        assert_eq!(prefs["onboarding_complete"], false);
        assert_eq!(prefs["exhibit"], "keep");
        assert_eq!(prefs["dark_theme"], true);
        assert_eq!(prefs["theme_chosen"], false);
        assert_eq!(prefs["culture_audio_on_pad"], true);
        let video = read_object(&root.path().join("video-settings.json"), 16384).unwrap();
        assert_eq!(video["width"], 2560);
        assert_eq!(video["height"], 1440);
        assert_eq!(video["frame_limit"], 120);
        for (fullscreen, borderless) in [(true, false), (true, true), (false, false)] {
            settings.fullscreen = fullscreen;
            settings.borderless = borderless;
            settings.save(root.path()).unwrap();
            let saved = read_object(&root.path().join("video-settings.json"), 16384).unwrap();
            assert_eq!(saved["fullscreen"], fullscreen);
            assert_eq!(saved["borderless"], borderless);
            let loaded = InitialSettings::load(root.path()).unwrap();
            assert_eq!(
                (loaded.fullscreen, loaded.borderless),
                (fullscreen, borderless)
            );
            assert_eq!((loaded.width, loaded.height), (2560, 1440));
        }
        assert!(
            InitialSettings::default()
                .save(Path::new("relative"))
                .is_err()
        );
    }

    #[test]
    fn finish_leaves_new_install_appearance_to_app_defaults() {
        let root = tempfile::tempdir().unwrap();
        fs::write(root.path().join("pixel-museum-install.json"), "{}").unwrap();
        fs::write(
            root.path().join("preferences.json"),
            r#"{"language":"it","language_chosen":true}"#,
        )
        .unwrap();
        InitialSettings::load(root.path())
            .unwrap()
            .save(root.path())
            .unwrap();
        let prefs = read_object(&root.path().join("preferences.json"), 1024 * 1024).unwrap();
        assert!(prefs.get("dark_theme").is_none());
        assert!(prefs.get("theme_chosen").is_none());
        assert_eq!(prefs["language"], "it");
        assert_eq!(prefs["language_chosen"], true);
    }
    #[test]
    fn finish_does_not_choose_app_language_on_a_new_install() {
        let root = tempfile::tempdir().unwrap();
        fs::write(root.path().join("pixel-museum-install.json"), "{}").unwrap();
        InitialSettings::default().save(root.path()).unwrap();
        let prefs = read_object(&root.path().join("preferences.json"), 1024 * 1024).unwrap();
        assert!(prefs.get("language").is_none());
        assert!(prefs.get("language_chosen").is_none());
        assert!(prefs.get("onboarding_complete").is_none());
    }
}
