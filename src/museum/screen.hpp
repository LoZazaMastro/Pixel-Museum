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
#include <map>
#include <array>
#include <functional>
namespace museum {
class Screen {
    friend struct ScreenInspection;
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
    void set_refresh_hz(float hz) { target_refresh_hz_ = hz == 120.f ? 120.f : 60.f; }
    bool motion_controls()const{return experience_active_&&!experience_paused_&&!experience_introduction_&&study_&&study_->motion_controls();}
    bool wants_quit()const{return quit_;}
    int take_startup_note(int* pixel_ordinal=nullptr);
    Catalog& catalog(){return catalog_;}
    using TrophyPinRenderer=std::function<unsigned(const TrophyView&,int,int,float,float,float,float)>;
    void set_trophy_pin_renderer(TrophyPinRenderer render){trophy_pin_renderer_=std::move(render);}
    void set_trophy_curator_preview(bool value){trophy_curator_preview_=value;}
    bool trophy_curator_preview()const{return trophy_curator_preview_;}
private:
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
    bool object_inspect_=false,connection_panel_=false;
    float object_zoom_=2,object_tilt_offset_=0;
    bool object_manual_=false;
    int output_width_=3840,output_height_=2160;
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
    float gallery_overlay_age_=0;int gallery_overlay_image_=-1;hui::tween::Spring gallery_labels_;
    std::array<double,3> interface_stage_ms_{}; // CPU submission timings, not GPU completion.
    bool playlist_active_=false,playlist_completed_=false,playlist_closing_=false;
    int playlist_display_index_=0,playlist_display_music_room_=-1;
    int playlist_selection_=0,playlist_playing_=-1;
    int playlist_music_room_=-1;
    bool story_soundtrack()const;
    const Soundtrack* current_soundtrack()const;
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
