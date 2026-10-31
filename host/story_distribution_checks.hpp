// Actual production compositor regressions; no fixture reaches production data.
#pragma once
namespace museum {
inline bool ScreenInspection::verify_story_distribution(Screen&s){
 const auto require=[](bool pass,const char*why){if(!pass)std::fprintf(stderr,"Distribution: %s\n",why);return pass;};
 const auto fixture=[](){Entry e;e.id="distribution-fixture";e.title="Distribution";e.year=1950;e.preferred_image=0;
  for(int n=0;n<10;++n){e.body.push_back("Paragraph "+std::to_string(n)+". "+std::string(120,'a'+n));e.story_headings.push_back("Section "+std::to_string(n));}
  for(int n=0;n<3;++n){Image im;im.url="fixture://distinct-"+std::to_string(n);im.title="Image "+std::to_string(n);e.images.push_back(im);}return e;};
 const auto use=[&](Entry e){s.catalog_.entries={std::move(e)};s.visible_={0};s.focus_=0;s.history_focus_=false;s.detail_=true;s.prepare_story();};
 const auto complete=[&](int feature,const std::vector<std::string>&body){std::vector<int> actual;for(const auto&card:s.story_cards_)if(card.feature==feature&&card.paragraph>=0){actual.push_back(card.paragraph);actual.insert(actual.end(),card.continuation.begin(),card.continuation.end());}if(actual.size()!=body.size())return false;for(size_t n=0;n<actual.size();++n)if(actual[n]!=int(n))return false;return true;};
 auto e=fixture();const auto original=e.body;use(e);std::vector<int> lengths;std::set<int> images;
 for(const auto&c:s.story_cards_)if(c.paragraph>=0){if(!require(c.image>0,"cover excluded and both groups illustrated"))return false;lengths.push_back(1+int(c.continuation.size()));images.insert(c.image);}else if(c.kind==Screen::StoryCard::photograph)return require(false,"consumed photograph remains empty");
 if(!require(lengths==std::vector<int>({5,5})&&images.size()==2&&complete(-1,original),"ten source paragraphs balance five/five over two distinct images"))return false;
 if(!require(s.current()->body==original,"source wording unchanged"))return false;
 e=fixture();e.images[2].story_paragraph=7;use(e);bool explicit_kept=false;for(const auto&c:s.story_cards_)if(c.image==2){explicit_kept=c.paragraph==7||std::find(c.continuation.begin(),c.continuation.end(),7)!=c.continuation.end();}
 if(!require(explicit_kept&&complete(-1,e.body),"explicit image anchor retained with its complete source paragraph"))return false;
 e=fixture();e.body.resize(4);e.story_headings.resize(4);e.images.resize(2);e.images[1].story_paragraph=2;e.explicit_story_media_only=true;e.preserve_unillustrated_opening=true;use(e);
 int opening_gaps=0;bool later_artifact=false;
 for(const auto&c:s.story_cards_)if(c.paragraph>=0){if(c.paragraph<2){if(!require(c.image<0&&c.continuation.empty(),"opt-in opening gap never borrows a later artifact"))return false;++opening_gaps;}else if(c.paragraph==2)later_artifact=c.image==1&&c.continuation==std::vector<int>({3});}
 if(!require(opening_gaps==2&&later_artifact&&complete(-1,e.body),"partial article keeps two opening gaps and the later illustrated chapter"))return false;
 e.preserve_unillustrated_opening=false;use(e);int legacy_chapters=0;
 for(const auto&c:s.story_cards_)if(c.paragraph>=0){++legacy_chapters;if(!require(c.paragraph==0&&c.image==1&&c.continuation==std::vector<int>({1,2,3}),"default prefix grouping remains unchanged"))return false;}
 if(!require(legacy_chapters==1&&complete(-1,e.body),"legacy curated introduction keeps its existing chapter"))return false;
 e=fixture();e.explicit_story_media_only=true;e.images[1].story_paragraph=0;use(e);int image_only=0;for(const auto&c:s.story_cards_)if(c.kind==Screen::StoryCard::photograph&&c.image==2)++image_only;
 if(!require(image_only==0&&complete(-1,e.body),"curated unmapped artifact stays outside story without guessed prose"))return false;
 s.image_index_=2;s.prepare_gallery();if(!require(s.viewer_.images().size()==3&&s.viewer_.index()==2&&s.current()->images[2].url=="fixture://distinct-2","all original images including unused artifact remain reachable in Square gallery"))return false;
 e=fixture();e.body.clear();e.story_headings.clear();use(e);for(const auto&c:s.story_cards_)if(c.kind==Screen::StoryCard::photograph)return require(false,"textless exhibit invents no empty photo chapters");s.image_index_=1;s.prepare_gallery();if(!require(s.viewer_.images().size()==3,"textless exhibit retains all gallery images"))return false;
 e=fixture();EditorialFeature f;f.id="feature";f.title="Feature";for(int n=0;n<4;++n){f.body.push_back("Feature source "+std::to_string(n)+std::string(150,'z'));f.story_headings.push_back("Feature section");}
 for(int n=3;n<5;++n){Image im;im.url="fixture://feature-"+std::to_string(n);e.images.push_back(im);f.image_indices.push_back(n);}e.editorial_features.push_back(f);use(e);
 for(const auto&c:s.story_cards_)if(c.paragraph>=0&&!require(c.feature<0?c.image<3:c.image>=3,"feature-owned photos never cross article boundary"))return false;
 if(!require(complete(-1,e.body)&&complete(0,f.body),"all main and feature paragraphs preserved independently"))return false;
 e=fixture();VideoRecord v;v.youtube_id="film-fixture";v.title="Film";v.story_paragraph=3;v.poster_url="fixture://poster";e.videos.push_back(v);Image im;im.url=v.poster_url;e.images.push_back(im);use(e);int film_count=0;
 for(const auto&c:s.story_cards_)if(c.kind==Screen::StoryCard::film){++film_count;if(!require(c.image==3&&c.paragraph==3&&c.title==e.story_headings[3]&&c.lead.empty(),"placed film replaces paragraph photograph and uses its authored heading/prose"))return false;}
 if(!require(film_count==1&&complete(-1,e.body),"video order and complete prose retained"))return false;
 e=fixture();e.explicit_story_media_only=true;e.images.resize(1);v.story_paragraph=3;e.videos={v};im.url=v.poster_url;e.images.push_back(im);use(e);bool explicit_video_kept=false;
 for(const auto&c:s.story_cards_)if(c.kind==Screen::StoryCard::film)explicit_video_kept=c.paragraph==3&&c.title==e.story_headings[3];
 if(!require(explicit_video_kept&&complete(-1,e.body),"explicit film never borrows the heading or paragraph of an unillustrated prefix"))return false;
 e=fixture();e.explicit_story_media_only=true;e.images[1].story_paragraph=0;e.images[2].story_paragraph=5;v.story_paragraph=-1;v.caption="A player caption, not an article paragraph.";e.videos={v};im.url=v.poster_url;e.images.push_back(im);use(e);bool opening_film=false;
 for(const auto&c:s.story_cards_){if(c.kind==Screen::StoryCard::film){opening_film=c.paragraph==0&&c.image==3&&c.title==e.story_headings[0]&&c.lead.empty();}if(c.kind==Screen::StoryCard::film&&!require(c.paragraph>=0,"body-backed film never becomes caption-only"))return false;}
 if(!require(opening_film&&complete(-1,e.body)&&s.current()->body==e.body,"unplaced first film illustrates intact introduction even with an authored p0 photo"))return false;
 s.image_index_=1;s.prepare_gallery();if(!require(s.viewer_.images().size()==4&&s.viewer_.index()==1,"displaced authored photograph remains available in full gallery"))return false;
 e=fixture();e.explicit_story_media_only=true;v.story_paragraph=-1;e.videos={v};im.url=v.poster_url;e.images.push_back(im);auto second=v;second.youtube_id="second-film";second.story_paragraph=5;second.poster_url="fixture://second-poster";e.videos.push_back(second);im.url=second.poster_url;e.images.push_back(im);use(e);std::set<int> film_paragraphs;
 for(const auto&c:s.story_cards_)if(c.kind==Screen::StoryCard::film){film_paragraphs.insert(c.paragraph);if(!require(c.lead.empty()&&c.title==e.story_headings[size_t(c.paragraph)],"each mapped film uses existing narrative, not its caption"))return false;}
 if(!require(film_paragraphs==std::set<int>({0,5})&&complete(-1,e.body),"two editorially mapped videos accompany distinct paragraphs without prose duplication"))return false;
 e=fixture();e.body.clear();e.story_headings.clear();e.videos={v};use(e);if(!require(s.story_cards_.size()==1&&s.story_cards_[0].kind==Screen::StoryCard::film&&s.story_cards_[0].paragraph<0&&s.story_cards_[0].lead==v.caption,"textless exhibit retains genuine film caption without inventing article prose"))return false;
 e=fixture();e.id="golden-joystick-2025";e.body.resize(2);e.story_headings.resize(2);e.images.resize(1);use(e);if(!require(s.story_cards_.size()==2&&complete(-1,e.body),"Golden Joystick explanation and winners remain exactly two independent cards"))return false;
 e=fixture();e.id="the-game-awards-fixture";e.explicit_story_media_only=true;e.images[1].story_paragraph=0;e.images[2].story_paragraph=1;v.poster_url=e.images[2].url;e.videos={v};use(e);bool year_photo=false;
 for(const auto&c:s.story_cards_){if(c.kind==Screen::StoryCard::film)return require(false,"awards unexpectedly render standalone film");if(c.paragraph==1)year_photo=c.image==2;}
 if(!require(year_photo&&complete(-1,e.body),"awards year photograph not reserved for a film card that is never created"))return false;
 e=fixture();e.subtitle="From the reference collection";e.story_headings.clear();use(e);for(const auto&c:s.story_cards_)if(c.paragraph>=0&&!require(c.title.empty(),"generic and absent headings stay blank"))return false;
 e=fixture();e.id="daily-11-16";use(e);const auto canonical_cards=s.story_cards_;auto event=e;event.id="recognition-fixture";event.year=2026;event.preferred_image=2;event.story_entry_id=e.id;
 if(!require(std::any_of(canonical_cards.begin(),canonical_cards.end(),[](const auto&c){return c.kind==Screen::StoryCard::experience&&c.study_index>=0;}),"canonical shared-story fixture includes its actual interactive experience"))return false;
 s.catalog_.entries.push_back(event);s.visible_={1};s.prepare_story();
 if(!require(s.current()->id==event.id&&s.current()->year==2026&&s.current()->preferred_image==2,"shared story preserves event timeline date and its own cover"))return false;
 if(!require(s.story_cards_.size()==canonical_cards.size(),"two dated stops retain identical card count"))return false;
 for(size_t n=0;n<canonical_cards.size();++n){const auto&a=canonical_cards[n];const auto&b=s.story_cards_[n];if(!require(a.kind==b.kind&&a.paragraph==b.paragraph&&a.image==b.image&&a.video==b.video&&a.title==b.title&&a.lead==b.lead&&a.continuation==b.continuation&&a.study_index==b.study_index&&a.music_room==b.music_room,"shared story preserves every card, interactive experience and image mapping"))return false;}
 s.catalog_.entries[1].story_entry_id="missing";s.prepare_story();bool own_cover_used=false;for(const auto&c:s.story_cards_)own_cover_used|=c.image==2;
 if(!require(!own_cover_used,"missing shared story safely reserves its own cover"))return false;
 std::puts("PASS actual story distribution: balanced complete paragraphs, explicit/curated guards, cover exclusion, feature isolation, video order, shared stories with independent dated covers.");return true;
}
}
