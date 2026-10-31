// Quiet one-shot archival atmosphere; source facts live in culture-memories.json.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/culture_ambience.hpp"
#include "core/save_file.hpp"
#include "platform/ps5/system.hpp"
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#include <algorithm>
#include <cmath>
#include <set>
#include <cstring>
namespace museum {
namespace {
// Only app-packaged assets, never absolute paths, traversal or remote URLs.
bool local_path(const std::string&p){
 return p.rfind("assets/culture-audio/",0)==0&&p.size()>25&&p.find("..") ==std::string::npos&&p.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-/.")==std::string::npos&&p.substr(p.size()-4)==".wav";
}
std::unique_ptr<CultureAmbience::LocalAudio> read_pcm(const std::string&path){
 std::string bytes;if(!hui::save::read_file(path,&bytes,20u<<20)||bytes.size()<44)return {};
 const auto*b=reinterpret_cast<const unsigned char*>(bytes.data());
 const auto u16=[&](std::size_t n){return unsigned(b[n])|(unsigned(b[n+1])<<8);};
 const auto u32=[&](std::size_t n){return std::uint32_t(b[n])|(std::uint32_t(b[n+1])<<8)|(std::uint32_t(b[n+2])<<16)|(std::uint32_t(b[n+3])<<24);};
 if(std::memcmp(b,"RIFF",4)||std::memcmp(b+8,"WAVE",4)||std::uint64_t(u32(4))+8!=bytes.size())return {};
 bool format=false;std::size_t data=0,size=0;
 for(std::size_t at=12;at+8<=bytes.size();){
  const auto n=u32(at+4);const std::size_t begin=at+8;
  if(n>bytes.size()-begin)return {};
  if(!std::memcmp(b+at,"fmt ",4)){
   if(format||n<16||u16(begin)!=1||u16(begin+2)!=2||u32(begin+4)!=48000||u32(begin+8)!=192000||u16(begin+12)!=4||u16(begin+14)!=16)return {};
   format=true;
  }else if(!std::memcmp(b+at,"data",4)){if(data||!n||n%4)return {};data=begin;size=n;}
  at=begin+n+(n&1u);if(at>bytes.size())return {};
 }
 if(!format||!data||size/4>48000u*600u)return {};
 auto result=std::make_unique<CultureAmbience::LocalAudio>();result->samples.resize(size/2);
 for(std::size_t n=0;n<size/2;++n){const unsigned v=u16(data+n*2);result->samples[n]=std::int16_t(v<32768?v:int(v)-65536);}
 return result;
}
}

bool CultureAmbience::load(const std::string&path){
 const auto reject=[&](const char*why){hui::sys::log("[Museum] culture table rejected: %s (%s)",why,path.c_str());return false;};
 std::string raw;if(!hui::save::read_file(path,&raw,2u<<20))return reject("file missing or exceeds 2 MiB");
 auto root=nlohmann::json::parse(raw,nullptr,false);if(root.is_discarded()||!root.is_object()||!root.contains("schema")||!root["schema"].is_number_integer()||root["schema"].get<int>()!=1||!root.contains("cues")||!root["cues"].is_array()||root["cues"].size()>512)return reject("invalid schema or more than 512 cues");
 std::vector<Cue>next;std::set<std::string>ids;
 std::vector<std::unique_ptr<LocalAudio>>loaded;
 // The manifest is in <app>/content. Resolve assets from that same app root.
 const auto slash=path.find_last_of("/\\");const auto parent=slash==std::string::npos?std::string():path.substr(0,slash);
 const auto root_slash=parent.find_last_of("/\\");
 const auto app_root=parent.empty()?std::string("."):(root_slash==std::string::npos?std::string("."):parent.substr(0,root_slash));
 std::size_t retained=0;for(const auto&pcm:local_storage_)retained+=pcm->samples.size()*2;
 std::size_t row_index=0,skipped=0;
 for(const auto&row:root["cues"]){
  Cue c;std::unique_ptr<LocalAudio>pcm;
  const auto parse_row=[&]()->const char*{
   if(!row.is_object())return "cue is not an object";
   for(const char*k:{"entry_id","kind"})if(!row.contains(k)||!row[k].is_string())return "missing/string entry_id or kind";
   c.entry_id=row["entry_id"].get<std::string>();c.kind=row["kind"].get<std::string>();
   if(c.entry_id.empty()||ids.count(c.entry_id))return "empty or duplicate entry_id";
   if(!row.contains("start_seconds")||!row["start_seconds"].is_number()||!row.contains("end_seconds")||!row["end_seconds"].is_number()||!row.contains("reverb")||!row["reverb"].is_boolean()||!row.contains("evidence")||row["evidence"].empty())return "missing/invalid range, reverb or evidence";
   if(row.contains("youtube_id")){if(!row["youtube_id"].is_string())return "youtube_id is not a string";c.youtube_id=row["youtube_id"].get<std::string>();}
   if(row.contains("local_audio_path")){if(!row["local_audio_path"].is_string())return "local_audio_path is not a string";c.local_audio_path=row["local_audio_path"].get<std::string>();if(!local_path(c.local_audio_path))return "unsafe local_audio_path";}
   c.start=row["start_seconds"].get<double>();c.end=row["end_seconds"].get<double>();c.reverb=row["reverb"].get<bool>();c.evidence=row["evidence"].dump();
   if(row.contains("gain")){if(!row["gain"].is_number())return "gain is not numeric";c.gain=row["gain"].get<float>();}
   if(row.contains("normalize_level")){if(!row["normalize_level"].is_boolean())return "normalize_level is not boolean";c.normalize_level=row["normalize_level"].get<bool>();}
   if(row.contains("ambient_policy")){if(!row["ambient_policy"].is_string())return "ambient_policy is not a string";const auto policy=row["ambient_policy"].get<std::string>();if(policy!="silence"&&policy!="duck")return "unknown ambient_policy";}
   if(c.local_audio_path.empty()&&(c.youtube_id.size()!=11||c.youtube_id.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")!=std::string::npos))return "invalid YouTube ID";
   if((c.kind!="music"&&c.kind!="voice")||!std::isfinite(c.start)||!std::isfinite(c.end)||c.start<0||c.end<=c.start||c.end-c.start>600||!std::isfinite(c.gain)||c.gain<=0||c.gain>2||(c.kind=="music"&&c.reverb))return "invalid kind/range/gain or reverb on music";
   if(!c.local_audio_path.empty()){
    // Local PCM is valid for both archival speech and music. A bad record
    // never disables unrelated recordings, including streamed cues.
    if(loaded.size()>=4)return "more than four local recordings";
    pcm=read_pcm(app_root+"/"+c.local_audio_path);if(!pcm)return "local WAV missing, invalid or exceeds 20 MiB (48 kHz stereo PCM16 required)";
    const double duration=double(pcm->samples.size()/2)/48000.;
    if(c.start!=0||std::abs(c.end-duration)>.002)return "local range does not match WAV duration";
    if(retained+pcm->samples.size()*2>(80u<<20))return "retained PCM exceeds 80 MiB";
    c.end=duration;
   }
   return nullptr;
  };
  const auto problem=parse_row();
  if(problem){++skipped;hui::sys::log("[Museum] culture cue skipped: row %zu / %s: %s",row_index,c.entry_id.empty()?"<unknown>":c.entry_id.c_str(),problem);}
  else{ids.insert(c.entry_id);if(pcm){retained+=pcm->samples.size()*2;c.local_audio=pcm.get();loaded.push_back(std::move(pcm));}next.push_back(std::move(c));}
  ++row_index;
 }
 if(next.empty()&&!root["cues"].empty())return reject("no usable cues after record validation");
 if(skipped)hui::sys::log("[Museum] culture table: %zu valid, %zu skipped",next.size(),skipped);
 relinquish();for(auto&pcm:loaded)local_storage_.push_back(std::move(pcm));cues_=std::move(next);stop_.clear();fired_=false;return true;
}
void CultureAmbience::relinquish(){owns_=ready_=false;active_=nullptr;closing_=dwell_=0;entry_bed_gain_.store(1);audible_.store(false);render_.store(false,std::memory_order_release);++revision_;}
CultureAmbience::Command CultureAmbience::update(const Context&c,const Playback&p,float dt){
 dt=std::isfinite(dt)?std::clamp(dt,0.f,.25f):0;
 const bool changed=c.entry_id!=stop_;
 if(changed){stop_=c.entry_id;dwell_=0;fired_=false;}
 volume_.store(std::isfinite(c.volume)?std::clamp(c.volume,0.f,1.f):0,std::memory_order_relaxed);
 if(owns_){
  Playback state=p;
  if(active_&&active_->local_audio){
   const auto progress=local_progress_.load(std::memory_order_acquire);
   const auto frame=unsigned(progress>>32)==revision_.load(std::memory_order_relaxed)?unsigned(progress):0u;
   state={true,frame>=active_->local_audio->samples.size()/2,false,double(frame)/48000.};
  }
  ready_=state.ready;
  const bool leaving=closing_>0||changed||!c.eligible||!active_||active_->entry_id!=c.entry_id;
  if(leaving){audible_.store(false);closing_+=dt;dwell_=0;}
  else{audible_.store(true);closing_=0;remaining_.store(float(std::max(0.,active_->end-state.position)));}
  if(state.ended||state.failed||closing_>=.18f){const auto*previous=active_;relinquish();return {Command::close,previous};}
  return {};
 }
 if(!c.eligible||c.volume<=.001f||fired_){dwell_=0;return {};}
 const auto it=std::find_if(cues_.begin(),cues_.end(),[&](const auto&cue){return cue.entry_id==c.entry_id;});
 if(it==cues_.end()){dwell_=0;return {};}
 dwell_+=dt;if(dwell_<2.f)return {};
 active_=&*it;fired_=owns_=true;ready_=active_->local_audio!=nullptr;dwell_=closing_=0;
 cue_gain_.store(active_->gain);normalize_level_.store(active_->normalize_level);voice_reverb_.store(active_->kind=="voice"&&active_->reverb);remaining_.store(float(active_->end-active_->start));
 // Every cultural recollection gets the foreground, including archival speech.
 bed_target_.store(0.f);entry_bed_gain_.store(1);
 local_render_.store(active_->local_audio,std::memory_order_release);
 ++revision_;audible_.store(true);render_.store(true,std::memory_order_release);
 return {Command::open,active_};
}
void CultureAmbience::process(const float*in,float*out,unsigned frames){
 const unsigned revision=revision_.load(std::memory_order_acquire);
 if(revision!=audio_revision_){audio_revision_=revision;level_.reset(normalize_level_.load(std::memory_order_relaxed));envelope_=user_gain_=0;audio_started_=false;entry_frames_=0;audio_remaining_=0;last_remaining_=-1;delay_.fill(0);delay_at_=0;local_audio_frame_=0;}
 const auto*local=local_render_.load(std::memory_order_acquire);
 const float volume=volume_.load(std::memory_order_relaxed),gain=cue_gain_.load(std::memory_order_relaxed);
 const bool enabled=audible_.load(std::memory_order_relaxed),reverb=voice_reverb_.load(std::memory_order_relaxed);
 const float remaining=remaining_.load(std::memory_order_relaxed);
 if(remaining!=last_remaining_){audio_remaining_=remaining;last_remaining_=remaining;}
 for(unsigned n=0;n<frames;++n){
  float l=0,r=0;
  if(local){
   if(local_audio_frame_<local->samples.size()/2){l=float(local->samples[local_audio_frame_*2])/32768.f;r=float(local->samples[local_audio_frame_*2+1])/32768.f;++local_audio_frame_;}
  }else if(in){l=std::isfinite(in[n*2])?std::clamp(in[n*2],-8.f,8.f):0;r=std::isfinite(in[n*2+1])?std::clamp(in[n*2+1],-8.f,8.f):0;}
  if(l!=0.f||r!=0.f)audio_started_=true; // Preserve even the quietest real PCM; no level gate.
  const float wanted=enabled&&audio_started_?(local?1.f:std::clamp(audio_remaining_/.35f,0.f,1.f)):0;
  if(audio_started_)audio_remaining_=std::max(0.f,audio_remaining_-1.f/48000);
  if(enabled&&audio_started_&&entry_frames_<48000)++entry_frames_;
  const float entry=float(entry_frames_)/48000.f;
  const float desired=std::min(wanted,entry);
  envelope_=desired<envelope_?std::max(desired,envelope_-1.f/7200):desired; // Unchanged150ms exit; exact one-second PCM-driven entry.
  const float balanced=level_.process(l,r);l*=balanced;r*=balanced;
  const unsigned at=delay_at_*2;
  if(reverb){const float dl=delay_[at],dr=delay_[at+1];delay_[at]=l+dr*.12f;delay_[at+1]=r+dl*.12f;l+=dr*.08f;r+=dl*.08f;}
  if(++delay_at_==3840)delay_at_=0;
  user_gain_+=std::clamp(volume-user_gain_,-1.f/4800,1.f/4800);
  l*=envelope_*user_gain_*gain;r*=envelope_*user_gain_*gain;
  // Preserve the waveform here. MuseumAudio applies the shared block-wise
  // OutputPeakGuard after the complete mix, including this exact layer trim.
  constexpr float cultural_volume_trim=.8f;
  out[n*2]+=l*cultural_volume_trim;out[n*2+1]+=r*cultural_volume_trim;
 }
 if(local)local_progress_.store((std::uint64_t(revision)<<32)|local_audio_frame_,std::memory_order_release);
 // UI reads this audio-sample clock: buffering never ducks the museum bed.
 // Music follows downward progress directly, without a second fade-in ramp.
 entry_bed_gain_.store(1.f-(1.f-bed_target_.load(std::memory_order_relaxed))*float(entry_frames_)/48000.f,std::memory_order_relaxed);
}
}
