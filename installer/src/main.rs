#![cfg_attr(all(windows, not(debug_assertions)), windows_subsystem = "windows")]

mod engine;
mod database;
mod integration;
mod locale;
mod manifest;
mod settings;
mod ui;
mod uninstall;
mod update;

use anyhow::{Context, Result, bail, ensure};
use std::{
    path::PathBuf,
    sync::{Arc, atomic::AtomicBool},
};

#[derive(Clone, Default)]
pub struct Options {
    pub manifest: Option<String>,
    pub manifest_sha256: Option<String>,
    pub payload_dir: Option<PathBuf>,
    pub install_dir: Option<PathBuf>,
    pub language: Option<String>,
    pub headless: bool,
    pub accept_license: bool,
    pub validate: bool,
    pub desktop_shortcut: bool,
    pub portable: bool,
    pub uninstall_root: Option<PathBuf>,
    pub quiet: bool,
    pub remove_personal_data: bool,
}

fn options() -> Result<Options> {
    let mut opts = Options::default();
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--manifest" => {
                opts.manifest = Some(
                    args.next()
                        .context("--manifest needs a path or HTTPS URL")?,
                )
            }
            "--manifest-sha256" => {
                opts.manifest_sha256 =
                    Some(args.next().context("--manifest-sha256 needs a digest")?)
            }
            "--payload-dir" => {
                opts.payload_dir = Some(args.next().context("--payload-dir needs a path")?.into())
            }
            "--install-dir" => {
                opts.install_dir = Some(args.next().context("--install-dir needs a path")?.into())
            }
            "--language" => {
                opts.language = Some(
                    args.next()
                        .context("--language needs en, it, fr, de or es")?,
                )
            }
            "--headless" => opts.headless = true,
            "--accept-license" => opts.accept_license = true,
            "--validate-manifest" => opts.validate = true,
            "--desktop-shortcut" => opts.desktop_shortcut = true,
            "--portable" => opts.portable = true,
            "--uninstall" => {
                opts.uninstall_root = Some(
                    args.next()
                        .context("--uninstall needs an absolute installation folder")?
                        .into(),
                )
            }
            "--quiet" => opts.quiet = true,
            "--remove-personal-data" => opts.remove_personal_data = true,
            "--help" | "-h" => {
                println!(
                    "Pixel Museum Setup\n\n--manifest <file.json|https://github.com/.../releases/download/.../manifest.json>\n--manifest-sha256 <digest>  Required for remote manifests\n--payload-dir <folder>     Prefer locally supplied packages\n--install-dir <folder>     Application and collection destination\n--language <en|it|fr|de|es>  Installer language only\n--desktop-shortcut        Also create a desktop shortcut\n--headless --accept-license  Install without the graphical wizard\n--portable                Headless installation without Windows registration\n--validate-manifest        Validate without installing\n--uninstall <folder>      Remove the installed application; keep personal data\n\nLicence: GPL-3.0-or-later for code. External media retain their own terms."
                );
                std::process::exit(0);
            }
            _ => bail!("Unknown argument: {arg}"),
        }
    }
    if let Some(lang) = &opts.language {
        ensure!(
            ["en", "it", "fr", "de", "es"].contains(&lang.as_str()),
            "Unsupported language"
        );
    }
    ensure!(
        !opts.portable || opts.headless,
        "--portable is only available with --headless"
    );
    if opts.uninstall_root.is_some() {
        ensure!(
            !opts.headless
                && !opts.validate
                && opts.manifest.is_none()
                && opts.install_dir.is_none()
                && !opts.portable,
            "Uninstall cannot be combined with installation options"
        );
    } else {
        ensure!(!opts.quiet, "Uninstall options require --uninstall");
    }
    ensure!(
        !opts.remove_personal_data || opts.uninstall_root.is_some(),
        "--remove-personal-data requires --uninstall"
    );
    Ok(opts)
}

fn run() -> Result<()> {
    let _ = rustls::crypto::ring::default_provider().install_default();
    let mut opts = options()?;
    if let Some(root) = &opts.uninstall_root {
        let installation = uninstall::inspect(root)?;
        if opts.language.is_none() {
            opts.language = Some(installation.language);
        }
        if opts.quiet {
            uninstall::remove_with_policy(root, opts.remove_personal_data)?;
            return Ok(());
        }
    }
    if opts.headless || opts.validate {
        let cancelled = Arc::new(AtomicBool::new(false));
        let release = engine::load_release(&opts, &cancelled)?;
        if opts.validate {
            println!(
                "Valid release {}: {} packages; {} download bytes; {} installed bytes",
                release.manifest.version,
                release.manifest.packages.len(),
                release.manifest.download_bytes()?,
                release.manifest.unpacked_bytes()?
            );
            return Ok(());
        }
        ensure!(
            opts.accept_license,
            "Installation requires --accept-license. Read LICENSE and THIRD_PARTY_NOTICES.md before accepting."
        );
        let destination = opts
            .install_dir
            .as_ref()
            .context("--headless requires --install-dir")?;
        if !opts.portable {
            // Match the graphical wizard: an existing managed installation is
            // updated transactionally, without reinstalling the collection.
            if destination.join("application-files.json").is_file() {
                return engine::upgrade_registered(
                    &release,
                    destination,
                    opts.language.as_deref().unwrap_or("en"),
                    &engine::InstallControl::default(),
                    |event| {
                        println!(
                            "{:?} {} {}/{}",
                            event.phase, event.package, event.done, event.total
                        )
                    },
                );
            }
            return engine::install_registered(
                &release,
                destination,
                opts.language.as_deref().unwrap_or("en"),
                opts.desktop_shortcut,
                &engine::InstallControl::default(),
                |event| {
                    println!(
                        "{:?} {} {}/{}",
                        event.phase, event.package, event.done, event.total
                    )
                },
            );
        }
        engine::install(
            &release,
            destination,
            opts.language.as_deref().unwrap_or("en"),
            &cancelled,
            |event| {
                println!(
                    "{:?} {} {}/{}",
                    event.phase, event.package, event.done, event.total
                );
            },
        )?;
        return Ok(());
    }
    ui::run(opts).map_err(|e| anyhow::anyhow!("Cannot start the installer: {e}"))
}

fn main() {
    let arguments: Vec<_> = std::env::args_os().collect();
    if arguments.iter().skip(1).any(|arg| arg == "--apply-update") {
        let result = if arguments.len() == 3 && arguments[1] == "--apply-update" {
            update::run_descriptor(std::path::Path::new(&arguments[2]))
        } else {
            Err(anyhow::anyhow!(
                "Usage: --apply-update <absolute descriptor.json>"
            ))
        };
        if let Err(error) = result {
            eprintln!("{error:#}");
            std::process::exit(1);
        }
        return;
    }
    if let Err(error) = run() {
        eprintln!("{error:#}");
        #[cfg(windows)]
        if !std::env::args()
            .any(|s| s == "--headless" || s == "--validate-manifest" || s == "--quiet")
        {
            let language = arguments
                .windows(2)
                .find(|pair| pair[0] == "--language")
                .and_then(|pair| pair[1].to_str())
                .map(locale::Language::from_code)
                .unwrap_or_else(locale::Language::detect);
            let uninstall = arguments.iter().any(|arg| arg == "--uninstall");
            rfd::MessageDialog::new()
                .set_title(language.text(if uninstall {
                    locale::Text::UninstallTitle
                } else {
                    locale::Text::SetupTitle
                }))
                .set_description(format!(
                    "{}\n\n{error:#}",
                    language.text(if uninstall {
                        locale::Text::UninstallFailed
                    } else {
                        locale::Text::FailedTitle
                    })
                ))
                .set_level(rfd::MessageLevel::Error)
                .show();
        }
        std::process::exit(1);
    }
}
