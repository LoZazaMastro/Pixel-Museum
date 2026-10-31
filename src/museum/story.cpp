// Pixel Museum - a collection explored as a sequence of living exhibit cards.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "museum/study_controls.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cctype>
#include <limits>
#include <set>
namespace museum {
using namespace hui;
using gfx::Color;using gfx::Rect;using gfx::Align;
namespace {
std::string authored_heading(const std::string&heading){
    std::string key;for(unsigned char c:heading)if(!std::isspace(c))key+=char(std::tolower(c));
    if(key=="fromthereferencecollection"||key=="insidethecollection")return {};
    return heading;
}
Rect fit_image(Rect box,const media::Asset&asset){
    if(asset.width<=0||asset.height<=0)return box;
    const float aspect=float(asset.width)/asset.height;
    if(box.w/box.h>aspect){const float width=box.h*aspect;box.x+=(box.w-width)/2;box.w=width;}
    else{const float height=box.w/aspect;box.y+=(box.h-height)/2;box.h=height;}
    return box;
}

}
const Entry& Screen::story_source(const Entry&entry)const{
    const auto*e=&entry;
    // Different dated stops may explicitly share one complete story. Their
    // timeline covers stay independent, while its card composition reserves
    // the canonical portrait. Refuse mismatched mappings rather than silently
    // reserving an unrelated image from another article.
    if(!history_focus_&&!e->story_entry_id.empty())if(const auto*canonical=catalog_.find_entry(e->story_entry_id)){
        bool same=canonical!=e&&canonical->body==e->body&&canonical->story_headings==e->story_headings&&canonical->images.size()==e->images.size();
        for(size_t n=0;same&&n<e->images.size();++n)same=canonical->images[n].url==e->images[n].url&&canonical->images[n].story_paragraph==e->images[n].story_paragraph;
        if(same)return *canonical;
    }
    return entry;
}
int Screen::story_cover_index(const Entry&entry)const{return story_source(entry).preferred_image;}
void Screen::prepare_story(){
    story_credits_.clear();story_text_.clear();story_cards_.clear();story_focus_=0;story_position_.snap(0);story_read_.snap(0);story_expanded_=false;workshop_active_=false;workshop_.reset();
    const auto*e=current();if(!e)return;
    const auto&shared=story_source(*e);
    const bool awards=shared.id.rfind("the-game-awards-",0)==0&&shared.body.size()>2;
    std::vector<bool>used(e->images.size(),false);
    const int story_cover=story_cover_index(*e);
    // The cover introduces the exhibit outside the story. Reserve it before
    // matching paragraphs so it cannot hide a distinct researched p0 image.
    if(!used.empty()){
        const auto cover=cache_.image_identity(e->images[size_t(std::clamp(story_cover,0,int(used.size())-1))].url);
        for(size_t n=0;n<used.size();++n)if(e->images[n].story_paragraph<0&&cache_.image_identity(e->images[n].url)==cover)used[n]=true;
    }
    for(const auto&feature:e->editorial_features)for(int index:feature.image_indices)if(index>=0&&index<int(used.size()))used[size_t(index)]=true;
    // A video's preview belongs to its player, never a positional prose image.
    if(!awards)for(const auto&film:e->videos)if(!film.poster_url.empty())for(size_t n=0;n<e->images.size();++n)if(e->images[n].url==film.poster_url)used[n]=true;
    const auto poster=[&](size_t video,int fallback){
        if(video<e->videos.size()&&!e->videos[video].poster_url.empty())for(size_t n=0;n<e->images.size();++n)if(e->images[n].url==e->videos[video].poster_url){
            if(fallback>=0&&fallback!=int(n))used[size_t(fallback)]=false;
            used[n]=true;return int(n);
        }
        const int image=fallback>=0?fallback:e->images.empty()?-1:e->preferred_image;
        if(image>=0)used[size_t(image)]=true;
        return image;
    };
    // A film illustrates an existing paragraph. Explicit editorial placements
    // win; the first unplaced film accompanies the introduction. Additional
    // films require distinct editorial placements rather than guessed topics.
    std::vector<int> paragraph_films(e->body.size(),-1);
    if(!awards&&!paragraph_films.empty()){
        for(size_t v=0;v<e->videos.size();++v){
            const int p=e->videos[v].story_paragraph;
            if(p>=0&&size_t(p)<paragraph_films.size()&&paragraph_films[size_t(p)]<0)paragraph_films[size_t(p)]=int(v);
        }
        for(size_t v=0;v<e->videos.size();++v){
            const int p=e->videos[v].story_paragraph;
            if(p<0||size_t(p)>=paragraph_films.size()){
                if(paragraph_films[0]<0)paragraph_films[0]=int(v);
                break;
            }
        }
    }
    if(!e->models.empty())story_cards_.push_back({StoryCard::object,-1,-1,-1,e->models[0].display_caption.empty()?"An object made for play":e->models[0].display_caption,e->summary});
    for(size_t p=0;p<e->body.size();++p){
        int photo=-1;
        // A researched replacement narrative cannot inherit an old gallery's
        // positional associations. Unmapped artefacts remain in the gallery.
        for(size_t n=0;n<e->images.size();++n)if(!used[n]&&(e->images[n].story_paragraph>=0?e->images[n].story_paragraph==int(p):!e->explicit_story_media_only&&n==p)){photo=int(n);used[n]=true;break;}
        // Each annual awards chapter is independently addressable, including
        // the selected ceremony whose artwork also introduces the exhibit.
        if(awards&&p>=2)for(size_t n=0;n<e->images.size();++n)if(e->images[n].story_paragraph==int(p)){photo=int(n);used[n]=true;break;}
        const std::string heading=p<e->story_headings.size()?authored_heading(e->story_headings[p]):p==0?authored_heading(e->subtitle):std::string{};
        if(awards&&p>=2&&photo<0&&heading.size()>=4){const auto year=heading.substr(0,4);for(const auto&film:e->videos)if(film.title.rfind(year,0)==0&&!film.poster_url.empty())for(size_t n=0;n<e->images.size();++n)if(e->images[n].url==film.poster_url){photo=int(n);used[n]=true;break;}}

        const int film=paragraph_films[p];
        if(film>=0){
            story_cards_.push_back({StoryCard::film,int(p),poster(size_t(film),photo),film,heading,{}});
        }else story_cards_.push_back({StoryCard::narrative,int(p),photo,-1,heading,{}});
    }
    if(e->body.empty())for(size_t v=0;v<e->videos.size();++v)story_cards_.push_back({StoryCard::film,-1,poster(v,-1),int(v),e->videos[v].title,e->videos[v].caption});
    for(size_t n=0;n<e->images.size();++n)if(!used[n])story_cards_.push_back({StoryCard::photograph,-1,int(n),-1,e->images[n].title,""});
    for(size_t f=0;f<e->editorial_features.size();++f){
        const auto&feature=e->editorial_features[f];
        std::vector<bool>shown(feature.image_indices.size(),false);
        for(size_t p=0;p<feature.body.size();++p){
            int photo=-1;
            for(size_t n=0;n<feature.image_indices.size();++n){const int index=feature.image_indices[n];if(!shown[n]&&e->images[size_t(index)].story_paragraph==int(p)){photo=index;shown[n]=true;break;}}
            StoryCard card{StoryCard::narrative,int(p),photo,-1,authored_heading(feature.story_headings[p]),{}};card.feature=int(f);story_cards_.push_back(std::move(card));
        }
        for(size_t n=0;n<feature.image_indices.size();++n)if(!shown[n]){const int index=feature.image_indices[n];StoryCard card{StoryCard::photograph,-1,index,-1,e->images[size_t(index)].title,""};card.feature=int(f);story_cards_.push_back(std::move(card));}
    }
    compose_story_scenes();
    for(size_t n=0;n<study_catalog().size();++n){const auto&info=study_catalog()[n];if(info.entry_id==shared.id){
        StoryCard card{StoryCard::experience,-1,-1,-1,info.title,info.explanation};card.study_index=int(n);story_cards_.push_back(std::move(card));
    }}
    if(!e->soundtrack_rooms.empty()){
        for(size_t n=0;n<e->soundtrack_rooms.size();++n){
            const auto&room=e->soundtrack_rooms[n];if(room.tracks.empty())continue;
            char invitation[1024];ui::format(invitation,"Listen to the music of %s",room.composer.c_str());
            StoryCard card{StoryCard::soundtrack,-1,-1,-1,"Music",std::string(invitation)+"\n"+shared.title};
            card.music_room=int(n);story_cards_.push_back(std::move(card));
        }
    }else if(!e->soundtrack.tracks.empty()){char invitation[1024];ui::format(invitation,"Listen to the music of %s",e->soundtrack.composer.c_str());story_cards_.push_back({StoryCard::soundtrack,-1,-1,-1,"Music",std::string(invitation)+"\n"+shared.title});}
}
void Screen::compose_story_scenes(){
    const auto*e=current();if(!e)return;
    std::vector<bool> remove(story_cards_.size(),false);
    const bool awards=e->id.rfind("the-game-awards-",0)==0&&e->body.size()>2;
    const auto image_key=[&](int index){return index>=0&&index<int(e->images.size())?cache_.image_identity(e->images[size_t(index)].url):std::string{};};
    std::set<std::string> scene_images;
    // The main-block artwork already introduces the exhibit. Internal cards
    // must add distinct material, even when aliases point at the same pixels.
    if(!e->images.empty()){
        const int cover=std::clamp(story_cover_index(*e),0,int(e->images.size())-1);
        if(e->images[size_t(cover)].story_paragraph<0)scene_images.insert(image_key(cover));
    }
    // Imported galleries can contain the same pixels under different URLs,
    // or attach one photograph to both the parent and a supplemental feature.
    // Keep the first illustrated occurrence; preserve all later prose.
    for(auto&card:story_cards_){
        if(card.kind==StoryCard::photograph||card.image<0||(awards&&card.feature<0&&card.paragraph>=2))continue;
        // An explicit paragraph binding remains valid even when its pixels
        // also introduce the exhibit or illustrate a related chapter.
        if(!scene_images.insert(image_key(card.image)).second&&e->images[size_t(card.image)].story_paragraph<0)card.image=-1;
    }
    // Existing legacy galleries already belong to their article. Spread those
    // photographs across complete paragraph boundaries before joining prose.
    // Curated media mappings remain an editorial decision, never a guess here.
    if(!awards&&!e->explicit_story_media_only){
        for(int feature=-1;feature<int(e->editorial_features.size());++feature){
            std::vector<size_t> paragraphs;
            std::vector<std::pair<size_t,int>> photos;
            std::set<std::string> gallery_images;
            std::vector<size_t> weights;
            std::set<int> anchors;
            const auto&body=feature<0?e->body:e->editorial_features[size_t(feature)].body;
            std::set<std::string> reserved;
            if(!e->images.empty())reserved.insert(image_key(std::clamp(story_cover_index(*e),0,int(e->images.size())-1)));
            for(const auto&card:story_cards_)if(card.image>=0&&(card.kind==StoryCard::film||e->images[size_t(card.image)].story_paragraph>=0))reserved.insert(image_key(card.image));
            for(size_t n=0;n<story_cards_.size();++n){
                auto&card=story_cards_[n];if(card.feature!=feature)continue;
                if(card.kind==StoryCard::narrative&&card.image>=0&&!reserved.count(image_key(card.image))){
                    if(gallery_images.insert(image_key(card.image)).second)photos.push_back({n,card.image});
                    scene_images.erase(image_key(card.image));card.image=-1;
                }
                if(card.paragraph>=0&&(card.kind==StoryCard::narrative||card.kind==StoryCard::film)){
                    if(card.image>=0||card.kind==StoryCard::film)anchors.insert(int(paragraphs.size()));
                    paragraphs.push_back(n);weights.push_back(body[size_t(card.paragraph)].size());
                }else if(card.kind==StoryCard::photograph&&card.image>=0){
                    const auto&photo=e->images[size_t(card.image)];
                    if(photo.story_paragraph>=0||reserved.count(image_key(card.image)))continue;
                    bool poster=false;for(const auto&film:e->videos)if(!film.poster_url.empty()&&film.poster_url==photo.url){poster=true;break;}
                    if(!poster&&gallery_images.insert(image_key(card.image)).second)photos.push_back({n,card.image});
                }
            }
            if(paragraphs.empty()||photos.empty())continue;
            std::vector<size_t> prefix(weights.size()+1,0);
            for(size_t p=0;p<weights.size();++p)prefix[p+1]=prefix[p]+weights[p];
            std::vector<int> chosen;
            const auto score=[&](const std::set<int>&points){
                size_t worst=0;long double square=0;int previous=0;
                for(int point:points){if(point==0)continue;const size_t bytes=prefix[size_t(point)]-prefix[size_t(previous)];worst=std::max(worst,bytes);square+=static_cast<long double>(bytes)*bytes;previous=point;}
                const size_t bytes=prefix.back()-prefix[size_t(previous)];worst=std::max(worst,bytes);square+=static_cast<long double>(bytes)*bytes;
                return std::pair<size_t,long double>{worst,square};
            };
            while(chosen.size()<photos.size()&&anchors.size()<paragraphs.size()){
                int best=-1;std::pair<size_t,long double> best_score{std::numeric_limits<size_t>::max(),std::numeric_limits<long double>::max()};
                if(anchors.empty())best=0;
                else for(size_t p=1;p<paragraphs.size();++p)if(!anchors.count(int(p))){
                    auto trial=anchors;trial.insert(int(p));const auto value=score(trial);
                    if(value<best_score){best=int(p);best_score=value;}
                }
                if(best<0)break;anchors.insert(best);chosen.push_back(best);
            }
            std::sort(chosen.begin(),chosen.end());
            for(size_t n=0;n<chosen.size();++n){
                auto&card=story_cards_[paragraphs[size_t(chosen[n])]];const auto photo=photos[n];
                card.image=photo.second;scene_images.insert(image_key(photo.second));
                if(story_cards_[photo.first].kind==StoryCard::photograph)remove[photo.first]=true;
            }
        }
    }
    // Main chapters are authored navigation stops. An image gap must never
    // silently collapse their headings and text into a different chapter.
    // Supplemental material keeps its own grouping within the same feature.
    for(int feature=-1;feature<int(e->editorial_features.size());++feature){
        if(feature<0)continue;
        std::vector<size_t> paragraphs;
        for(size_t n=0;n<story_cards_.size();++n){const auto&c=story_cards_[n];if(c.feature==feature&&c.paragraph>=0&&(c.kind==StoryCard::narrative||c.kind==StoryCard::film))paragraphs.push_back(n);}
        if(paragraphs.empty())continue;
        bool illustrated=false;for(size_t n:paragraphs)if(story_cards_[n].image>=0||story_cards_[n].kind==StoryCard::film)illustrated=true;
        if(!illustrated){
            int image=e->images.empty()?-1:e->preferred_image;
            if(feature>=0&&!e->editorial_features[size_t(feature)].image_indices.empty())image=e->editorial_features[size_t(feature)].image_indices[0];
            if(image>=0&&scene_images.insert(image_key(image)).second)story_cards_[paragraphs[0]].image=image;
        }
        size_t previous=story_cards_.size();std::vector<size_t> opening;
        for(size_t n:paragraphs){
            auto&c=story_cards_[n];const bool anchor=c.image>=0||c.kind==StoryCard::film;
            if(anchor){
                // A partial, explicitly curated article can retain a genuine
                // opening image gap instead of moving a later artifact back.
                const bool explicitly_placed_film=c.kind==StoryCard::film&&c.video>=0&&size_t(c.video)<e->videos.size()&&e->videos[size_t(c.video)].story_paragraph>=0;
                if(previous==story_cards_.size()&&!opening.empty()&&!e->preserve_unillustrated_opening&&!explicitly_placed_film){
                    const size_t first=opening.front();const int image=c.image,video=c.video;const auto kind=c.kind;
                    auto&start=story_cards_[first];start.image=image;start.video=video;start.kind=kind;
                    for(size_t p=1;p<opening.size();++p){start.continuation.push_back(story_cards_[opening[p]].paragraph);remove[opening[p]]=true;}
                    start.continuation.push_back(c.paragraph);remove[n]=true;previous=first;opening.clear();
                }else previous=n;
            }else if(previous<story_cards_.size()){
                story_cards_[previous].continuation.push_back(c.paragraph);remove[n]=true;
            }else opening.push_back(n);
        }
    }
    std::vector<StoryCard> scenes;scenes.reserve(story_cards_.size());
    for(size_t n=0;n<story_cards_.size();++n){
        if(remove[n])continue;
        auto&c=story_cards_[n];
        // Unassigned photographs remain available in the full-resolution gallery.
        // Story cards pair the existing narrative with meaningful media instead
        // of appending empty image-only chapters.
        if(c.kind==StoryCard::photograph)continue;
        scenes.push_back(std::move(c));
    }
    story_cards_=std::move(scenes);
    // A chapter always retains a real illustration from its own exhibit.
    // Prefer unused related photographs over covers and video thumbnails.
    // Sparse galleries can reuse their own material; they never borrow an
    // unrelated image or silently turn a chapter into a blank text panel.
    std::vector<unsigned> image_uses(e->images.size(),0);
    for(const auto&card:story_cards_)if(card.image>=0&&card.image<int(image_uses.size()))++image_uses[size_t(card.image)];
    for(auto&card:story_cards_){
        if(card.image>=0||(card.kind!=StoryCard::narrative&&card.kind!=StoryCard::film))continue;
        const auto&feature=card.feature>=0?e->editorial_features[size_t(card.feature)].image_indices:std::vector<int>{};
        int best=-1;unsigned best_score=std::numeric_limits<unsigned>::max();
        for(size_t n=0;n<e->images.size();++n){
            bool video_poster=false;for(const auto&film:e->videos)if(film.poster_url==e->images[n].url){video_poster=true;break;}
            std::string identity=e->images[n].title+" "+e->images[n].caption;
            std::transform(identity.begin(),identity.end(),identity.begin(),[](unsigned char ch){return char(std::tolower(ch));});
            const bool logo=identity.find("logo")!=std::string::npos||identity.find("wordmark")!=std::string::npos;
            const bool manual=identity.find("manual")!=std::string::npos||identity.find("booklet")!=std::string::npos;
            const bool own_feature=std::find(feature.begin(),feature.end(),int(n))!=feature.end();
            // Reusing a relevant photograph is preferable to filling a chapter
            // with the cover, a video thumbnail or another manual page.
            const unsigned cover_cost=int(n)==story_cover_index(*e)?(e->kind=="game"?1000u:30u):0u;
            const unsigned score=image_uses[n]*100u+cover_cost+(video_poster?1400u:0u)+(card.feature>=0&&!own_feature?20u:0u)+(logo?2000u:0u)+(manual?1200u:0u);
            if(score<best_score){best=int(n);best_score=score;}
        }
        if(best>=0){card.image=best;++image_uses[size_t(best)];}
    }
}
bool Screen::story_object()const{return detail_&&story_focus_>=0&&story_focus_<int(story_cards_.size())&&story_cards_[size_t(story_focus_)].kind==StoryCard::object;}
const Soundtrack* Screen::current_soundtrack()const{
    const auto*e=current();if(!e)return nullptr;
    int room=playlist_music_room_;
    if(!playlist_active_&&story_focus_>=0&&story_focus_<int(story_cards_.size()))room=story_cards_[size_t(story_focus_)].music_room;
    if(room>=0&&room<int(e->soundtrack_rooms.size()))return &e->soundtrack_rooms[size_t(room)];
    return &e->soundtrack;
}
void Screen::move_story(int delta,ui::Feedback&f){
    if(story_cards_.empty())return;
    const int next=std::clamp(story_focus_+delta,0,int(story_cards_.size())-1);
    if(next==story_focus_)return;
    story_focus_=next;story_expanded_=false;story_read_.target=0;scroll_.snap(0);scroll_max_=0;story_actions_.clear();story_action_=-1;
    // A card change needs the same perceptible directional detent as the
    // timeline, rather than the very short generic focus tick.
    f.timeline_step(delta);
}
void Screen::draw_detail(){
    const auto*e=current();if(!e||story_cards_.empty())return;
    const float opened=std::clamp(story_open_.value,0.f,1.f);
    const auto palette=colours();const Color ink=palette.ink,quiet=palette.muted;
    const Color card=gfx::mix(palette.paper,tone_,.08f);
    const float rise=(1-opened)*780;
    story_actions_.clear();story_action_=-1;story_video_anchor_=0;sources_anchor_=0;
    if(seek_first_video_){for(size_t n=0;n<story_cards_.size();++n)if(story_cards_[n].kind==StoryCard::film){story_focus_=int(n);break;}seek_first_video_=false;}
    page_.push_clip({0,266,1920,672});page_.push_opacity(opened*fade_);
    const int first=std::max(0,int(std::floor(story_position_.value))-1),last=std::min(int(story_cards_.size())-1,int(std::ceil(story_position_.value))+1);
    for(int n=first;n<=last;++n){
        const auto&c=story_cards_[size_t(n)];const bool active=n==story_focus_;
        const float x=(float(n)-story_position_.value)*1792;
        if(std::abs(x)>1840)continue;
        const float scroll=active?scroll_.value:0;
        page_.push_transform(1,0,0,x,rise);
        const bool is_experience=c.kind==StoryCard::experience||c.kind==StoryCard::interactive;
        const auto experience_palette=museum_palette(1-theme_mix_.value);
        if(is_experience){
            const float pulse=reduced_?1.f:.94f+.06f*std::sin(time_*.55f);
            const float strength=(.16f+.12f*theme_mix_.value)*pulse;
            const Color lavender=Color::rgb(0xc8b7e5,strength),mint=Color::rgb(0xaad6c7,strength);
            page_.glow({108,302,740,580},32,84,lavender);
            page_.glow({1068,302,740,580},32,84,mint);
        }
        page_.rounded_rect({96,286,1728,620},0,is_experience?experience_palette.paper:card);
        page_.line(96,286,1824,286,1,(is_experience?experience_palette.ink:ink).with_alpha(.14f));
        const auto action=[&](Rect box,int image,int video){if(active)story_actions_.push_back({{box.x+x,box.y+rise,box.w,box.h},image,video});};
        const bool media=c.image>=0||c.kind==StoryCard::film||c.kind==StoryCard::object;
        const bool reverse=media&&c.kind==StoryCard::narrative&&(n%2==0);
        const float tx=media?(reverse?1214.f:144.f):184.f;
        const float tw=media?560.f:1440.f;
        const Rect media_box{reverse?132.f:758.f,318,1034,548};
        const char*label=c.kind==StoryCard::object?"IN YOUR HANDS":c.kind==StoryCard::film?"FROM THE ARCHIVE":c.kind==StoryCard::photograph?"LOOK CLOSER":c.kind==StoryCard::sources?"PROVENANCE":c.feature>=0?"IN FOCUS":"THE STORY";
        char number[64];hui::ui::format(number,"%02d / %s",n+1,label);
        if(c.kind!=StoryCard::soundtrack&&c.kind!=StoryCard::photograph&&c.kind!=StoryCard::experience&&c.kind!=StoryCard::interactive)ui::text(page_,fonts_.mono,number,tx,344,17,quiet,Align::left,1.5f);
        if(c.kind==StoryCard::soundtrack){
            draw_playlist({132,310,1656,575},active,c.music_room);
        }else if(c.kind==StoryCard::photograph){
            const auto&i=e->images[size_t(c.image)];cache_.request(image_url(i));const Rect photo{120,306,1680,580};
            image(page_,i,photo,true);action(fit_image(photo,cache_.get(image_url(i))),c.image,-1);
            if(active)scroll_max_=0;
        }else if(c.kind==StoryCard::interactive){
            workshop_.draw(page_,fonts_,{132,310,1656,575},tone_,active&&workshop_active_);
            if(active)scroll_max_=0;
        }else if(c.kind==StoryCard::experience){
            const auto&info=study_catalog()[size_t(c.study_index)];
            ui::text(page_,fonts_.mono,"EXPERIENCE / A PLAYABLE IDEA",148,350,18,experience_palette.muted,Align::left,2);
            const float body_top=ui::paragraph(page_,fonts_.semibold,c.title,144,423,48,720,55,experience_palette.ink)+16;
            page_.push_clip({144,body_top-27,720,860-body_top});page_.push_transform(1,0,0,0,-scroll);
            float end=ui::paragraph(page_,fonts_.regular,c.lead,148,body_top,25,710,36,experience_palette.muted);
            end+=24+draw_study_controls(page_,fonts_,info.id,{148,end+24,710,160},experience_palette.ink,experience_palette.paper,false);
            page_.pop_transform();page_.pop_clip();
            draw_study_preview(page_,c.study_index,{930,365,810,465});
            ui::text(page_,fonts_.regular,"Enter the experience",148,873,22,experience_palette.ink);
            if(active)scroll_max_=std::max(0.f,end-813);
        }else if(e->id.rfind("the-game-awards-",0)==0&&c.kind==StoryCard::narrative&&c.title.size()>=4&&c.title[0]=='2'&&std::isdigit(static_cast<unsigned char>(c.title[1]))&&std::isdigit(static_cast<unsigned char>(c.title[2]))&&std::isdigit(static_cast<unsigned char>(c.title[3]))){
            const std::string year=c.title.substr(0,4);
            char winners_heading[128];ui::format(winners_heading,"%s Winners",year.c_str());ui::text(page_,fonts_.display,winners_heading,144,418,62,ink);
            const auto&text=e->body[size_t(c.paragraph)];std::vector<std::string> winners;
            for(size_t begin=0;begin<text.size();){const auto end=text.find("\n\n",begin);winners.push_back(text.substr(begin,end==std::string::npos?end:end-begin));if(end==std::string::npos)break;begin=end+2;}
            page_.push_clip({140,448,760,420});page_.push_transform(1,0,0,0,-scroll);float y=482;
            for(const auto&award:winners){const auto separator=award.find('\n');const auto category=award.substr(0,separator),winner=separator==std::string::npos?std::string{}:award.substr(separator+1);
                const float category_end=ui::paragraph(page_,fonts_.mono,ui::upper(category),148,y,17,720,24,quiet);
                y=ui::paragraph(page_,fonts_.semibold,winner,148,category_end+15,27,720,39,ink)+38;
            }
            page_.pop_transform();page_.pop_clip();if(active)scroll_max_=std::max(0.f,y-830);
            int film=-1;for(size_t v=0;v<e->videos.size();++v)if(e->videos[v].title.rfind(year,0)==0){film=int(v);break;}
            const Rect frame{958,376,810,456};
            if(c.image>=0){const auto&i=e->images[size_t(c.image)];cache_.request(image_url(i));image(page_,i,frame,true);}
            if(film>=0){
                page_.push_opacity(active&&screening_from_story_&&video_index_==film?1.f-std::clamp(screening_open_.value,0.f,1.f):1.f);
                page_.circle(frame.cx(),frame.cy(),43,Color::rgb(0x101713,.65f));
                page_.triangle({frame.cx()-11,frame.cy()-17,34,34},Color::rgb(0xf1efe6),0,1.5708f);
                page_.pop_opacity();action(frame,-1,film);
            }else if(c.image>=0)action(fit_image(frame,cache_.get(image_url(e->images[size_t(c.image)]))),c.image,-1);
        }else{
            const float font_size=media?26.f:34.f,line=media?38.f:50.f;
            if(story_text_.size()!=story_cards_.size())story_text_.resize(story_cards_.size());
            auto&text=story_text_[size_t(n)];
            if(!text.ready){
                text.title_size=media?40.f:64.f;
                while(fonts_.semibold.font->wrap(ui::resolve_text(c.title),text.title_size,tw).size()>3&&text.title_size>28)--text.title_size;
                // Match the former title's 99-line limit; prose stays unlimited.
                text.title=ui::paragraph_lines(fonts_.semibold,c.title,text.title_size,tw);
                text.title_height=c.title.empty()?0.f:float(fonts_.semibold.font->wrap(ui::resolve_text(c.title),text.title_size,tw).size())*text.title_size*1.15f;
                const auto&body=c.feature>=0?e->editorial_features[size_t(c.feature)].body:e->body;
                const auto&headings=c.feature>=0?e->editorial_features[size_t(c.feature)].story_headings:e->story_headings;
                text.append(fonts_.regular,c.paragraph>=0?body[size_t(c.paragraph)]:c.lead,font_size,tw,line);
                std::string previous_heading=c.title;
                for(int p:c.continuation){
                    if(p<0||p>=int(body.size()))continue;
                    text.gap(32);
                    if(p<int(headings.size())&&!authored_heading(headings[size_t(p)]).empty()&&headings[size_t(p)]!=previous_heading){
                        previous_heading=headings[size_t(p)];
                        text.append(fonts_.semibold,previous_heading,font_size*1.12f,tw,line*1.15f,true);text.gap(12);
                    }
                    text.append(fonts_.regular,body[size_t(p)],font_size,tw,line);
                }
                text.ready=true;
            }
            ui::paragraph(page_,fonts_.semibold,text.title,tx,404,text.title_size,text.title_size*1.15f,ink);
            const float top=404+text.title_height+(c.title.empty()?0.f:28.f);
            const float available=824-top;
            page_.push_clip({tx,top-28,tw,available+28});page_.push_transform(1,0,0,0,-scroll);
            text.draw(page_,fonts_.regular,fonts_.semibold,tx,top,scroll,top-28,824,ink,quiet);
            page_.pop_transform();page_.pop_clip();
            // Compare the final glyph's bottom with the actual reading clip,
            // not the unused baseline advance following the last line.
            const float overflow=text.content_bottom(fonts_.regular,fonts_.semibold)-available;
            const float extent=overflow>1.f?overflow:0.f;
            if(active)scroll_max_=extent;
            if(extent>0&&available+28>0){
                const float height=available+28;
                const float thumb=std::min(height,std::max(32.f,height*height/(height+extent)));
                const float position=std::clamp(scroll/extent,0.f,1.f);
                const Rect track{tx+tw+14,top-28,6,height};
                page_.rounded_rect(track,3,quiet.with_alpha(.22f));
                page_.rounded_rect({track.x,track.y+(height-thumb)*position,track.w,thumb},3,ink.with_alpha(.65f));
            }
            if(c.kind==StoryCard::film){
                const Rect frame{media_box.x+30,media_box.y,974,548};
                if(c.image>=0){const auto&i=e->images[size_t(c.image)];cache_.request(image_url(i));image(page_,i,frame,true);}
                else page_.gradient_rect(frame,0,gfx::mix(Color::rgb(0x15241e),tone_,.14f),Color::rgb(0x101713));
                page_.push_opacity(active&&screening_from_story_&&video_index_==c.video?1.f-std::clamp(screening_open_.value,0.f,1.f):1.f);
                page_.circle(frame.cx(),frame.cy(),50,Color::rgb(0x101713,.45f));
                page_.triangle({frame.cx()-15,frame.cy()-21,44,42},Color::rgb(0xf1efe6),0,1.5708f);
                page_.pop_opacity();action(frame,-1,c.video);
            }else if(c.image>=0){
                const auto&i=e->images[size_t(c.image)];cache_.request(image_url(i));const auto a=cache_.get(image_url(i));
                const Rect photo{media_box.x,media_box.y,media_box.w,media_box.h-50};
                image(page_,i,photo,true);action(fit_image(photo,a),c.image,-1);
            }else if(c.kind==StoryCard::object){
                const Rect object_box{0,media_box.y-214,1920,960};
                if(active)object_origin_={object_box.x+x,object_box.y+rise,object_box.w,object_box.h};
                if(object_texture_&&object_open_.value<.001f)page_.image(object_texture_,object_box,gfx::kCanvasUv,Color::rgb(0xffffff,object_alpha_));
                else if(!object_texture_)ui::paragraph(page_,fonts_.mono,object_.error().empty()?"Loading model":object_.error(),object_box.x+24,object_box.cy(),18,object_box.w-48,27,quiet,6,Align::center);
            }else{
                // Retained only for a genuinely empty source gallery; the
                // catalogue admission audit rejects these editorial gaps.
                ui::text(page_,fonts_.display,std::to_string(e->year),1670,850,170,ink.with_alpha(.045f),Align::right);
            }
        }
        page_.pop_transform();
    }
    page_.pop_opacity();page_.pop_clip();
    if(!story_actions_.empty())story_action_=0;
    scroll_.target=std::clamp(scroll_.target,0.f,scroll_max_);
    // The navigation is the exhibit's own sequence of cards. Only three labels
    // are painted, even when a long archive article has hundreds of scenes.
    page_.push_opacity(opened);
    const float segment=std::min(78.f,1540.f/std::max(size_t(1),story_cards_.size()));
    const float start=960-segment*float(story_cards_.size())*.5f;
    for(size_t n=0;n<story_cards_.size();++n){const float h=std::clamp(1.f-std::abs(float(n)-story_position_.value),0.f,1.f);page_.rounded_rect({start+float(n)*segment+3,929,segment-6,2+2*h},0,gfx::mix(quiet.with_alpha(.18f),gfx::mix(ink,tone_,.65f),h));}
    for(int n=std::max(0,story_focus_-1);n<=std::min(int(story_cards_.size())-1,story_focus_+1);++n){
        const float x=960+(float(n)-story_position_.value)*600;
        const std::string t=n==story_focus_?"":story_cards_[size_t(n)].title;float size=18;
        while(fonts_.regular.font->wrap(t,size,540).size()>1&&size>13)--size;
        ui::paragraph(page_,fonts_.regular,t,x,968,size,540,size*1.15f,ink.with_alpha(n==story_focus_?1.f:.38f),2,Align::center);
    }
    page_.pop_opacity();
    if(!workshop_active_&&!gallery_&&!screening_&&!object_inspect_&&gallery_open_.value<.001f&&screening_open_.value<.001f&&object_open_.value<.001f){
        const auto&c=story_cards_[size_t(story_focus_)];
        std::vector<ui::Hint> controls={{ui::Button::dpad,story_expanded_?"Cards / read":"Cards"}};
        if(c.kind==StoryCard::soundtrack)controls.push_back({ui::Button::cross,"Listen"});
        const bool archive_video=e->id.rfind("the-game-awards-",0)==0&&!story_actions_.empty()&&story_actions_[0].video>=0;
        if(archive_video)controls.push_back({ui::Button::cross,"Watch edition"});
        if(!archive_video&&(c.kind==StoryCard::object||c.kind==StoryCard::film||c.kind==StoryCard::interactive||c.kind==StoryCard::experience))controls.push_back({ui::Button::cross,c.kind==StoryCard::object?"Inspect object":c.kind==StoryCard::film?"Play film":"Enter study"});
        if(story_object())controls.push_back({ui::Button::square,"Inspect 3D"});
        else if(c.image>=0)controls.push_back({ui::Button::square,"View image"});
        if(scroll_max_>0&&!story_object())controls.push_back({ui::Button::right_stick,"Read"});
        controls.push_back({ui::Button::l1,"Exhibit",ui::Button::r1});controls.push_back({ui::Button::circle,"Timeline"});controls.push_back({ui::Button::options,"Options"});
        page_.push_opacity(opened);hints(controls);page_.pop_opacity();
    }
}
}
