// Pixel Museum — a controller-first collection, built with ps5-homebrew-ui.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "museum/catalog.hpp"
#include "museum/culture_ambience.hpp"
#include "museum/culture_audio_route.hpp"
#include "museum/theme.hpp"
#include "museum/localization.hpp"
#include "museum/object_scene.hpp"
#include "museum/pixel_workshop.hpp"
#include "museum/study.hpp"
#include "museum/experience_audio.hpp"
#include "museum/study_catalog.hpp"
#include "museum/credit_layout.hpp"
#include "museum/narrative_layout.hpp"
#include "museum/timeline_motion.hpp"
#include "museum/volume_preferences.hpp"
#include "museum/collection_installer.hpp"
#include "museum/screen_collection_policy.hpp"
#include "museum/desktop_settings.hpp"
#include "museum/database_updater.hpp"
#if defined(MUSEUM_DESKTOP)
#include "museum/application_updater.hpp"
#endif
#include "museum/collection_install_view.hpp"
#include "platform/media.hpp"
#include "gfx/renderer.hpp"
#include "ui/components/image_viewer.hpp"
#include "ui/components/input_prompt.hpp"
#include "museum/search.hpp"
#include "museum/trophies.hpp"
#include "museum/pin_scene.hpp"
#include "platform/ps5/trophy_notification.hpp"
#include "ui/glyphs.hpp"
#include <string>
#include <algorithm>
#include <cmath>
#include <map>
#include <array>
#include <functional>
#include <atomic>
#include <pthread.h>
namespace museum {
class Screen {
    friend struct ScreenInspection;
    friend struct CollectionStartupInspection;
    friend struct CollectionRemovalInspection;
#if defined(MUSEUM_DESKTOP)
    friend struct DesktopInputInspection;
    friend struct DesktopNavigationInspection;
#endif
public:
    ~Screen();
    bool init(const std::string& root,const std::string& data);
    void handle(const hui::InputFrame&,hui::ui::Feedback&);
    void update(float dt);
    void draw(int width,int height,unsigned framebuffer=0);
    void shutdown();
    void select(const std::string& id);
    void preview(int mode); // 0 timeline, 1 story, 2 gallery, 3 screening, 4 preferences, 5 credits
    void log_performance()const;
    void mix_video(float* out,unsigned frames,float* controller_speaker=nullptr,bool culture_on_pad=false);
    void mix_experience(float*out,unsigned frames,float*controller_speaker=nullptr){experience_audio_.render(out,frames,controller_speaker);}
    bool take_trophy_sound(){const bool sound=trophy_fallback_sound_;trophy_fallback_sound_=false;return sound;}
    bool onboarding_active()const{return onboarding_||language_choice_||theme_choice_||theme_confirming_;}
    bool collection_pending()const{return collection_pending_;}
    bool experience_active()const{return experience_active_;}
    bool secondary_controller_active()const{return experience_active_&&study_&&study_->local_multiplayer();}
    bool culture_timeline_active()const{return history_focus_;}
    float archival_ambient_gain()const{return culture_ambience_.ambient_gain();}
    std::vector<int> today_entries(bool culture) const;
    std::string today_date_label() const;
    float selected_year() const;
    bool video_active() const;
    bool music_player_active()const{return playlist_active_;}
    float music_volume()const{return volume_;}
    float master_volume()const{return master_volume_;}
    float sfx_volume()const{return sfx_volume_;}
    float culture_volume()const{return culture_volume_;}
    float pad_volume()const{return pad_volume_;}
    bool culture_audio_on_pad()const{return culture_audio_on_pad_;}
    bool music_muted()const{return volume_<=0.f;}
    void set_refresh_hz(float hz) {
#if defined(MUSEUM_DESKTOP)
        target_refresh_hz_ = hz>=30.f&&hz<=360.f ? hz : 60.f;
#else
        target_refresh_hz_ = hz == 120.f ? 120.f : 60.f;
#endif
    }
    bool motion_controls()const{return experience_active_&&!experience_paused_&&!experience_introduction_&&study_&&study_->motion_controls();}
    bool wants_quit()const{return quit_;}
    int take_startup_note(int* pixel_ordinal=nullptr);
    Catalog& catalog(){return catalog_;}
    using TrophyPinRenderer=std::function<unsigned(const TrophyView&,int,int,float,float,float,float)>;
    void set_trophy_pin_renderer(TrophyPinRenderer render){trophy_pin_renderer_=std::move(render);}
    void set_trophy_curator_preview(bool value){trophy_curator_preview_=value;}
    bool trophy_curator_preview()const{return trophy_curator_preview_;}
#if defined(MUSEUM_DESKTOP)
    void set_desktop_video_modes(DesktopDisplayModes);
    void init_desktop_video_settings(const DesktopVideoSettings& current);
    const DesktopVideoSettings& desktop_video_settings()const{return desktop_video_;}
    bool take_desktop_video_request(DesktopVideoSettings&);
    void set_desktop_video_settings_applied(const DesktopVideoSettings&);
    void desktop_video_apply_failed(const std::string& reason);
    bool wants_text_input()const{return search_prompt_.is_open();}
    bool desktop_dark_theme()const{return theme_mix_.value>=.5f;}
    bool desktop_pointer_interactive()const;
    unsigned desktop_navigation_feedback_state()const;
    bool take_desktop_url_request(std::string&);
    std::string desktop_resources_error()const;
    bool take_application_restart_request();
    bool begin_application_restart();
#endif
private:
    bool support_dialog_=false;
    int support_focus_=0;
    unsigned support_qr_=0;
    hui::tween::Spring support_open_;
    void open_support(hui::ui::Feedback&);
    bool handle_support(const hui::InputFrame&,hui::ui::Feedback&);
    void draw_support();
    int support_action_count()const;
    const char* support_action_label(int)const;
    hui::gfx::Rect support_action_bounds(int)const;
    DatabaseUpdater database_updater_;
    bool initial_database_sync_=false,initial_database_started_=false,initial_database_complete_=false;
    std::string initial_database_error_;
    DatabaseUpdater::Snapshot database_state_;
    bool database_auto_checked_=false,database_dialog_=false;
    std::uint64_t database_notified_revision_=0,database_ready_notified_revision_=0;
    int database_focus_=0;
    float database_completion_notice_=0;
    static std::string update_download_amount(std::uint64_t downloaded,std::uint64_t total);
    void draw_update_progress();
    void render_notifications();
    hui::tween::Spring database_open_;
    void open_database_update(hui::ui::Feedback&);
    bool handle_database_update(const hui::InputFrame&,hui::ui::Feedback&);
    void update_database(float);
    void observe_database_update(const DatabaseUpdater::Snapshot&);
    bool database_notification_ready()const;
    void draw_database_update();
    int database_action_count()const;
    const char* database_action_label(int)const;
    hui::gfx::Rect database_action_bounds(int)const;
#if defined(MUSEUM_DESKTOP)
    ApplicationUpdater application_updater_;
    ApplicationUpdater::Snapshot application_state_;
    bool application_auto_checked_=false,application_dialog_=false,application_restart_request_=false,application_restart_failed_=false;
    bool application_combined_check_=false;
    std::string application_notified_version_,application_ready_notified_version_,application_restart_error_;
    int application_focus_=0;
    float application_completion_notice_=0;
    hui::tween::Spring application_open_;
    void open_application_update(hui::ui::Feedback&);
    void open_update_check(hui::ui::Feedback&);
    bool handle_application_update(const hui::InputFrame&,hui::ui::Feedback&);
    void update_application(float);
    void observe_application_update(const ApplicationUpdater::Snapshot&);
    bool application_notification_ready()const;
    void draw_application_update();
    int application_action_count()const;
    const char* application_action_label(int)const;
    hui::gfx::Rect application_action_bounds(int)const;
    DesktopDisplayModes desktop_modes_;
    DesktopVideoSettings desktop_video_,desktop_video_draft_,desktop_video_request_;
    void select_desktop_resolution(int direction);
    bool desktop_video_open_=false,desktop_video_pending_=false,desktop_video_applying_=false;
    int desktop_video_focus_=0;
    hui::DesktopControllerStyle desktop_controller_style_=hui::DesktopControllerStyle::keyboard_mouse;
    hui::PointerInput desktop_pointer_{};
    hui::gfx::DrawList desktop_layer_;
    hui::gfx::DrawList desktop_cursor_layer_;
    float desktop_wheel_remainder_=0;
    float desktop_cursor_alpha_=0,desktop_cursor_glow_=0;
    struct DesktopLink { hui::gfx::Rect bounds;std::string url; };
    std::vector<DesktopLink> desktop_links_;
    enum class DesktopScrollTarget { content,credits,description };
    struct DesktopScrollArea { DesktopScrollTarget target;hui::gfx::Rect viewport,track;float maximum=0,position=0,minimum_thumb=32; };
    std::vector<DesktopScrollArea> desktop_scroll_areas_;
    bool desktop_scroll_dragging_=false;
    DesktopScrollTarget desktop_scroll_drag_target_=DesktopScrollTarget::content;
    float desktop_scroll_drag_offset_=0;
    void desktop_add_scroll_area(DesktopScrollTarget,hui::gfx::Rect viewport,hui::gfx::Rect track,float maximum,float position,float minimum_thumb=32);
    bool desktop_scroll_enabled(DesktopScrollTarget)const;
    bool handle_desktop_scrolling(hui::InputFrame&,hui::ui::Feedback&);
    std::string desktop_url_request_;
    std::size_t desktop_search_caret_=0;
    bool desktop_search_selection_=false;
    bool desktop_search_submit_rearm_=false;
    std::string desktop_search_observed_;
    struct DesktopControl { hui::gfx::Rect bounds;std::string label,key;int command=0;hui::ui::Button glyph=hui::ui::Button::cross,second=hui::ui::Button::none; std::string second_key{}; float scale=1; };
    std::vector<DesktopControl> desktop_controls()const;
    bool handle_desktop_input(hui::InputFrame&,hui::ui::Feedback&);
    bool handle_desktop_video(const hui::InputFrame&,hui::ui::Feedback&);
    bool handle_desktop_search(hui::InputFrame&,hui::ui::Feedback&);
    void draw_desktop_video(float x);
    hui::gfx::Rect desktop_search_button_bounds(int)const;
    void draw_desktop_chrome(hui::gfx::DrawList&);
    void render_desktop_chrome();
    void render_desktop_cursor();
    bool desktop_pointer_target(float x,float y)const;
    bool desktop_can_open_sign_in_browser(const media::Connection&)const;
    bool desktop_open_sign_in_browser(const media::Connection&);
    void draw_desktop_sign_in_browser(const media::Connection&,float x);
    void desktop_add_link(hui::gfx::Rect,const std::string&);
    void desktop_add_text_links(const std::string&,float x,float baseline,float size,hui::gfx::Rect clip,bool site_names=false);
    bool desktop_footer_input(hui::InputFrame&,hui::ui::Feedback&);
    int desktop_preference_count()const;
    int desktop_preference_setting(int row)const;
    const char* desktop_preference_label(int row)const;
#endif
    CollectionInstaller collection_installer_;
    CollectionStartupPresentation collection_presentation_;
    bool collection_pending_=false,collection_started_=false,collection_media_started_=false,collection_media_error_=false;
    float collection_elapsed_=0,collection_ready_elapsed_=0;
    int collection_phase_log_=-1,collection_progress_log_=-1;
    enum class CollectionRemovalState {idle,stopping_media,removing,failed};
    CollectionRemovalState collection_removal_state_=CollectionRemovalState::idle;
    bool collection_remove_dialog_=false;
    int collection_remove_focus_=0;
    float collection_removal_elapsed_=0;
    hui::tween::Spring collection_remove_open_;
    pthread_t collection_media_stop_thread_{};
    bool collection_media_stop_joinable_=false;
    std::atomic<bool> collection_media_stop_done_{false};
    bool collection_removal_active()const{return collection_removal_state_!=CollectionRemovalState::idle;}
    bool begin_collection_removal();
    void join_collection_media_stop();
    void handle_collection_removal(const hui::InputFrame&,hui::ui::Feedback&);
    void update_collection_removal(float);
    void draw_collection_removal();
    bool start_collection_media();
    void update_collection_startup(float);
    void handle_collection_startup(const hui::InputFrame&,hui::ui::Feedback&);
    void handle_language_choice(const hui::InputFrame&,hui::ui::Feedback&);
    CollectionInstallViewState collection_install_view_state()const;
    hui::gfx::Renderer renderer_;
    hui::gfx::Font regular_,bold_,display_,mono_,cjk_,unicode_;
    hui::ui::FontRef cjk_ref_,unicode_ref_;
    hui::ui::Fonts fonts_;
    hui::ui::ImageViewer viewer_;
    hui::gfx::DrawList background_,page_,overlay_,media_layer_,composition_;
    hui::gfx::Canvas composed_,previous_entry_,wall_;
    hui::gfx::DrawList wall_layer_,welcome_,experience_layer_;
    float wall_time_=-10;
    bool entry_snapshot_=false;
    hui::gfx::DrawList boot_;
    Catalog catalog_;
    Catalog history_catalog_;
    // The complete localised collection owns the source records. Rebuild the
    // filtered view only on input/locale changes, never while drawing a frame.
    Catalog history_catalog_all_;
    int culture_filter_=0;
    void rebuild_history_filter();
    int active_filter()const{return history_focus_?culture_filter_:filter_;}
    const char* active_filter_label()const;
    bool history_focus_=false;
    bool history_transition_=false;
    float history_direction_=1;
    int history_focus_index_=0;
    std::map<int,std::string> gaming_year_selection_,culture_year_selection_;
    hui::tween::Spring history_position_,history_emphasis_;
    void focus_history(bool);
    void move_history(int,hui::ui::Feedback&);
    void warm_history();
    void open_photo(hui::gfx::Rect);
    void draw_history_rail(float);
    void draw_history_page();
    hui::gfx::Rect history_image_bounds()const;
    media::RemoteCache cache_;
    media::Video video_;
    CultureAmbience culture_ambience_;
    CultureAudioRoute culture_audio_route_;
    bool culture_input_active_=true;
    void update_culture_ambience();
    void release_culture_ambience();
    ObjectScene object_;
    std::array<ObjectScene,2> prepared_objects_;
    std::array<std::string,2> prepared_paths_;
    bool prepared_programs_ready_=false;
    std::vector<std::string> large_model_paths_; // Known masters outside the neighbour-cache budget.
    std::array<unsigned,2> prepared_use_{};
    unsigned prepared_clock_=0;
    void retain_object();
    bool initialize_object_programs();
    bool warm_objects();
    std::string model_url_,model_path_;
    unsigned object_texture_=0;
    float object_angle_=0;
    float object_alpha_=0;
    float object_render_angle_=0,object_render_tilt_=0,object_render_zoom_=0;
    float object_render_clock_=0,object_frame_ms_=0,model_wait_=0;
    bool model_requested_=false;
    hui::gfx::Rect object_origin_{0,-9,1920,960};
    int object_render_width_=0,object_render_height_=0;
    std::map<std::string,float> image_fades_;
    std::map<std::string,float> image_wait_started_;
    hui::gfx::Color tone_=hui::gfx::Color::rgb(0xdc9b79);
    std::string root_,data_,initial_exhibit_,notice_;
    float notice_time_=0;
    float tactile_repeat_=0;
    std::vector<int> visible_;
    std::vector<std::string> nearby_covers_;
    int focus_=0,section_=0,filter_=0,tab_=0,setting_=0,image_index_=0,video_index_=0;
    int filter_notice_observed_=0;
    float filter_notice_time_=0;
    float year_notice_time_=0;
    float year_notice_age_=0;
    int year_notice_from_=0,year_notice_to_=0;
    int year_notice_displayed_=0;
    bool year_notice_tick_=false;
    void show_year_notice(int from,int to);
    void draw_filter_notice();
    bool detail_=false,gallery_=false,screening_=false,fullscreen_=false,settings_=false,credits_=false;
    bool film_captions_enabled_=true;
    bool chapters_=false,year_guide_=false;
    hui::ui::InputPrompt search_prompt_;
    bool search_page_=false;
    std::string search_query_;
    std::vector<SearchResult> search_results_;
    int search_focus_=0;
    hui::tween::Spring search_open_,search_position_;
    void open_search(hui::ui::Feedback&);
    bool handle_search(const hui::InputFrame&,hui::ui::Feedback&);
    void draw_search();
    std::string language_="en";
    int language_focus_=0;
    bool language_choice_=true,language_chosen_=false;
    void apply_language();
    bool dark_theme_=true,theme_chosen_=false,theme_choice_=true,theme_confirming_=false;
    float theme_confirm_progress_=0;
    hui::tween::Spring theme_mix_,language_selection_,theme_selection_,settings_scroll_,image_dialog_open_;
    bool image_dialog_=false,image_clear_confirm_=false;
    MuseumPalette colours()const{return museum_palette(theme_mix_.value);}
    bool onboarding_=true,onboarding_complete_=false,onboarding_leaving_=false;
    static constexpr int onboarding_cards_=6;
    int onboarding_step_=0;
    hui::tween::Spring onboarding_position_,onboarding_fade_;
    void draw_onboarding();
    std::vector<int> years_;
    int year_focus_=0;
    bool guide_experiences_=false;
    hui::tween::Spring guide_mode_;
    int experience_focus_=0,experience_index_=-1;
    float experience_description_scroll_=0,experience_description_max_=0,experience_description_clock_=0;
    hui::tween::Spring experience_position_,experience_open_,experience_intro_;
    bool experience_active_=false,experience_introduction_=true;
    float experience_progress_checkpoint_=0;
    bool experience_paused_=false;
    bool experience_completion_seen_=false;
    int experience_pause_selection_=0;
    hui::tween::Spring experience_pause_open_;
    bool experience_input_paused_=false,experience_rearm_=false;
    float target_refresh_hz_ = 60.f;
    bool motion_controls_=false,motion_calibrated_=false;
    std::array<float,3> motion_neutral_{};
    ExperienceAudio experience_audio_;
    std::unique_ptr<Study> study_,study_preview_;
    int study_preview_index_=-1;
    float study_preview_frame_time_=-1;
    void draw_study_preview(hui::gfx::DrawList&,int,hui::gfx::Rect);
    hui::gfx::Rect experience_origin_{132,310,1656,575};
    void open_experience(int,hui::gfx::Rect);
    bool handle_experience(const hui::InputFrame&,hui::ui::Feedback&);
    void draw_experience();
    void draw_experience_library(float x);
    hui::tween::Spring year_panel_,year_position_;
    void open_year_guide();
    void jump_today(hui::ui::Feedback&);
    void draw_year_guide();
    static constexpr float guide_sidebar_width_=736.f;
    float guide_sidebar_x()const{
        return canvas_bounds().x-guide_sidebar_width_*(1-std::clamp(year_panel_.value,0.f,1.f));
    }
    hui::gfx::Rect guide_preview_bounds()const{
        constexpr float width=1072.f;
        const auto canvas=canvas_bounds();
        const float left=canvas.x+guide_sidebar_width_;
        const float remaining=canvas.w-guide_sidebar_width_;
        return {left+(remaining-width)*.5f,142,width,796};
    }
    bool object_inspect_=false,connection_panel_=false;
    float object_zoom_=2,object_tilt_offset_=0;
    bool object_manual_=false;
    int output_width_=3840,output_height_=2160;
    hui::gfx::Rect canvas_bounds()const{
#if defined(MUSEUM_DESKTOP)
        const float left=desktop_canvas_left(output_width_,output_height_);
        return {left,0,1920-2*left,1080};
#else
        return {0,0,1920,1080};
#endif
    }
    float timeline_stop_x(float distance,bool culture)const{
        const float extra=(culture?170.f:190.f)*hui::tween::smoothstep(std::min(1.f,std::abs(distance)));
        float step=340.f;
#if defined(MUSEUM_DESKTOP)
        const float extension=-canvas_bounds().x;
        const float compact=std::clamp((960.f+extension-190.f-160.f)/3.f,280.f,340.f);
        step+=(compact-step)*std::min(1.f,extension/180.f);
#endif
        return 960.f+distance*step+(distance<0?-extra:extra);
    }
    static constexpr float options_panel_width(){return 810.f;}
    float options_panel_x()const{
        const auto canvas=canvas_bounds();
        return canvas.x+canvas.w-panel_.value*options_panel_width();
    }
    unsigned connection_qr_=0;
    std::string connection_qr_value_;
    int chapter_focus_=0;
    hui::tween::Spring chapter_marker_;
    bool reduced_=false,muted_=false,quit_=false,dirty_=false,ready_=false;
    float media_volume_=.6f;
    void adjust_media_volume(const hui::InputFrame&);
    float volume_=.48f,time_=0,dt_=0,fade_=1,idle_=0,save_delay_=0,scroll_max_=0;
    float master_volume_=1.f,sfx_volume_=1.f,culture_volume_=1.f;
    float pad_volume_=1.f;
    bool culture_audio_on_pad_=false;
    bool volumes_open_=false;
    int volume_focus_=0;
    float boot_time_=0;
    int boot_note_=0;
    hui::tween::Spring timeline_,scroll_,panel_,focus_line_;
    TimelineMotion timeline_motion_;
    hui::tween::Spring story_open_,gallery_open_,screening_open_,video_full_,object_open_;
    hui::gfx::Rect gallery_origin_{950,220,826,478},screening_origin_{950,220,826,478};
    struct StoryAction { hui::gfx::Rect bounds;int image=-1,video=-1; };
    std::vector<StoryAction> story_actions_;
    int story_action_=0;
    struct StoryCard {
        enum Kind { narrative, photograph, film, object, interactive, experience, soundtrack, sources };
        Kind kind=narrative;
        int paragraph=-1,image=-1,video=-1;
        std::string title,lead;
        int study_index=-1;
        int feature=-1; // Supplemental narrative; original parent text stays untouched.
        std::vector<int> continuation{}; // Source paragraphs sharing this illustrated scene.
        int music_room=-1; // Independent album; -1 retains the original single-room catalogue.
    };
    std::vector<StoryCard> story_cards_;
    int story_focus_=0;
    hui::tween::Spring story_position_,story_read_;
    bool story_expanded_=false,workshop_active_=false;
    CreditLayout story_credits_;
    std::vector<NarrativeLayout> story_text_;
    PixelWorkshop workshop_;
    void prepare_story();
    void compose_story_scenes();
    void move_story(int delta,hui::ui::Feedback&);
    bool story_object()const;
    float video_frame_alpha_=0;
    float film_progress_age_=0;
    const char* film_audio_hint()const;
    float gallery_overlay_age_=0;int gallery_overlay_image_=-1;hui::tween::Spring gallery_labels_;
    std::array<double,3> interface_stage_ms_{}; // CPU submission timings, not GPU completion.
    bool playlist_active_=false,playlist_completed_=false,playlist_closing_=false;
    int playlist_display_index_=0,playlist_display_music_room_=-1;
    int playlist_selection_=0,playlist_playing_=-1;
    int playlist_hover_=-1;
    int playlist_music_room_=-1;
    bool story_soundtrack()const;
    const Soundtrack* current_soundtrack()const;
    struct PlaylistLayout { float title_size=54,artist_size=25,rows_y=360;int visible=7,first=0; };
    PlaylistLayout playlist_layout(const Entry&,const Soundtrack&)const;
    void play_playlist(int index);
    void stop_playlist();
    void update_playlist();
    bool handle_playlist(const hui::InputFrame&,hui::ui::Feedback&);
    void draw_playlist(hui::gfx::Rect,bool active,int room_index=-1);
    hui::gfx::Rect playlist_frame()const;
    bool story_sources_=false,screening_from_story_=false,seek_first_video_=false,seek_sources_=false;
    float story_video_anchor_=0,sources_anchor_=0;
    hui::tween::Spring sources_open_,media_hints_,credits_open_,credits_scroll_;
    float credits_scroll_max_=0;
    std::vector<std::string> feature_resources_lines_;
    std::string feature_resources_text_;
    void load_runtime_credits();
    int date_year_=0,date_month_=0,date_day_=0;
    std::array<int,2> today_cursor_{{-1,-1}};
    std::array<bool,2> filter_trigger_down_{{false,false}};
    void set_today_date(int year,int month,int day);
    void refresh_today_date();
    void change_filter(int delta,hui::ui::Feedback&);
    bool anniversary_=false;
    const Entry* current()const;
    int story_cover_index(const Entry&)const;
    const Entry& story_source(const Entry&)const;
    void rebuild(bool notify=true);
    void move(int delta,hui::ui::Feedback&);
    void chapter(int delta,hui::ui::Feedback&);
    void changed(bool timeline_navigation=false);
    void load_settings();
    void save_settings();
    bool font(const std::string&,hui::gfx::Font&,hui::ui::FontRef&);
    void logo(hui::gfx::DrawList&,float x,float y,float size,hui::gfx::Color)const;
    void heading(hui::gfx::DrawList&,const std::string&,float x,float baseline,float size,float width,hui::gfx::Color)const;
    void image(hui::gfx::DrawList&,const Image&,hui::gfx::Rect,bool fit=true,float alpha=1);
    const std::string& image_url(const Image& image)const{return theme_mix_.value>=.5f&&!image.dark_url.empty()?image.dark_url:image.url;}
    void draw_header();
    void draw_timeline();
    void draw_chapters();
    void draw_object();
    void draw_connection();
    void draw_boot();
    void draw_gallery();
    void snapshot_current();
    const Entry* chapter_object()const;
    void draw_detail();
    void draw_screening();
    void draw_preferences();
    void draw_credits();
    void hints(const std::vector<hui::ui::Hint>&);
    void prepare_gallery(bool reset=true);
    bool guide_trophies_=false;
    std::unique_ptr<Trophies> trophies_;
    PinScene trophy_pin_scene_;
    hui::ps5::TrophyNotifications trophy_notifications_;
    std::string trophy_media_session_;
    double trophy_media_previous_=0,trophy_media_played_=0;
    void initialize_trophies();
    void update_trophies();
    std::vector<TrophyUnlock> trophy_fallback_queue_;
    TrophyUnlock trophy_fallback_current_;
    float trophy_fallback_time_=0;
    bool trophy_fallback_sound_=false;
    void draw_trophy_fallback();
    int trophy_focus_=0;
    bool trophy_expanded_=false,trophy_pin_open_=false;
    float trophy_focus_time_=0,trophy_pin_yaw_=0,trophy_pin_pitch_=0,trophy_pin_zoom_=1,trophy_pin_pan_y_=0,pin_onboarding_time_=0;
    float trophy_pin_haptic_wait_=0;
    std::array<unsigned,13> intro_m_colours_{{0,1,2,3,4,5,6,7,0,1,2,3,4}};
    unsigned intro_m_random_=0,intro_m_from_=0,intro_m_to_=0;
    int intro_m_active_=-1,intro_m_previous_=-1;
    float intro_m_fade_=0;
    hui::tween::Spring trophy_position_;
    TrophyPinRenderer trophy_pin_renderer_;
#if defined(MUSEUM_CURATOR_PREVIEW)
    bool trophy_curator_preview_=true;
#else
    bool trophy_curator_preview_=false;
#endif
    void draw_trophy_library();
    void draw_trophy_badge(hui::gfx::DrawList&,const std::string&,float,float,float,bool);
    void draw_trophy_detail();
    void draw_trophy_pin_viewer();
};
}
