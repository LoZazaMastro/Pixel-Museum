use crate::{
    Options,
    engine::{self, InstallControl, Phase, Progress, Release},
    locale::{Language, Text},
    settings::InitialSettings,
};
use eframe::egui::{
    self, Align, Color32, FontData, FontDefinitions, FontFamily, FontId, RichText, Stroke, Vec2,
};
use std::{
    path::PathBuf,
    sync::{Arc, atomic::Ordering, mpsc},
    time::Duration,
};

#[derive(Clone, Copy)]
struct Palette {
    paper: Color32,
    ink: Color32,
    surface: Color32,
    selection: Color32,
    muted: Color32,
    rule: Color32,
}
impl Palette {
    const fn light() -> Self {
        Self {
            paper: Color32::from_rgb(244, 242, 235),
            ink: Color32::from_rgb(32, 33, 32),
            surface: Color32::WHITE,
            selection: Color32::from_rgb(231, 230, 224),
            muted: Color32::from_rgb(110, 110, 106),
            rule: Color32::from_rgb(218, 217, 211),
        }
    }
    const fn dark() -> Self {
        Self {
            paper: Color32::from_rgb(27, 28, 26),
            ink: Color32::from_rgb(244, 242, 235),
            surface: Color32::from_rgb(35, 36, 33),
            selection: Color32::from_rgb(54, 55, 51),
            muted: Color32::from_rgb(172, 172, 164),
            rule: Color32::from_rgb(69, 70, 64),
        }
    }
}
thread_local! {static COLORS:std::cell::Cell<Palette>=const{std::cell::Cell::new(Palette::light())};}
fn paper() -> Color32 {
    COLORS.with(|c| c.get().paper)
}
fn ink() -> Color32 {
    COLORS.with(|c| c.get().ink)
}
fn surface() -> Color32 {
    COLORS.with(|c| c.get().surface)
}
fn selection() -> Color32 {
    COLORS.with(|c| c.get().selection)
}
fn muted() -> Color32 {
    COLORS.with(|c| c.get().muted)
}
fn rule() -> Color32 {
    COLORS.with(|c| c.get().rule)
}

#[derive(Clone, Copy, PartialEq)]
enum Page {
    Welcome,
    Licence,
    Destination,
    Installing,
    Finished,
    Failed,
    Uninstall,
    Uninstalling,
    Uninstalled,
    UninstallFailed,
}
enum Message {
    Loaded(Result<Release, String>),
    Progress(Progress),
    Done(Result<(), String>),
    Uninstalled(Result<crate::uninstall::Outcome, String>),
}

struct Setup {
    opts: Options,
    language: Language,
    page: Page,
    accepted: bool,
    desktop_shortcut: bool,
    legal_document: String,
    legal_lines: Vec<String>,
    legal_columns: usize,
    initial_settings: InitialSettings,
    installer_dark: bool,
    manual_theme: bool,
    destination: String,
    installed_version: Option<String>,
    upgrading: bool,
    release: Option<Release>,
    loading: bool,
    error: Option<String>,
    progress: Option<Progress>,
    control: Arc<InstallControl>,
    tx: mpsc::Sender<Message>,
    rx: mpsc::Receiver<Message>,
    closing: bool,
    was_cancelled: bool,
    remove_personal_data: bool,
    #[cfg(feature = "preview")]
    preview_captured: bool,
}

pub fn run(opts: Options) -> eframe::Result {
    #[cfg(feature = "preview")]
    let initial_height = if std::env::var_os("PIXEL_MUSEUM_SETUP_PREVIEW_AUDIO_OPEN").is_some() {
        760.0
    } else {
        660.0
    };
    #[cfg(not(feature = "preview"))]
    let initial_height = 660.0;
    let language = opts
        .language
        .as_deref()
        .map(Language::from_code)
        .unwrap_or_else(Language::detect);
    let window_title = language.text(if opts.uninstall_root.is_some() {
        Text::UninstallTitle
    } else {
        Text::SetupTitle
    });
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title(window_title)
            .with_app_id("PixelMuseum.Setup")
            .with_inner_size([1000.0, initial_height])
            .with_min_inner_size([920.0, 620.0])
            .with_decorations(false)
            .with_resizable(true)
            .with_visible(
                !(cfg!(feature = "preview")
                    && std::env::var_os("PIXEL_MUSEUM_SETUP_SCREENSHOT").is_some()),
            )
            .with_icon(icon()),
        renderer: eframe::Renderer::Glow,
        centered: true,
        ..Default::default()
    };
    eframe::run_native(
        "Pixel Museum Setup",
        options,
        Box::new(move |cc| Ok(Box::new(Setup::new(cc, opts)))),
    )
}

fn icon() -> egui::IconData {
    let mut rgba = Vec::with_capacity(112 * 112 * 4);
    for y in 0..112 {
        for x in 0..112 {
            let cx = x / 16;
            let cy = y / 16;
            let ink = (cx == 1 || cx == 5) && (1..=5).contains(&cy)
                || cy == 2 && (cx == 2 || cx == 4)
                || cy == 3 && cx == 3;
            rgba.extend_from_slice(if ink {
                &[32, 37, 33, 255]
            } else {
                &[244, 242, 235, 255]
            });
        }
    }
    egui::IconData {
        rgba,
        width: 112,
        height: 112,
    }
}

fn legal_document(language: Language) -> String {
    format!(
        "{}\n\n{}\n\n{}\n\n{}\n\n{}\n\n{}\n\n{}",
        engine::LICENSE,
        language.text(Text::LegalCollection),
        engine::NOTICES,
        language.text(Text::LegalFont),
        engine::FONT_LICENCE,
        language.text(Text::LegalInstaller),
        engine::SOFTWARE_LICENCES
    )
}

impl Setup {
    fn new(cc: &eframe::CreationContext<'_>, opts: Options) -> Self {
        configure(&cc.egui_ctx);
        let language = opts
            .language
            .as_deref()
            .map(Language::from_code)
            .unwrap_or_else(Language::detect);
        let destination = opts
            .uninstall_root
            .clone()
            .or_else(|| opts.install_dir.clone())
            .or_else(crate::integration::installed_destination)
            .unwrap_or_else(engine::default_destination)
            .to_string_lossy()
            .into_owned();
        let (tx, rx) = mpsc::channel();
        let uninstall = opts.uninstall_root.is_some();
        let installed_version = if uninstall {
            None
        } else {
            crate::uninstall::inspect(std::path::Path::new(&destination))
                .ok()
                .map(|installation| installation.inventory.version)
        };
        let desktop_shortcut = opts.desktop_shortcut;
        let remove_personal_data = opts.remove_personal_data;
        let mut result = Self {
            opts,
            language,
            page: if uninstall {
                Page::Uninstall
            } else {
                Page::Welcome
            },
            accepted: false,
            desktop_shortcut,
            legal_document: legal_document(language),
            legal_lines: Vec::new(),
            legal_columns: 0,
            initial_settings: InitialSettings::default(),
            installer_dark: cc.egui_ctx.system_theme() == Some(egui::Theme::Dark),
            manual_theme: false,
            destination,
            installed_version,
            upgrading: false,
            release: None,
            loading: false,
            error: None,
            progress: None,
            control: Arc::new(InstallControl::default()),
            tx,
            rx,
            closing: false,
            was_cancelled: false,
            remove_personal_data,
            #[cfg(feature = "preview")]
            preview_captured: false,
        };
        #[cfg(feature = "preview")]
        if let Ok(page) = std::env::var("PIXEL_MUSEUM_SETUP_PREVIEW_PAGE") {
            result.page = match page.as_str() {
                "licence" => Page::Licence,
                "destination" => Page::Destination,
                "installing" => Page::Installing,
                "finished" => Page::Finished,
                "uninstall" => Page::Uninstall,
                "uninstalled" => Page::Uninstalled,
                _ => Page::Welcome,
            };
        }
        #[cfg(feature = "preview")]
        if let Ok(mode) = std::env::var("PIXEL_MUSEUM_SETUP_PREVIEW_DISPLAY_MODE") {
            result.initial_settings.fullscreen = mode == "fullscreen" || mode == "borderless";
            result.initial_settings.borderless = mode == "borderless";
        }
        #[cfg(feature = "preview")]
        if let Ok(theme) = std::env::var("PIXEL_MUSEUM_SETUP_PREVIEW_THEME") {
            result.installer_dark = theme == "dark";
            result.manual_theme = true;
            cc.egui_ctx.set_theme(if result.installer_dark {
                egui::Theme::Dark
            } else {
                egui::Theme::Light
            });
            apply_theme(&cc.egui_ctx, result.installer_dark);
        }
        #[cfg(feature = "preview")]
        if std::env::var_os("PIXEL_MUSEUM_SETUP_PREVIEW_ACCEPTED").is_some() {
            result.accepted = true;
        }
        if !result.read_only_preview() && !uninstall {
            result.load(cc.egui_ctx.clone());
        }
        result
    }

    fn read_only_preview(&self) -> bool {
        #[cfg(feature = "preview")]
        {
            std::env::var_os("PIXEL_MUSEUM_SETUP_PREVIEW_READONLY").is_some()
        }
        #[cfg(not(feature = "preview"))]
        {
            false
        }
    }

    fn text(&self, key: Text) -> &'static str {
        self.language.text(key)
    }

    fn load(&mut self, ctx: egui::Context) {
        self.loading = true;
        self.error = None;
        self.release = None;
        let opts = self.opts.clone();
        let tx = self.tx.clone();
        let control = self.control.clone();
        std::thread::spawn(move || {
            let result =
                engine::load_release(&opts, control.cancel_token()).map_err(|e| format!("{e:#}"));
            let _ = tx.send(Message::Loaded(result));
            ctx.request_repaint();
        });
    }

    fn refresh_installed_version(&mut self) {
        self.installed_version =
            crate::uninstall::inspect(std::path::Path::new(self.destination.trim()))
                .ok()
                .map(|installation| installation.inventory.version);
    }

    fn can_upgrade(&self) -> bool {
        self.installed_version
            .as_deref()
            .zip(self.release.as_ref())
            .is_some_and(|(old, release)| {
                crate::update::version_is_newer(old, &release.manifest.version)
            })
    }

    fn start(&mut self, ctx: egui::Context) {
        if self.read_only_preview() {
            return;
        }
        if !self.accepted {
            return;
        }
        let Some(release) = self.release.clone() else {
            return;
        };
        let path = PathBuf::from(self.destination.trim());
        let upgrade = self.can_upgrade();
        if self.installed_version.is_some() && !upgrade {
            return;
        }
        if !upgrade {
            if let Err(error) = engine::validate_destination(&path) {
                self.error = Some(format!("{error:#}"));
                return;
            }
        }
        self.upgrading = upgrade;
        self.control = Arc::new(InstallControl::default());
        self.page = Page::Installing;
        self.error = None;
        self.progress = None;
        self.was_cancelled = false;
        let control = self.control.clone();
        let tx = self.tx.clone();
        let language = self.language.code();
        let desktop_shortcut = self.desktop_shortcut;
        std::thread::spawn(move || {
            let progress = |progress| {
                let _ = tx.send(Message::Progress(progress));
                ctx.request_repaint();
            };
            let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                if upgrade {
                    engine::upgrade_registered(&release, &path, language, &control, progress)
                } else {
                    engine::install_registered(
                        &release,
                        &path,
                        language,
                        desktop_shortcut,
                        &control,
                        progress,
                    )
                }
                .map_err(|e| format!("{e:#}"))
            }))
            .unwrap_or_else(|_| {
                Err(Language::from_code(language)
                    .text(Text::WorkerFailed)
                    .into())
            });
            let _ = tx.send(Message::Done(result));
            ctx.request_repaint();
        });
    }

    fn read_messages(&mut self, ctx: &egui::Context) {
        while let Ok(message) = self.rx.try_recv() {
            match message {
                Message::Loaded(result) => {
                    self.loading = false;
                    match result {
                        Ok(release) => {
                            self.release = Some(release);
                            self.error = None;
                        }
                        Err(error) => self.error = Some(error),
                    }
                }
                Message::Progress(progress) => self.progress = Some(progress),
                Message::Done(mut result) => {
                    if result.is_ok() {
                        result = crate::integration::verify_completed_install(
                            std::path::Path::new(self.destination.trim()),
                        )
                        .map_err(|e| format!("{}\n\n{e:#}", self.text(Text::RegistrationFailed)));
                    }
                    match result {
                        Ok(()) => {
                            self.page = Page::Finished;
                            if !self.upgrading {
                                match InitialSettings::load(std::path::Path::new(
                                    self.destination.trim(),
                                )) {
                                    Ok(settings) => self.initial_settings = settings,
                                    Err(error) => self.error = Some(format!("{error:#}")),
                                }
                            }
                        }
                        Err(error) => {
                            self.was_cancelled =
                                self.control.cancel_token().load(Ordering::Relaxed);
                            self.error = Some(error);
                            self.page = Page::Failed;
                        }
                    }
                    if self.closing {
                        ctx.send_viewport_cmd(egui::ViewportCommand::Close);
                    }
                }
                Message::Uninstalled(result) => {
                    match result {
                        Ok(outcome) => {
                            self.page = Page::Uninstalled;
                            let mut details = outcome.cleanup_warning.unwrap_or_default();
                            if !outcome.retained_modified_files.is_empty() {
                                if !details.is_empty() {
                                    details.push('\n');
                                }
                                details.push_str(self.text(Text::RetainedModified));
                                details.push('\n');
                                details.push_str(&outcome.retained_modified_files.join("\n"));
                            }
                            self.error = if details.is_empty() {
                                None
                            } else {
                                Some(details)
                            };
                        }
                        Err(error) => {
                            self.page = Page::UninstallFailed;
                            self.error = Some(error);
                        }
                    }
                    if self.closing {
                        ctx.send_viewport_cmd(egui::ViewportCommand::Close);
                    }
                }
            }
        }
    }

    fn start_uninstall(&mut self, ctx: egui::Context) {
        if self.read_only_preview() {
            return;
        }
        let Some(root) = self.opts.uninstall_root.clone() else {
            return;
        };
        self.page = Page::Uninstalling;
        self.error = None;
        let tx = self.tx.clone();
        let remove_personal_data = self.remove_personal_data;
        std::thread::spawn(move || {
            let result = crate::uninstall::remove_with_policy(&root, remove_personal_data)
                .map_err(|e| format!("{e:#}"));
            let _ = tx.send(Message::Uninstalled(result));
            ctx.request_repaint();
        });
    }

    fn titlebar(&mut self, root: &mut egui::Ui, ctx: &egui::Context) {
        egui::Panel::top("museum-titlebar")
            .exact_size(46.0)
            .resizable(false)
            .frame(egui::Frame::new().fill(paper()).inner_margin(0))
            .show(root, |ui| {
                let (bar, _) = ui.allocate_exact_size(
                    egui::vec2(ui.available_width(), 46.0),
                    egui::Sense::hover(),
                );
                paint_brand(ui, egui::pos2(bar.left() + 12.0, bar.center().y));
                ui.painter().line_segment(
                    [bar.left_bottom(), bar.right_bottom()],
                    Stroke::new(1.0, rule()),
                );
                let maximized = ctx.input(|i| i.viewport().maximized.unwrap_or(false));
                let drag = egui::Rect::from_min_max(
                    bar.min + egui::vec2(4.0, 4.0),
                    egui::pos2(bar.right() - 184.0, bar.bottom()),
                );
                let response = ui.interact(
                    drag,
                    ui.scope_id().with("window-drag"),
                    egui::Sense::click_and_drag(),
                );
                if response.double_clicked() {
                    ctx.send_viewport_cmd(egui::ViewportCommand::Maximized(!maximized));
                } else if response.drag_started() {
                    ctx.send_viewport_cmd(egui::ViewportCommand::StartDrag);
                }
                let theme_rect = egui::Rect::from_min_size(
                    egui::pos2(bar.right() - 184.0, bar.top()),
                    egui::vec2(46.0, 46.0),
                );
                let theme_tip = self.text(if self.installer_dark {
                    Text::Light
                } else {
                    Text::Dark
                });
                let theme = ui
                    .put(
                        theme_rect,
                        egui::Button::new("")
                            .fill(Color32::TRANSPARENT)
                            .stroke(Stroke::NONE)
                            .corner_radius(0),
                    )
                    .on_hover_text(theme_tip);
                theme
                    .widget_info(|| egui::WidgetInfo::labeled(egui::Role::Button, true, theme_tip));
                if theme.hovered() {
                    ui.painter().rect_filled(theme_rect, 0, selection());
                }
                paint_theme_icon(ui, theme_rect.center(), self.installer_dark);
                if theme.clicked() {
                    self.installer_dark = !self.installer_dark;
                    self.manual_theme = true;
                    ctx.set_theme(if self.installer_dark {
                        egui::Theme::Dark
                    } else {
                        egui::Theme::Light
                    });
                    apply_theme(ctx, self.installer_dark);
                }
                for n in 0..3 {
                    let rect = egui::Rect::from_min_size(
                        egui::pos2(bar.right() - 138.0 + n as f32 * 46.0, bar.top()),
                        egui::vec2(46.0, 46.0),
                    );
                    let tooltip = self.text(match n {
                        0 => Text::Minimize,
                        1 => {
                            if maximized {
                                Text::Restore
                            } else {
                                Text::Maximize
                            }
                        }
                        _ => Text::Close,
                    });
                    let response = ui
                        .put(
                            rect,
                            egui::Button::new("")
                                .fill(Color32::TRANSPARENT)
                                .stroke(Stroke::NONE)
                                .corner_radius(0),
                        )
                        .on_hover_text(tooltip);
                    response.widget_info(|| {
                        egui::WidgetInfo::labeled(egui::Role::Button, true, tooltip)
                    });
                    if response.hovered() {
                        ui.painter().rect_filled(rect, 0, selection());
                    }
                    let c = rect.center();
                    let line = Stroke::new(1.0, ink());
                    match n {
                        0 => {
                            ui.painter().line_segment(
                                [c + egui::vec2(-5.0, 0.0), c + egui::vec2(5.0, 0.0)],
                                line,
                            );
                        }
                        1 => {
                            let r = egui::Rect::from_center_size(c, egui::vec2(9.0, 9.0));
                            ui.painter()
                                .rect_stroke(r, 0, line, egui::StrokeKind::Inside);
                            if maximized {
                                ui.painter().line_segment(
                                    [c + egui::vec2(-2.0, -7.0), c + egui::vec2(7.0, -7.0)],
                                    line,
                                );
                                ui.painter().line_segment(
                                    [c + egui::vec2(7.0, -7.0), c + egui::vec2(7.0, 2.0)],
                                    line,
                                );
                            }
                        }
                        _ => {
                            ui.painter().line_segment(
                                [c + egui::vec2(-4.0, -4.0), c + egui::vec2(4.0, 4.0)],
                                line,
                            );
                            ui.painter().line_segment(
                                [c + egui::vec2(4.0, -4.0), c + egui::vec2(-4.0, 4.0)],
                                line,
                            );
                        }
                    }
                    if response.clicked() {
                        if n == 2 && self.page == Page::Installing {
                            self.control.request_cancel();
                            self.closing = true;
                        } else {
                            ctx.send_viewport_cmd(match n {
                                0 => egui::ViewportCommand::Minimized(true),
                                1 => egui::ViewportCommand::Maximized(!maximized),
                                _ => egui::ViewportCommand::Close,
                            });
                        }
                    }
                }
            });
    }

    fn sidebar(&self, root: &mut egui::Ui) {
        egui::Panel::left("museum-sidebar")
            .exact_size(240.0)
            .resizable(false)
            .frame(egui::Frame::new().fill(paper()).inner_margin(26))
            .show(root, |ui| {
                ui.add_space(36.0);
                let active = match self.page {
                    Page::Welcome => 0,
                    Page::Licence => 1,
                    Page::Destination => 2,
                    _ => 3,
                };
                let steps: &[Text] = if self.opts.uninstall_root.is_some()
                    || matches!(
                        self.page,
                        Page::Uninstall
                            | Page::Uninstalling
                            | Page::Uninstalled
                            | Page::UninstallFailed
                    ) {
                    &[Text::Uninstallation]
                } else {
                    &[
                        Text::Language,
                        Text::Licence,
                        Text::Destination,
                        Text::Installation,
                    ]
                };
                for (i, key) in steps.iter().copied().enumerate() {
                    let (rect, _) =
                        ui.allocate_exact_size(egui::vec2(188.0, 42.0), egui::Sense::hover());
                    let x = rect.left() + 4.0;
                    let y = rect.center().y;
                    if i + 1 < steps.len() {
                        ui.painter().line_segment(
                            [egui::pos2(x, y + 3.0), egui::pos2(x, y + 45.0)],
                            Stroke::new(1.0, rule()),
                        );
                    }
                    ui.painter().rect_filled(
                        egui::Rect::from_center_size(egui::pos2(x, y), egui::Vec2::splat(6.0)),
                        0,
                        if i == active || steps.len() == 1 {
                            ink()
                        } else if i < active {
                            muted()
                        } else {
                            rule()
                        },
                    );
                    ui.painter().text(
                        egui::pos2(rect.left() + 21.0, y),
                        egui::Align2::LEFT_CENTER,
                        format!("{:02}", i + 1),
                        FontId::monospace(10.0),
                        muted(),
                    );
                    ui.painter().text(
                        egui::pos2(rect.left() + 48.0, y),
                        egui::Align2::LEFT_CENTER,
                        self.text(key),
                        FontId::new(
                            13.0,
                            FontFamily::Name(
                                if i == active || steps.len() == 1 {
                                    "museum-semibold"
                                } else {
                                    "museum-inter"
                                }
                                .into(),
                            ),
                        ),
                        if i == active || steps.len() == 1 {
                            ink()
                        } else {
                            muted()
                        },
                    );
                }
            });
    }

    fn footer(&mut self, root: &mut egui::Ui, ctx: &egui::Context) {
        egui::Panel::bottom("museum-footer")
            .exact_size(94.0)
            .frame(egui::Frame::new().fill(paper()).inner_margin(egui::Margin {
                left: 38,
                right: 38,
                top: 18,
                bottom: 22,
            }))
            .show(root, |ui| {
                ui.horizontal(|ui| {
                    if matches!(self.page, Page::Licence | Page::Destination)
                        && secondary(ui, self.text(Text::Back)).clicked()
                    {
                        self.page = if self.page == Page::Licence {
                            Page::Welcome
                        } else {
                            Page::Licence
                        };
                    }
                    if self.page == Page::Installing {
                        if ui
                            .add_enabled(
                                !self.control.cancel_token().load(Ordering::Relaxed)
                                    && !self.control.is_committing(),
                                egui::Button::new(self.text(Text::Cancel))
                                    .fill(surface())
                                    .stroke(Stroke::new(1.0, rule()))
                                    .min_size(egui::vec2(100.0, 44.0))
                                    .corner_radius(0),
                            )
                            .clicked()
                        {
                            self.control.request_cancel();
                        }
                    }
                    if matches!(self.page, Page::Uninstall | Page::UninstallFailed)
                        && secondary(ui, self.text(Text::Cancel)).clicked()
                    {
                        ctx.send_viewport_cmd(egui::ViewportCommand::Close);
                    }
                    ui.with_layout(
                        egui::Layout::right_to_left(Align::Center),
                        |ui| match self.page {
                            Page::Welcome => {
                                if primary(ui, self.text(Text::Continue), true).clicked() {
                                    self.page = Page::Licence;
                                }
                            }
                            Page::Licence => {
                                if primary(ui, self.text(Text::Continue), self.accepted).clicked() {
                                    self.page = Page::Destination;
                                }
                            }
                            Page::Destination => {
                                if primary(
                                    ui,
                                    self.text(if self.installed_version.is_some() {
                                        Text::Upgrade
                                    } else {
                                        Text::Install
                                    }),
                                    self.accepted
                                        && self.release.is_some()
                                        && !self.loading
                                        && (self.installed_version.is_none() || self.can_upgrade()),
                                )
                                .clicked()
                                {
                                    self.start(ctx.clone());
                                }
                            }
                            Page::Installing => {}
                            Page::Finished => {
                                if primary(ui, self.text(Text::Launch), !self.read_only_preview())
                                    .clicked()
                                {
                                    self.finish(true, ctx);
                                }
                                if secondary(ui, self.text(Text::Finish)).clicked() {
                                    self.finish(false, ctx);
                                }
                            }
                            Page::Failed => {
                                if primary(ui, self.text(Text::Retry), true).clicked() {
                                    self.page = Page::Destination;
                                    self.closing = false;
                                }
                                if secondary(ui, self.text(Text::Close)).clicked() {
                                    ctx.send_viewport_cmd(egui::ViewportCommand::Close);
                                }
                            }
                            Page::Uninstall | Page::UninstallFailed => {
                                if primary(
                                    ui,
                                    self.text(if self.page == Page::UninstallFailed {
                                        Text::Retry
                                    } else {
                                        Text::Uninstall
                                    }),
                                    !self.read_only_preview(),
                                )
                                .clicked()
                                {
                                    self.start_uninstall(ctx.clone());
                                }
                            }
                            Page::Uninstalling => {}
                            Page::Uninstalled => {
                                if primary(ui, self.text(Text::Close), true).clicked() {
                                    ctx.send_viewport_cmd(egui::ViewportCommand::Close);
                                }
                            }
                        },
                    );
                });
            });
    }

    fn welcome(&mut self, ui: &mut egui::Ui) {
        title(ui, self.text(Text::ChooseLanguage), "");
        ui.add_space(28.0);
        let width = ui.available_width();
        let row_spacing = ui.spacing().item_spacing.y;
        ui.spacing_mut().item_spacing.y = 0.0;
        for language in Language::ALL {
            let chosen = language == self.language;
            let (rect, response) =
                ui.allocate_exact_size(egui::vec2(width, 44.0), egui::Sense::click());
            if chosen || response.hovered() {
                ui.painter()
                    .rect_filled(rect, 0, if chosen { selection() } else { selection() });
            }
            ui.painter().line_segment(
                [rect.left_bottom(), rect.right_bottom()],
                Stroke::new(1.0, rule()),
            );
            if chosen {
                ui.painter().rect_filled(
                    egui::Rect::from_center_size(
                        egui::pos2(rect.left() + 17.0, rect.center().y),
                        egui::Vec2::splat(6.0),
                    ),
                    0,
                    ink(),
                );
            }
            ui.painter().text(
                egui::pos2(rect.left() + 35.0, rect.center().y),
                egui::Align2::LEFT_CENTER,
                language.native(),
                FontId::proportional(16.0),
                ink(),
            );
            ui.painter().text(
                egui::pos2(rect.right() - 15.0, rect.center().y),
                egui::Align2::RIGHT_CENTER,
                language.code().to_ascii_uppercase(),
                FontId::monospace(10.0),
                muted(),
            );
            if response.clicked() {
                self.language = language;
                self.legal_document = legal_document(language);
                self.legal_lines.clear();
                self.legal_columns = 0;
                ui.ctx().send_viewport_cmd(egui::ViewportCommand::Title(
                    self.text(Text::SetupTitle).into(),
                ));
            }
        }
        ui.spacing_mut().item_spacing.y = row_spacing;
    }

    fn licence(&mut self, ui: &mut egui::Ui) {
        title(ui, self.text(Text::Licence), self.text(Text::LicenceBody));
        ui.add_space(14.0);
        let columns = ((ui.available_width() - 30.0) / 7.1).floor().max(35.0) as usize;
        if self.legal_columns != columns {
            self.legal_lines = wrap_legal(&self.legal_document, columns);
            self.legal_columns = columns;
        }
        egui::Frame::new()
            .fill(surface())
            .corner_radius(0)
            .stroke(Stroke::new(1.0, rule()))
            .inner_margin(14)
            .show(ui, |ui| {
                ui.set_min_width(ui.available_width());
                ui.spacing_mut().item_spacing.y = 0.0;
                egui::ScrollArea::vertical()
                    .id_salt("licence-document")
                    .max_height(274.0)
                    .min_scrolled_height(274.0)
                    .show_rows(ui, 15.0, self.legal_lines.len(), |ui, range| {
                        ui.spacing_mut().item_spacing.y = 0.0;
                        for n in range {
                            ui.add_sized(
                                egui::vec2(ui.available_width(), 15.0),
                                egui::Label::new(
                                    RichText::new(&self.legal_lines[n])
                                        .font(FontId::monospace(11.5))
                                        .color(ink()),
                                )
                                .halign(Align::Min)
                                .extend(),
                            );
                        }
                    });
            });
        ui.add_space(16.0);
        let label = self.text(Text::Accept);
        square_checkbox(ui, &mut self.accepted, label);
    }

    fn destination(&mut self, ui: &mut egui::Ui, ctx: &egui::Context) {
        title(
            ui,
            self.text(Text::Folder),
            self.text(Text::DestinationBody),
        );
        ui.add_space(22.0);
        let browse = self.text(Text::Browse);
        let width = ui.available_width();
        let (row, _) = ui.allocate_exact_size(egui::vec2(width, 44.0), egui::Sense::hover());
        let button_width = 112.0;
        let field = egui::Rect::from_min_max(
            row.min,
            egui::pos2(row.right() - button_width - 10.0, row.bottom()),
        );
        let button =
            egui::Rect::from_min_max(egui::pos2(row.right() - button_width, row.top()), row.max);
        if ui
            .put(
                field,
                egui::TextEdit::singleline(&mut self.destination)
                    .font(FontId::proportional(13.0))
                    .margin(egui::vec2(12.0, 0.0))
                    .align(egui::Align2::LEFT_CENTER)
                    .min_size(egui::vec2(field.width(), 44.0))
                    .desired_width(field.width()),
            )
            .changed()
        {
            self.refresh_installed_version();
            self.error = None;
        }
        if ui
            .put(
                button,
                egui::Button::new(RichText::new(browse).size(13.0))
                    .min_size(egui::vec2(button_width, 44.0))
                    .fill(surface())
                    .stroke(Stroke::new(1.0, rule()))
                    .corner_radius(0),
            )
            .clicked()
        {
            if let Some(folder) = rfd::FileDialog::new()
                .set_title(self.text(Text::Folder))
                .set_directory(self.destination.trim())
                .pick_folder()
            {
                let folder = if folder
                    .file_name()
                    .is_some_and(|n| n.eq_ignore_ascii_case("Pixel Museum"))
                {
                    folder
                } else {
                    folder.join("Pixel Museum")
                };
                self.destination = folder.to_string_lossy().into_owned();
                self.refresh_installed_version();
                self.error = None;
            }
        }
        ui.add_space(12.0);
        let hint = match (self.installed_version.as_deref(), self.release.as_ref()) {
            (Some(installed), Some(release)) if self.can_upgrade() => {
                format!(
                    "{installed} → {}
{}",
                    release.manifest.version,
                    self.text(Text::UpgradeKeepsData)
                )
            }
            (Some(installed), Some(release))
                if crate::update::version_is_newer(&release.manifest.version, installed) =>
            {
                self.text(Text::NewerVersionInstalled).to_owned()
            }
            (Some(_), Some(_)) => self.text(Text::CurrentVersion).to_owned(),
            (Some(_), None) => self.text(Text::UpgradeKeepsData).to_owned(),
            _ => self.text(Text::FolderHint).to_owned(),
        };
        ui.label(RichText::new(hint).size(12.0).color(muted()));
        if self.installed_version.is_none() {
            ui.add_space(18.0);
            square_checkbox(
                ui,
                &mut self.desktop_shortcut,
                self.language.text(Text::DesktopShortcut),
            );
        }
        ui.add_space(12.0);
        if self.loading {
            ui.horizontal(|ui| {
                ui.spinner();
                ui.label(self.text(Text::Loading));
            });
        } else if self.release.is_none() {
            ui.label(
                RichText::new(self.text(Text::NoPackage))
                    .size(13.0)
                    .color(muted()),
            );
            ui.add_space(8.0);
            if secondary(ui, self.text(Text::ChoosePackage)).clicked() {
                if let Some(file) = rfd::FileDialog::new()
                    .set_title(self.text(Text::Package))
                    .add_filter("Pixel Museum", &["json"])
                    .pick_file()
                {
                    self.opts.manifest = Some(file.to_string_lossy().into_owned());
                    self.load(ctx.clone());
                }
            }
        }
        if let Some(error) = &self.error {
            ui.add_space(6.0);
            ui.label(RichText::new(error).size(12.0).color(ink()));
        }
    }

    fn installing(&self, ui: &mut egui::Ui) {
        // Geometry and timing follow production draw_collection_install_view:
        // virtual x=260..1660, M at(1450,315), cell33, 78 cells step18/side12.
        let total = self
            .release
            .as_ref()
            .and_then(|r| r.manifest.download_bytes().ok())
            .unwrap_or(0);
        let (phase, done, total) = self
            .progress
            .as_ref()
            .map(|p| (p.phase, p.done, p.total))
            .unwrap_or(if self.upgrading {
                (Phase::Check, 0, 0)
            } else {
                (Phase::Download, 0, total)
            });
        let fraction = if total > 0 {
            (done as f32 / total as f32).clamp(0.0, 1.0)
        } else {
            0.0
        };
        let cancelling = self.control.cancel_token().load(Ordering::Relaxed);
        let waiting = total == 0 || cancelling || (!self.upgrading && phase != Phase::Download);
        let key = if cancelling {
            Text::Cancelling
        } else {
            match phase {
                Phase::Download => Text::Downloading,
                Phase::Check => Text::CheckingExisting,
                Phase::Verify if self.upgrading => Text::VerifyingUpdate,
                Phase::Verify => Text::Verifying,
                Phase::Extract => Text::ExtractingUpdate,
                Phase::Prepare => Text::PreparingUpdate,
                Phase::Install => Text::Installing,
                Phase::Finish if self.upgrading => Text::ApplyingUpdate,
                Phase::Finish => Text::Finishing,
            }
        };
        let width = ui
            .available_width()
            .min((ui.clip_rect().right() - 38.0 - ui.cursor().left()).max(1.0));
        let scale = width / 1400.0;
        ui.add_space(30.0);
        let (rect, _) =
            ui.allocate_exact_size(egui::vec2(width, 450.0 * scale), egui::Sense::hover());
        let time = ui.input(|i| i.time) as f32;
        let m = rect.min + egui::vec2(1190.0 * scale, 0.0);
        let cell = 33.0 * scale;
        let heading = ui.painter().layout(
            self.text(key).to_owned(),
            FontId::new(60.0 * scale, FontFamily::Proportional),
            ink(),
            1110.0 * scale,
        );
        ui.painter().galley(
            egui::pos2(rect.left(), m.y + cell * 2.5 - heading.size().y * 0.5),
            heading,
            ink(),
        );
        let ordinal = (time / 0.7) as usize % 13;
        let mark = [
            (0, 0),
            (4, 0),
            (0, 1),
            (1, 1),
            (3, 1),
            (4, 1),
            (0, 2),
            (2, 2),
            (4, 2),
            (0, 3),
            (4, 3),
            (0, 4),
            (4, 4),
        ];
        for (n, (x, y)) in mark.into_iter().enumerate() {
            ui.painter().rect_filled(
                egui::Rect::from_min_size(
                    m + egui::vec2(x as f32 * cell, y as f32 * cell),
                    egui::Vec2::splat(cell),
                ),
                0,
                ink().linear_multiply(if n == ordinal { 0.85 } else { 0.17 }),
            );
        }
        if total != 0 && !cancelling {
            let percent = ui.painter().layout_no_wrap(
                format!("{:.0}%", fraction * 100.0),
                FontId::monospace(40.0 * scale),
                ink(),
            );
            ui.painter().galley(
                egui::pos2(
                    rect.right() - percent.size().x,
                    rect.top() + 311.0 * scale - percent.size().y,
                ),
                percent,
                ink(),
            );
        }
        let moving = (time * 10.0) as usize % 78;
        let step = rect.width() / 78.0;
        let side = step * 12.0 / 18.0;
        for n in 0..78 {
            let mut alpha = if (n as f32) < fraction * 78.0 {
                0.82
            } else {
                0.10
            };
            if waiting && n >= moving && n < moving + 3 {
                alpha = 0.45;
            } else if !waiting && fraction < 1.0 && n == ((fraction * 78.0) as usize).min(77) {
                alpha = 0.5 + 0.35 * (time * 3.0).sin();
            }
            ui.painter().rect_filled(
                egui::Rect::from_min_size(
                    rect.min + egui::vec2(n as f32 * step, 344.0 * scale),
                    egui::Vec2::splat(side),
                ),
                0,
                ink().linear_multiply(alpha),
            );
        }
        if total != 0 && !cancelling {
            let detail = if phase == Phase::Prepare {
                format!("{done} / {total}")
            } else {
                format!("{} / {}", bytes(done), bytes(total))
            };
            ui.painter().text(
                rect.min + egui::vec2(0.0, 403.0 * scale),
                egui::Align2::LEFT_BOTTOM,
                detail,
                FontId::monospace(20.0 * scale),
                muted(),
            );
        }
    }

    fn finished(&mut self, ui: &mut egui::Ui) {
        if self.upgrading {
            title(ui, self.text(Text::UpgradeComplete), "");
            self.error_view(ui);
            return;
        }
        let language = self.language;
        #[cfg(feature = "preview")]
        let preview_audio_open =
            std::env::var_os("PIXEL_MUSEUM_SETUP_PREVIEW_AUDIO_OPEN").is_some();
        #[cfg(not(feature = "preview"))]
        let preview_audio_open = false;
        title(
            ui,
            language.text(Text::CompleteTitle),
            language.text(Text::SettingsIntro),
        );
        ui.add_space(20.0);
        ui.separator();
        ui.add_space(5.0);
        egui::CollapsingHeader::new(RichText::new(language.text(Text::Video)).font(FontId::new(
            14.0,
            FontFamily::Name("museum-semibold".into()),
        )))
        .id_salt("initial-video")
        .default_open(!preview_audio_open)
        .show(ui, |ui| {
            let display_modes = [Text::Fullscreen, Text::Borderless, Text::Windowed];
            let mut display_mode = if self.initial_settings.fullscreen {
                if self.initial_settings.borderless {
                    1
                } else {
                    0
                }
            } else {
                2
            };
            let mut size = (self.initial_settings.width, self.initial_settings.height);
            egui::Grid::new("video-preferences")
                .num_columns(2)
                .spacing([20.0, 8.0])
                .min_col_width(160.0)
                .show(ui, |ui| {
                    ui.label(language.text(Text::DisplayMode));
                    egui::ComboBox::from_id_salt("initial-display-mode")
                        .selected_text(language.text(display_modes[display_mode]))
                        .width(236.0)
                        .show_ui(ui, |ui| {
                            for (mode, label) in display_modes.into_iter().enumerate() {
                                ui.selectable_value(&mut display_mode, mode, language.text(label));
                            }
                        });
                    self.initial_settings.fullscreen = display_mode != 2;
                    self.initial_settings.borderless = display_mode == 1;
                    ui.end_row();
                    ui.label(language.text(Text::Resolution));
                    let sizes = crate::settings::resolution_choices(size, display_mode == 0);
                    if display_mode == 0 && !sizes.contains(&size) {
                        size = (1920, 1080);
                    }
                    let resolution_text = if self.initial_settings.borderless {
                        crate::settings::desktop_size().map_or_else(
                            || language.text(Text::Desktop).to_owned(),
                            |mode| {
                                format!(
                                    "{} \u{00b7} {}",
                                    language.text(Text::Desktop),
                                    crate::settings::resolution_label(mode)
                                )
                            },
                        )
                    } else {
                        crate::settings::resolution_label(size)
                    };
                    ui.add_enabled_ui(!self.initial_settings.borderless, |ui| {
                        egui::ComboBox::from_id_salt("initial-resolution")
                            .selected_text(resolution_text)
                            .width(236.0)
                            .show_ui(ui, |ui| {
                                for mode in sizes {
                                    ui.selectable_value(
                                        &mut size,
                                        mode,
                                        crate::settings::resolution_label(mode),
                                    );
                                }
                            });
                    });
                    ui.end_row();
                    ui.label(language.text(Text::FrameLimit));
                    let rate = if self.initial_settings.frame_limit == 0 {
                        language.text(Text::Unlimited).to_owned()
                    } else {
                        format!("{} FPS", self.initial_settings.frame_limit)
                    };
                    egui::ComboBox::from_id_salt("initial-frame-limit")
                        .selected_text(rate)
                        .width(154.0)
                        .show_ui(ui, |ui| {
                            for value in [30, 60, 120, 144, 165, 240, 360, 0] {
                                let text = if value == 0 {
                                    language.text(Text::Unlimited).to_owned()
                                } else {
                                    format!("{value} FPS")
                                };
                                ui.selectable_value(
                                    &mut self.initial_settings.frame_limit,
                                    value,
                                    text,
                                );
                            }
                        });
                    ui.end_row();
                });
            self.initial_settings.width = size.0;
            self.initial_settings.height = size.1;
            ui.add_space(9.0);
            square_checkbox(
                ui,
                &mut self.initial_settings.vsync,
                language.text(Text::Vsync),
            );
        });
        ui.add_space(6.0);
        ui.separator();
        ui.add_space(5.0);
        egui::CollapsingHeader::new(RichText::new(language.text(Text::Audio)).font(FontId::new(
            14.0,
            FontFamily::Name("museum-semibold".into()),
        )))
        .id_salt("initial-audio")
        .default_open(preview_audio_open)
        .show(ui, |ui| {
            egui::Grid::new("audio-preferences")
                .num_columns(2)
                .spacing([20.0, 9.0])
                .min_col_width(160.0)
                .show(ui, |ui| {
                    for (key, level) in [
                        (Text::Master, &mut self.initial_settings.master),
                        (Text::Sfx, &mut self.initial_settings.sfx),
                        (Text::Ambient, &mut self.initial_settings.ambient),
                        (Text::Culture, &mut self.initial_settings.culture),
                    ] {
                        ui.label(language.text(key));
                        ui.add(
                            egui::Slider::new(level, 0.0..=1.0)
                                .step_by(0.01)
                                .custom_formatter(|v, _| format!("{:.0}%", v * 100.0)),
                        );
                        ui.end_row();
                    }
                });
        });
        ui.add_space(12.0);
        ui.horizontal_wrapped(|ui| {
            ui.label(
                RichText::new(language.text(Text::DualSenseFirmwareAdvice))
                    .small()
                    .color(muted()),
            );
            ui.hyperlink_to(
                RichText::new(language.text(Text::DownloadPlayStationAccessories)).small(),
                format!(
                    "https://controller.dl.playstation.net/controller/lang/{}/2100004.html",
                    language.code()
                ),
            );
        });
        self.error_view(ui);
    }

    fn finish(&mut self, launch: bool, ctx: &egui::Context) {
        if self.read_only_preview() {
            if !launch {
                ctx.send_viewport_cmd(egui::ViewportCommand::Close);
            }
            return;
        }
        let root = PathBuf::from(self.destination.trim());
        if !self.upgrading {
            if let Err(error) = self.initial_settings.save(&root) {
                self.error = Some(format!("{error:#}"));
                return;
            }
        }
        if launch {
            let executable = self
                .release
                .as_ref()
                .map(|r| r.manifest.executable.as_str())
                .unwrap_or("Pixel Museum.exe");
            if let Err(error) = std::process::Command::new(root.join(executable))
                .current_dir(&root)
                .spawn()
            {
                self.error = Some(format!("{}\n{error}", self.text(Text::LaunchError)));
                return;
            }
        }
        ctx.send_viewport_cmd(egui::ViewportCommand::Close);
    }

    fn failed(&self, ui: &mut egui::Ui) {
        title(
            ui,
            self.text(if self.was_cancelled {
                Text::CancelledTitle
            } else {
                Text::FailedTitle
            }),
            if self.was_cancelled {
                self.text(Text::CancelledBody)
            } else {
                ""
            },
        );
        ui.add_space(18.0);
        self.error_view(ui);
    }

    fn uninstall_page(&mut self, ui: &mut egui::Ui) {
        let (heading, body) = match self.page {
            Page::Uninstalled => (
                Text::UninstalledTitle,
                if self.remove_personal_data {
                    Text::UninstalledFullBody
                } else {
                    Text::UninstalledBody
                },
            ),
            Page::UninstallFailed => (Text::UninstallFailed, Text::UninstallBody),
            Page::Uninstalling => (Text::Uninstalling, Text::UninstallBody),
            _ => (Text::UninstallTitle, Text::UninstallBody),
        };
        title(ui, self.text(heading), self.text(body));
        if matches!(self.page, Page::Uninstall | Page::UninstallFailed) {
            ui.add_space(16.0);
            let label = self.text(Text::RemovePersonalData);
            square_checkbox(ui, &mut self.remove_personal_data, label);
        }
        if self
            .opts
            .uninstall_root
            .as_ref()
            .is_some_and(|root| crate::uninstall::retains_running_helper(root))
        {
            ui.add_space(12.0);
            ui.label(
                RichText::new(self.text(Text::MaintenanceRetained))
                    .size(14.0)
                    .color(muted()),
            );
        }
        ui.add_space(24.0);
        ui.label(
            RichText::new(self.text(Text::Folder))
                .size(12.0)
                .color(muted()),
        );
        ui.add_space(6.0);
        ui.add(
            egui::Label::new(RichText::new(&self.destination).size(14.0).color(ink()))
                .wrap()
                .selectable(true),
        );
        if self.page == Page::Uninstalling {
            ui.add_space(28.0);
            let time = ui.ctx().input(|i| i.time);
            let (rect, _) = ui.allocate_exact_size(egui::vec2(96.0, 96.0), egui::Sense::hover());
            paint_pixel_m(ui, rect.center(), 54.0, time, true);
        }
        self.error_view(ui);
    }

    fn error_view(&self, ui: &mut egui::Ui) {
        if let Some(error) = &self.error {
            ui.add_space(8.0);
            egui::CollapsingHeader::new(RichText::new(self.text(Text::Details)).size(12.0))
                .default_open(matches!(self.page, Page::Failed | Page::UninstallFailed))
                .show(ui, |ui| {
                    egui::ScrollArea::vertical()
                        .max_height(130.0)
                        .show(ui, |ui| {
                            ui.label(RichText::new(error).size(12.0).color(ink()));
                        });
                });
        }
    }
}

impl eframe::App for Setup {
    #[cfg(feature = "preview")]
    fn raw_input_hook(&mut self, ctx: &egui::Context, raw: &mut egui::RawInput) {
        if std::env::var_os("PIXEL_MUSEUM_SETUP_PREVIEW_HOVER_THEME").is_some() {
            let width = raw
                .viewports
                .get(&egui::ViewportId::ROOT)
                .and_then(|v| v.inner_rect)
                .map(|r| r.width())
                .unwrap_or_else(|| ctx.content_rect().width());
            raw.events
                .push(egui::Event::PointerMoved(egui::pos2(width - 161.0, 23.0)));
        }
    }
    fn logic(&mut self, ctx: &egui::Context, _: &mut eframe::Frame) {
        if !self.manual_theme {
            let dark = ctx.system_theme() == Some(egui::Theme::Dark);
            if dark != self.installer_dark {
                self.installer_dark = dark;
                apply_theme(ctx, dark);
            }
        }
        #[cfg(feature = "preview")]
        if std::env::var_os("PIXEL_MUSEUM_SETUP_SCREENSHOT").is_some() {
            ctx.send_viewport_cmd(egui::ViewportCommand::RequestPaintWhileHidden);
        }
        self.read_messages(ctx);
        if ctx.input(|i| i.viewport().close_requested()) && self.page == Page::Installing {
            self.control.request_cancel();
            self.closing = true;
            ctx.send_viewport_cmd(egui::ViewportCommand::CancelClose);
        }
        if ctx.input(|i| i.viewport().close_requested()) && self.page == Page::Uninstalling {
            self.closing = true;
            ctx.send_viewport_cmd(egui::ViewportCommand::CancelClose);
        }
    }

    fn ui(&mut self, root: &mut egui::Ui, _: &mut eframe::Frame) {
        let ctx = root.ctx().clone();
        let window = root.max_rect();
        self.titlebar(root, &ctx);
        self.sidebar(root);
        self.footer(root, &ctx);
        egui::CentralPanel::default()
            .frame(egui::Frame::new().fill(paper()).inner_margin(0))
            .show(root, |ui| {
                egui::ScrollArea::vertical()
                    .id_salt("page-scroll")
                    .auto_shrink([false, false])
                    .show(ui, |ui| {
                        egui::Frame::new()
                            .inner_margin(egui::Margin {
                                left: 38,
                                right: 38,
                                top: 34,
                                bottom: 12,
                            })
                            .show(ui, |ui| {
                                ui.set_width(ui.available_width());
                                match self.page {
                                    Page::Welcome => self.welcome(ui),
                                    Page::Licence => self.licence(ui),
                                    Page::Destination => self.destination(ui, &ctx),
                                    Page::Installing => self.installing(ui),
                                    Page::Finished => self.finished(ui),
                                    Page::Failed => self.failed(ui),
                                    Page::Uninstall
                                    | Page::Uninstalling
                                    | Page::Uninstalled
                                    | Page::UninstallFailed => self.uninstall_page(ui),
                                }
                            });
                    });
            });
        resize_frame(root, window, &ctx);
        if matches!(self.page, Page::Installing | Page::Uninstalling) || self.loading {
            ctx.request_repaint_after(Duration::from_millis(150));
        }
        #[cfg(feature = "preview")]
        if !self.preview_captured {
            ctx.request_repaint_after(Duration::from_millis(100));
            if ctx.cumulative_pass_nr() >= 3 && !self.loading {
                if let Ok(path) = std::env::var("PIXEL_MUSEUM_SETUP_SCREENSHOT") {
                    self.preview_captured = true;
                    let crop_theme =
                        std::env::var_os("PIXEL_MUSEUM_SETUP_PREVIEW_CROP_THEME").is_some();
                    let logical_width = ctx.content_rect().width();
                    ctx.request_screenshot(move |pixels| {
                        let (x, y, width, height) = if crop_theme {
                            let scale = pixels.width() as f32 / logical_width;
                            let x = ((logical_width - 184.0) * scale).round() as usize;
                            (
                                x,
                                0,
                                (46.0 * scale).round() as usize,
                                (46.0 * scale).round() as usize,
                            )
                        } else {
                            (0, 0, pixels.width(), pixels.height())
                        };
                        let mut bytes = Vec::with_capacity(width * height * 4);
                        for row in y..y + height {
                            for pixel in &pixels.pixels
                                [row * pixels.width() + x..row * pixels.width() + x + width]
                            {
                                bytes.extend_from_slice(&pixel.to_array());
                            }
                        }
                        image::save_buffer(
                            path,
                            &bytes,
                            width as u32,
                            height as u32,
                            image::ColorType::Rgba8,
                        )
                        .expect("save setup preview");
                        std::process::exit(0);
                    });
                }
            }
        }
    }
}

fn title(ui: &mut egui::Ui, heading: &str, description: &str) {
    ui.label(
        RichText::new(heading)
            .font(FontId::new(32.0, FontFamily::Name("museum-heading".into())))
            .color(ink()),
    );
    if !description.is_empty() {
        ui.add_space(15.0);
        ui.label(RichText::new(description).size(15.0).color(muted()));
    }
}

fn paint_brand(ui: &egui::Ui, anchor: egui::Pos2) {
    let scale = 0.8;
    let origin = anchor - egui::vec2(0.0, 16.0 * scale);
    let cell = 32.0 / 7.0 * scale;
    for (x, y) in [
        (1, 1),
        (5, 1),
        (1, 2),
        (2, 2),
        (4, 2),
        (5, 2),
        (1, 3),
        (3, 3),
        (5, 3),
        (1, 4),
        (5, 4),
        (1, 5),
        (5, 5),
    ] {
        ui.painter().rect_filled(
            egui::Rect::from_min_size(
                origin + egui::vec2(x as f32 * cell, y as f32 * cell),
                egui::Vec2::splat(cell),
            ),
            0,
            ink(),
        );
    }
    let mut x = origin.x + 42.0 * scale;
    for character in "PIXEL MUSEUM".chars() {
        let glyph = ui.painter().layout_no_wrap(
            character.to_string(),
            FontId::new(14.0 * scale, FontFamily::Name("museum-semibold".into())),
            ink(),
        );
        ui.painter().galley(
            egui::pos2(x, anchor.y - glyph.size().y * 0.5),
            glyph.clone(),
            ink(),
        );
        x += glyph.size().x + 1.5 * scale;
    }
}

fn paint_pixel_m(ui: &egui::Ui, center: egui::Pos2, side: f32, time: f64, animated: bool) {
    let ordinal = (time / 0.7) as usize % 13;
    let cell = side / 5.0;
    let origin = center - egui::Vec2::splat(side / 2.0);
    for (n, (x, y)) in [
        (0, 0),
        (4, 0),
        (0, 1),
        (1, 1),
        (3, 1),
        (4, 1),
        (0, 2),
        (2, 2),
        (4, 2),
        (0, 3),
        (4, 3),
        (0, 4),
        (4, 4),
    ]
    .into_iter()
    .enumerate()
    {
        ui.painter().rect_filled(
            egui::Rect::from_min_size(
                origin + egui::vec2(x as f32 * cell, y as f32 * cell),
                egui::Vec2::splat(cell),
            ),
            0,
            ink().linear_multiply(if !animated || n == ordinal {
                0.85
            } else {
                0.17
            }),
        );
    }
}

fn paint_theme_icon(ui: &egui::Ui, center: egui::Pos2, dark: bool) {
    // Same 24-unit SVG geometry and rounded 1.65-unit stroke as website/site.js.
    let scale = 20.0 / 24.0;
    let map = |point: Vec2| center + (point - egui::vec2(12.0, 12.0)) * scale;
    let stroke = Stroke::new(1.65 * scale, ink());
    if dark {
        ui.painter().circle_stroke(center, 4.0 * scale, stroke);
        for n in 0..8 {
            let angle = n as f32 * std::f32::consts::TAU / 8.0;
            let direction = egui::vec2(angle.cos(), angle.sin());
            let points = [
                center + direction * (8.0 * scale),
                center + direction * (10.0 * scale),
            ];
            ui.painter().line_segment(points, stroke);
            for point in points {
                ui.painter().circle_filled(point, stroke.width * 0.5, ink());
            }
        }
    } else {
        // M21 12.79 A9 9 0 1 1 11.21 3 A7 7 0 0 0 21 12.79 Z
        // Stroke each smooth arc separately; round their shared ends in ink.
        // This avoids a sharp miter at the cusp and never masks the background.
        let first = egui::vec2(21.0, 12.79);
        let last = egui::vec2(11.21, 3.0);
        for (from, to, radius, clockwise) in
            [(first, last, 9.0f32, true), (last, first, 7.0, false)]
        {
            let chord = to - from;
            let h = (radius * radius - chord.length_sq() * 0.25).sqrt();
            let arc_center = (from + to) * 0.5 - egui::vec2(-chord.y, chord.x).normalized() * h;
            let start = (from - arc_center).angle();
            let mut sweep = (to - arc_center).angle() - start;
            if clockwise && sweep < 0.0 {
                sweep += std::f32::consts::TAU;
            } else if !clockwise && sweep > 0.0 {
                sweep -= std::f32::consts::TAU;
            }
            let points = (0..=48)
                .map(|n| {
                    let t = start + sweep * n as f32 / 48.0;
                    map(arc_center + egui::vec2(t.cos(), t.sin()) * radius)
                })
                .collect();
            ui.painter().add(egui::Shape::line(points, stroke));
        }
        for point in [first, last] {
            ui.painter()
                .circle_filled(map(point), stroke.width * 0.5, ink());
        }
    }
}

fn square_checkbox(ui: &mut egui::Ui, checked: &mut bool, label: &str) -> egui::Response {
    let text = ui.painter().layout(
        label.to_owned(),
        FontId::proportional(13.0),
        ink(),
        (ui.available_width() - 28.0).max(60.0),
    );
    let height = text.size().y.max(18.0) + 8.0;
    let (rect, mut response) = ui.allocate_exact_size(
        egui::vec2(ui.available_width(), height),
        egui::Sense::click(),
    );
    #[cfg(feature = "preview")]
    if std::env::var_os("PIXEL_MUSEUM_SETUP_PREVIEW_CHECKBOX_FOCUS").is_some() {
        response.request_focus();
    }
    let keyboard = response.has_focus()
        && ui.input(|i| i.key_pressed(egui::Key::Space) || i.key_pressed(egui::Key::Enter));
    if response.clicked() || keyboard {
        *checked = !*checked;
        response.mark_changed();
        response.request_focus();
    }
    response.widget_info(|| {
        egui::WidgetInfo::selected(egui::Role::CheckBox, ui.is_enabled(), *checked, label)
    });
    let square = egui::Rect::from_center_size(
        egui::pos2(rect.left() + 9.0, rect.center().y),
        egui::vec2(18.0, 18.0),
    );
    ui.painter().rect_filled(
        square,
        0,
        if *checked {
            ink()
        } else {
            Color32::TRANSPARENT
        },
    );
    ui.painter()
        .rect_stroke(square, 0, Stroke::new(1.0, ink()), egui::StrokeKind::Inside);
    if *checked {
        for (x, y, w, h) in [
            (4., 8., 2., 2.),
            (6., 10., 2., 2.),
            (8., 8., 2., 3.),
            (10., 6., 2., 3.),
            (12., 4., 2., 3.),
        ] {
            ui.painter().rect_filled(
                egui::Rect::from_min_size(square.min + egui::vec2(x, y), egui::vec2(w, h)),
                0,
                surface(),
            );
        }
    }
    ui.painter().galley(
        egui::pos2(rect.left() + 28.0, rect.center().y - text.size().y * 0.5),
        text,
        ink(),
    );
    if response.has_focus() {
        ui.painter().rect_stroke(
            square.shrink(2.0),
            0,
            Stroke::new(1.0, if *checked { surface() } else { ink() }),
            egui::StrokeKind::Inside,
        );
    }
    response.on_hover_cursor(egui::CursorIcon::PointingHand)
}

fn wrap_legal(text: &str, columns: usize) -> Vec<String> {
    let mut lines = Vec::new();
    for original in text.lines() {
        if original.trim().is_empty() {
            lines.push(String::new());
            continue;
        }
        let mut row = String::new();
        let mut length = 0;
        for word in original.split_whitespace() {
            let count = word.chars().count();
            if length > 0 && length + 1 + count > columns {
                lines.push(std::mem::take(&mut row));
                length = 0;
            }
            if count > columns {
                for character in word.chars() {
                    if length == columns {
                        lines.push(std::mem::take(&mut row));
                        length = 0;
                    }
                    row.push(character);
                    length += 1;
                }
            } else {
                if length > 0 {
                    row.push(' ');
                    length += 1;
                }
                row.push_str(word);
                length += count;
            }
        }
        if !row.is_empty() {
            lines.push(row);
        }
    }
    lines
}

fn resize_frame(ui: &mut egui::Ui, rect: egui::Rect, ctx: &egui::Context) {
    if ctx.input(|i| i.viewport().maximized.unwrap_or(false)) {
        return;
    }
    use egui::ResizeDirection as D;
    let lo = rect.min;
    let hi = rect.max;
    let corner = 10.0;
    let edge = 4.0;
    for (n, (a, b, d, cursor)) in [
        (
            lo,
            lo + egui::vec2(corner, corner),
            D::NorthWest,
            egui::CursorIcon::ResizeNwSe,
        ),
        (
            egui::pos2(hi.x - corner, lo.y),
            egui::pos2(hi.x, lo.y + corner),
            D::NorthEast,
            egui::CursorIcon::ResizeNeSw,
        ),
        (
            egui::pos2(lo.x, hi.y - corner),
            egui::pos2(lo.x + corner, hi.y),
            D::SouthWest,
            egui::CursorIcon::ResizeNeSw,
        ),
        (
            hi - egui::vec2(corner, corner),
            hi,
            D::SouthEast,
            egui::CursorIcon::ResizeNwSe,
        ),
        (
            lo + egui::vec2(corner, 0.0),
            egui::pos2(hi.x - corner, lo.y + edge),
            D::North,
            egui::CursorIcon::ResizeVertical,
        ),
        (
            egui::pos2(lo.x + corner, hi.y - edge),
            hi - egui::vec2(corner, 0.0),
            D::South,
            egui::CursorIcon::ResizeVertical,
        ),
        (
            lo + egui::vec2(0.0, corner),
            egui::pos2(lo.x + edge, hi.y - corner),
            D::West,
            egui::CursorIcon::ResizeHorizontal,
        ),
        (
            egui::pos2(hi.x - edge, lo.y + corner),
            hi - egui::vec2(0.0, corner),
            D::East,
            egui::CursorIcon::ResizeHorizontal,
        ),
    ]
    .into_iter()
    .enumerate()
    {
        let response = ui
            .interact(
                egui::Rect::from_min_max(a, b),
                ui.scope_id().with(("window-resize", n)),
                egui::Sense::drag(),
            )
            .on_hover_cursor(cursor);
        if response.drag_started() {
            ctx.send_viewport_cmd(egui::ViewportCommand::BeginResize(d));
        }
    }
}

fn primary(ui: &mut egui::Ui, label: &str, enabled: bool) -> egui::Response {
    ui.add_enabled(
        enabled,
        egui::Button::new(
            RichText::new(label)
                .font(FontId::new(
                    14.0,
                    FontFamily::Name("museum-semibold".into()),
                ))
                .color(surface()),
        )
        .fill(ink())
        .stroke(Stroke::NONE)
        .min_size(egui::vec2(132.0, 44.0))
        .corner_radius(0),
    )
}

fn secondary(ui: &mut egui::Ui, label: &str) -> egui::Response {
    ui.add(
        egui::Button::new(RichText::new(label).size(13.0).color(ink()))
            .fill(surface())
            .stroke(Stroke::new(1.0, rule()))
            .min_size(egui::vec2(100.0, 44.0))
            .corner_radius(0),
    )
}

fn bytes(n: u64) -> String {
    if n >= 1024 * 1024 * 1024 {
        format!("{:.2} GiB", n as f64 / 1073741824.0)
    } else {
        format!("{:.1} MiB", n as f64 / 1048576.0)
    }
}

fn configure(ctx: &egui::Context) {
    let mut fonts = FontDefinitions::default();
    // Segoe remains a platform fallback; the primary face is the museum's exact Inter.
    if let Ok(bytes) = std::fs::read("C:\\Windows\\Fonts\\segoeui.ttf") {
        fonts
            .font_data
            .insert("museum-ui".into(), Arc::new(FontData::from_owned(bytes)));
        fonts
            .families
            .entry(FontFamily::Proportional)
            .or_default()
            .insert(0, "museum-ui".into());
    }
    let base = FontData::from_static(include_bytes!("../assets/Inter.ttf"));
    for (name, weight) in [
        ("museum-inter", 400.0),
        ("museum-semibold", 600.0),
        ("museum-heading", 650.0),
    ] {
        let mut data = base.clone();
        data.tweak.coords = egui::epaint::text::VariationCoords::new([(b"wght", weight)]);
        fonts.font_data.insert(name.into(), Arc::new(data));
        let mut family = fonts
            .families
            .get(&FontFamily::Proportional)
            .cloned()
            .unwrap_or_default();
        family.insert(0, name.into());
        fonts.families.insert(FontFamily::Name(name.into()), family);
    }
    fonts
        .families
        .get_mut(&FontFamily::Proportional)
        .unwrap()
        .insert(0, "museum-inter".into());
    ctx.set_fonts(fonts);
    ctx.set_theme(egui::ThemePreference::System);
    apply_theme(ctx, ctx.system_theme() == Some(egui::Theme::Dark));
}

fn apply_theme(ctx: &egui::Context, dark: bool) {
    COLORS.with(|colors| {
        colors.set(if dark {
            Palette::dark()
        } else {
            Palette::light()
        })
    });
    let mut style = egui::Style::default();
    style.visuals = if dark {
        egui::Visuals::dark()
    } else {
        egui::Visuals::light()
    };
    style.visuals.override_text_color = Some(ink());
    style.visuals.hyperlink_color = ink();
    style.visuals.warn_fg_color = ink();
    style.visuals.error_fg_color = ink();
    style.visuals.window_corner_radius = egui::CornerRadius::ZERO;
    style.visuals.panel_fill = paper();
    style.visuals.window_fill = surface();
    style.visuals.selection.bg_fill = selection();
    style.visuals.selection.stroke = Stroke::new(1.0, ink());
    style.visuals.widgets.noninteractive.bg_fill = surface();
    style.visuals.widgets.noninteractive.bg_stroke = Stroke::new(1.0, rule());
    style.visuals.widgets.inactive.bg_fill = surface();
    style.visuals.widgets.inactive.weak_bg_fill = surface();
    style.visuals.widgets.inactive.bg_stroke = Stroke::new(1.0, rule());
    style.visuals.widgets.hovered.bg_fill = selection();
    style.visuals.widgets.hovered.weak_bg_fill = selection();
    style.visuals.widgets.active.bg_fill = selection();
    style.visuals.widgets.active.bg_stroke = Stroke::new(1.0, ink());
    style.visuals.widgets.active.fg_stroke = Stroke::new(1.0, ink());
    style.visuals.widgets.hovered.bg_stroke = Stroke::new(1.0, ink());
    style.visuals.widgets.hovered.fg_stroke = Stroke::new(1.0, ink());
    style.visuals.widgets.inactive.corner_radius = egui::CornerRadius::same(0);
    style.visuals.widgets.hovered.corner_radius = egui::CornerRadius::same(0);
    style.visuals.widgets.active.corner_radius = egui::CornerRadius::same(0);
    style.spacing.item_spacing = Vec2::new(8.0, 8.0);
    style.spacing.button_padding = Vec2::new(15.0, 10.0);
    style.spacing.interact_size = Vec2::new(30.0, 30.0);
    style
        .text_styles
        .insert(egui::TextStyle::Body, FontId::proportional(14.0));
    style.text_styles.insert(
        egui::TextStyle::Button,
        FontId::new(14.0, FontFamily::Name("museum-semibold".into())),
    );
    ctx.set_global_style(style);
}
