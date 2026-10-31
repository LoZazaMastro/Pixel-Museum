// Original source stories and connected editorial cards share one carousel.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "host/behavior.hpp"
#include <algorithm>
#include <cstdio>
#include <set>
#include "third_party/nlohmann/json.hpp"
namespace museum {
bool ScreenInspection::verify_search(Screen&s){
    s.language_="en";s.apply_language();
    s.onboarding_=false;s.boot_time_=5;s.settings_=s.credits_=s.year_guide_=false;s.preview(0);
    hui::ui::Feedback feedback;hui::InputFrame input;input.connected=true;s.open_year_guide();
    input.pressed=hui::action_bit(hui::Action::touch);s.handle(input,feedback);
    if(!s.search_prompt_.is_open()||!s.year_guide_)return false;
    s.search_prompt_.field.set_text("1989");input.pressed=hui::action_bit(hui::Action::menu);s.handle(input,feedback);
    if(!s.search_page_||s.search_prompt_.is_open()||s.year_guide_||s.search_results_.empty())return false;
    bool gaming=false,culture=false;int previous=0;
    for(const auto&result:s.search_results_){const auto&e=(result.culture?s.history_catalog_:s.catalog_).entries[size_t(result.index)];gaming|=!result.culture;culture|=result.culture;const int day=chronology_day(e);if(day<previous)return false;previous=day;}
    if(!gaming||!culture)return false;
    for(size_t n=0;n<s.search_results_.size();++n)if(s.search_results_[n].culture){
        const auto id=s.history_catalog_.entries[size_t(s.search_results_[n].index)].id;s.search_focus_=int(n);input.pressed=hui::action_bit(hui::Action::confirm);s.handle(input,feedback);
        if(!s.history_focus_||s.current()->id!=id||s.detail_||s.search_page_)return false;break;
    }
    s.search_open_.snap(0);s.search_prompt_.dismiss();s.search_page_=true;
    for(size_t n=0;n<s.search_results_.size();++n)if(!s.search_results_[n].culture){
        const auto id=s.catalog_.entries[size_t(s.search_results_[n].index)].id;s.search_focus_=int(n);input.pressed=hui::action_bit(hui::Action::confirm);s.handle(input,feedback);
        if(s.history_focus_||s.current()->id!=id||!s.detail_||s.search_page_)return false;break;
    }
    s.detail_=false;s.search_page_=true;s.search_focus_=0;
    for(size_t n=0;n<s.search_results_.size();++n)if(s.search_results_[n].culture){s.search_focus_=int(n);break;}
    s.search_position_.snap(float(s.search_focus_));s.search_open_.snap(1);
    std::puts("Search UI PASS: second touchpad opens keyboard, submit orders both timelines, culture and game results open the exact selected exhibit.");return true;
}
bool ScreenInspection::verify_story_scenes(Screen&s){
    const auto visible=s.visible_;const int focus=s.focus_;unsigned scenes=0,paragraphs=0,unillustrated=0;
    nlohmann::json quality={{"scope","Actual composed story scenes; gallery, credits, music and experiences do not count as narrative completion."},{"entries",nlohmann::json::array()}};
    unsigned complete=0;
    for(size_t entry=0;entry<s.catalog_.entries.size();++entry){
        const auto&e=s.catalog_.entries[entry];if(e.calendar_only&&!e.linked_exhibit_id.empty())continue;
        s.visible_={int(entry)};s.focus_=0;s.prepare_story();
        std::set<std::string> image_keys;
        if(!e.images.empty())image_keys.insert(s.cache_.image_identity(e.images[size_t(std::clamp(e.preferred_image,0,int(e.images.size())-1))].url));
        for(const auto&card:s.story_cards_)if(card.image>=0){
            const auto identity=s.cache_.image_identity(e.images[size_t(card.image)].url);
            if(!image_keys.insert(identity).second){std::fprintf(stderr,"Repeated article photograph: %s\n",e.id.c_str());return false;}
        }
        for(int feature=-1;feature<int(e.editorial_features.size());++feature){
            const auto&body=feature<0?e.body:e.editorial_features[size_t(feature)].body;
            std::vector<int> seen;seen.reserve(body.size());
            for(const auto&card:s.story_cards_)if(card.feature==feature&&card.paragraph>=0){
                ++scenes;if(card.image<0){++unillustrated;std::fprintf(stderr,"Editorial image still needed: %s/feature%d/paragraph%d\n",e.id.c_str(),feature,card.paragraph);}
                else if(card.image>=int(e.images.size()))return false;
                seen.push_back(card.paragraph);seen.insert(seen.end(),card.continuation.begin(),card.continuation.end());
            }
            if(seen.size()!=body.size()){std::fprintf(stderr,"Story paragraph count changed: %s feature%d\n",e.id.c_str(),feature);return false;}
            for(size_t n=0;n<seen.size();++n)if(seen[n]!=int(n)){std::fprintf(stderr,"Story prose reordered or repeated: %s/%zu\n",e.id.c_str(),n);return false;}
            paragraphs+=unsigned(body.size());
        }
        unsigned narrative=0,illustrated=0,photo_only=0;
        for(const auto&card:s.story_cards_){
            if(card.paragraph>=0&&(card.kind==Screen::StoryCard::narrative||card.kind==Screen::StoryCard::film)){
                ++narrative;if(card.image>=0||(card.kind==Screen::StoryCard::film&&card.video>=0))++illustrated;
            }else if(card.kind==Screen::StoryCard::photograph)++photo_only;
        }
        const bool ready=narrative>=2&&illustrated==narrative;complete+=unsigned(ready);
        quality["entries"].push_back({{"id",e.id},{"title",e.title},{"narrative_scenes",narrative},{"illustrated_narrative_scenes",illustrated},{"standalone_photographs",photo_only},{"meets_multi_card_illustrated_requirement",ready}});
    }
    s.visible_=visible;s.focus_=focus;s.prepare_story();
    quality["complete_articles"]=complete;quality["incomplete_articles"]=quality["entries"].size()-complete;
    hui::save::write_atomic("build/research/narrative-card-completeness.json",quality.dump(2));
    std::printf("Story composition: %u scenes retain all %u source paragraphs in original order; no repeated image content. Editorial scenes still needing distinct imagery: %u\n",scenes,paragraphs,unillustrated);return true;
}
bool ScreenInspection::verify_feature_cards(Screen&s,unsigned framebuffer,int width,int height){
    unsigned features=0,cards=0;
    for(const auto&e:s.catalog_.entries)for(const auto&feature:e.editorial_features){
        ++features;cards+=unsigned(feature.body.size());
        if(feature.body.size()!=feature.story_headings.size()||feature.body.empty()||feature.sources.empty())return false;
        for(int index:feature.image_indices)if(index<0||index>=int(e.images.size()))return false;
    }
    if(features!=91||cards!=364){std::fprintf(stderr,"Connected feature inventory: %u features/%u cards, expected91/364\n",features,cards);return false;}
    const bool dark=s.dark_theme_;s.dark_theme_=true;s.theme_mix_.snap(1);
    s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.settings_=s.credits_=false;s.panel_.snap(0);s.year_guide_=false;s.year_panel_.snap(0);
    unsigned researched=0;
    for(const auto&parent:s.catalog_.entries){
        if(!parent.explicit_story_media_only)continue;
        ++researched;s.select(parent.id);s.preview(1);
        for(const auto&card:s.story_cards_)if(card.feature<0&&card.paragraph>=0&&card.image>=0){
            if(parent.images[size_t(card.image)].story_paragraph>=0&&parent.images[size_t(card.image)].story_paragraph!=card.paragraph&&std::find(card.continuation.begin(),card.continuation.end(),parent.images[size_t(card.image)].story_paragraph)==card.continuation.end()){
                std::fprintf(stderr,"Unreviewed positional media mapping: %s\n",parent.id.c_str());return false;
            }
        }
        for(size_t n=0;n<parent.images.size();++n){
            const auto identity=s.cache_.image_identity(parent.images[n].url);
            if(identity==s.cache_.image_identity(parent.images[size_t(parent.preferred_image)].url))continue;
            const bool nested=std::any_of(parent.editorial_features.begin(),parent.editorial_features.end(),[n](const auto&feature){return std::find(feature.image_indices.begin(),feature.image_indices.end(),int(n))!=feature.image_indices.end();});
            if(!nested&&std::none_of(s.story_cards_.begin(),s.story_cards_.end(),[&](const auto&card){return card.image>=0&&s.cache_.image_identity(parent.images[size_t(card.image)].url)==identity;})){
                std::fprintf(stderr,"Detached gallery artefact disappeared: %s\n",parent.id.c_str());return false;
            }
        }
        s.preview(0);
    }
    if(researched<45){std::fputs("Researched canonical parser policy missing\n",stderr);return false;}
    for(const auto&parent:s.catalog_.entries){
        if(parent.editorial_features.empty())continue;
        const auto id=parent.id;
        s.select(id);if(!s.current()||s.current()->id!=id)return false;
        const auto*e=s.current();const auto original=e->body;
        for(std::size_t wanted=0;wanted<e->editorial_features.size();++wanted){
        s.preview(1);
        const auto first=std::find_if(s.story_cards_.begin(),s.story_cards_.end(),[wanted](const auto&c){return c.feature==int(wanted)&&c.paragraph>=0;});
        if(first==s.story_cards_.end())return false;
        const auto index=int(first-s.story_cards_.begin());s.story_focus_=index;s.story_position_.snap(float(index));s.story_open_.snap(1);
        s.story_expanded_=false;s.story_read_.snap(0);
        if(first->image>=0&&!e->editorial_features[size_t(first->feature)].image_indices.empty()&&std::find(e->editorial_features[size_t(first->feature)].image_indices.begin(),e->editorial_features[size_t(first->feature)].image_indices.end(),first->image)==e->editorial_features[size_t(first->feature)].image_indices.end())return false;
        hui::ui::Feedback feedback;hui::InputFrame input;input.connected=true;input.pressed=hui::action_bit(hui::Action::west);s.handle(input,feedback);
        if(!s.story_expanded_||s.current()->body!=original)return false;
        s.story_read_.snap(1);s.draw(width,height,framebuffer);
        if(glGetError()!=GL_NO_ERROR)return false;
        s.preview(0);
        }
    }
    for(const char*id:{"feature-mabel-addis-classroom","feature-ed-smith-apf","feature-umurangi-looking","feature-riven-performance-audio","feature-kondo-functional-music","feature-kazuko-shibuya-pixel-art","feature-maestro-nobuo-uematsu","feature-akira-yamaoka-noise","feature-jessica-curry-worlds","feature-berlin-game-museum","feature-games-in-museums"}){
        s.select(id);if(!s.current()||s.current()->id!=id)return false;
        if((std::string(id)=="feature-maestro-nobuo-uematsu"||std::string(id)=="feature-akira-yamaoka-noise"||std::string(id)=="feature-jessica-curry-worlds")&&s.current()->images.empty())return false;
        s.preview(1);s.story_open_.snap(1);s.draw(width,height,framebuffer);
        if(glGetError()!=GL_NO_ERROR)return false;
        s.preview(0);
    }
    s.select("wikipedia-453246");s.preview(1);
    const auto playable=std::find_if(s.story_cards_.begin(),s.story_cards_.end(),[](const auto&card){return card.kind==Screen::StoryCard::experience;});
    if(playable==s.story_cards_.end())return false;
    s.story_focus_=int(playable-s.story_cards_.begin());s.story_position_.snap(float(s.story_focus_));s.story_open_.snap(1);
    s.draw(width,height,framebuffer);
    if(!s.current()||s.current()->id!="wikipedia-453246"||s.study_preview_index_<0||
       study_catalog()[size_t(s.study_preview_index_)].entry_id!=s.current()->id||glGetError()!=GL_NO_ERROR)return false;
    s.dark_theme_=dark;s.theme_mix_.snap(dark?1.f:0.f);
    std::printf("Connected editorial:%ufeatures/%ucards, parent prose preserved, gallery indices and production reading renders passed at%dx%d\n",features,cards,width,height);
    return true;
}
}
