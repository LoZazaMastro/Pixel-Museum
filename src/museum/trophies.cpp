// Pixel Museum - local achievements; never registers official PSN trophies.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/trophies.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <ctime>
#include <cerrno>
#include <set>
#include <unordered_set>
#include <sys/stat.h>
#ifdef _WIN32
#include <windows.h>
#include <io.h>
#include <direct.h>
#else
#include <unistd.h>
#endif
namespace museum {
namespace {
constexpr std::size_t kMaxFile=4u*1024u*1024u,kMaxItems=100000;
std::string hex(const std::string& s) {
    static const char digits[]="0123456789abcdef";std::string out;out.reserve(s.size()*2);
    for(unsigned char c:s){out+=digits[c>>4];out+=digits[c&15];}return out;
}
bool unhex(const std::string& s,std::string& out) {
    if(s.size()%2||s.size()>8192)return false;out.clear();
    auto nib=[](char c){return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;};
    for(std::size_t i=0;i<s.size();i+=2){int a=nib(s[i]),b=nib(s[i+1]);if(a<0||b<0)return false;out+=char((a<<4)|b);}return true;
}
std::string checksum(const std::string& s) {
    std::uint64_t h=14695981039346656037ull;for(unsigned char c:s){h^=c;h*=1099511628211ull;}
    static const char digits[]="0123456789abcdef";std::string out(16,'0');
    for(std::size_t i=16;i>0;--i){out[i-1]=digits[h&15];h>>=4;}return out;
}
bool number(const std::string& s,std::uint64_t& v) {
    if(s.empty()||s.size()>20)return false;v=0;
    for(char c:s){if(c<'0'||c>'9'||v>(UINT64_MAX-unsigned(c-'0'))/10)return false;v=v*10+unsigned(c-'0');}return true;
}
bool contains(const std::vector<std::string>& v,const std::string& s){return std::find(v.begin(),v.end(),s)!=v.end();}
bool add(std::vector<std::string>& v,const std::string& s){if(s.empty()||s.size()>1024||contains(v,s)||v.size()>=kMaxItems)return false;v.push_back(s);return true;}
std::string cardKey(const std::string& id,int index){return id+"\x1f"+std::to_string(index);}
bool read(const std::string& path,std::string& out) {
    FILE* f=std::fopen(path.c_str(),"rb");if(!f)return false;
    if(std::fseek(f,0,SEEK_END)!=0){std::fclose(f);return false;}const long n=std::ftell(f);
    if(n<0||std::uint64_t(n)>kMaxFile||std::fseek(f,0,SEEK_SET)!=0){std::fclose(f);return false;}
    out.resize(std::size_t(n));const bool ok=std::fread(out.data(),1,out.size(),f)==out.size()&&!std::ferror(f);
    const bool closed=std::fclose(f)==0;return ok&&closed;
}
bool replace(const std::string& from,const std::string& to) {
#ifdef _WIN32
    return MoveFileExA(from.c_str(),to.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0;
#else
    return std::rename(from.c_str(),to.c_str())==0;
#endif
}
bool atomic(const std::string& path,const std::string& bytes) {
    for(std::size_t i=1;i<path.size();++i)if(path[i]=='/'||path[i]=='\\'){
        const auto part=path.substr(0,i);
#ifdef _WIN32
        const int rc=_mkdir(part.c_str());
#else
        const int rc=mkdir(part.c_str(),0700);
#endif
        if(rc!=0&&errno!=EEXIST)return false;
    }
    const std::string temp=path+".tmp";FILE* f=std::fopen(temp.c_str(),"wb");if(!f)return false;
    bool ok=std::fwrite(bytes.data(),1,bytes.size(),f)==bytes.size()&&std::fflush(f)==0;
#ifdef _WIN32
    if(ok)ok=_commit(_fileno(f))==0;
#else
    if(ok)ok=fsync(fileno(f))==0;
#endif
    if(std::fclose(f)!=0)ok=false;
    if(!ok){std::remove(temp.c_str());return false;}
    std::string verify;if(!read(temp,verify)||verify!=bytes){std::remove(temp.c_str());return false;}
    if(!replace(temp,path)){std::remove(temp.c_str());return false;}return true;
}
}
Trophies::Trophies(std::string state_path):path_(std::move(state_path)){}
std::vector<std::uint64_t> Trophies::visitMilestones(){std::vector<std::uint64_t> v={20,50,100,150,200};for(std::uint64_t n=300;n<=1500;n+=100)v.push_back(n);return v;}
std::string Trophies::encode(const State& s) {
    std::string out="PIXEL_MUSEUM_TROPHIES\t1\n";
    auto list=[&](char tag,const std::vector<std::string>& v){std::set<std::string> sorted(v.begin(),v.end());for(const auto& x:sorted)out+=std::string(1,tag)+"\t"+hex(x)+"\n";};
    list('V',s.visited);list('C',s.snapshot);list('Q',s.seen_cards);list('K',s.culture);
    for(const auto& p:s.unlocked)out+="U\t"+hex(p.first)+"\t"+std::to_string(p.second)+"\n";
    for(const auto& p:s.stats)out+="S\t"+hex(p.first)+"\t"+std::to_string(p.second)+"\n";
    out+="F\t"+std::to_string(s.first_music?1:0)+std::to_string(s.first_video?1:0)+std::to_string(s.max_zoom?1:0)+std::to_string(s.first_today?1:0)+"\n";
    return out+"H\t"+checksum(out)+"\n";
}
bool Trophies::decode(const std::string& bytes,State& result) {
    const std::string magic="PIXEL_MUSEUM_TROPHIES\t1\n";
    if(bytes.size()>kMaxFile||bytes.compare(0,magic.size(),magic)!=0)return false;
    auto footer=bytes.rfind("H\t");if(footer==std::string::npos||bytes.substr(footer)!="H\t"+checksum(bytes.substr(0,footer))+"\n")return false;
    State s;std::size_t cursor=magic.size(),count=0;bool flags=false;
    while(cursor<footer) {
        auto end=bytes.find('\n',cursor);if(end==std::string::npos||end>footer)end=footer;
        const std::string line=bytes.substr(cursor,end-cursor);cursor=end+1;
        if(++count>kMaxItems||line.size()<2||line[1]!='\t')return false;
        char tag=line[0];auto split=line.find('\t',2);std::string value=line.substr(2,split==std::string::npos?split:split-2),key;
        if(tag=='F'){if(flags||(value.size()!=3&&value.size()!=4)||value.find_first_not_of("01")!=std::string::npos)return false;flags=true;s.first_music=value[0]=='1';s.first_video=value[1]=='1';s.max_zoom=value[2]=='1';s.first_today=value.size()==4&&value[3]=='1';continue;}
        if(!unhex(value,key)||key.empty())return false;
        if(tag=='U'||tag=='S'){std::uint64_t n;if(split==std::string::npos||!number(line.substr(split+1),n))return false;auto& map=tag=='U'?s.unlocked:s.stats;if(!map.emplace(key,n).second)return false;}
        else {if(split!=std::string::npos)return false;std::vector<std::string>* v=tag=='V'?&s.visited:tag=='C'?&s.snapshot:tag=='Q'?&s.seen_cards:tag=='K'?&s.culture:nullptr;if(!v||!add(*v,key))return false;}
    }
    if(!flags)return false;result=std::move(s);return true;
}
bool Trophies::load() {
    State loaded;std::string raw;struct stat st{};const bool exists=stat(path_.c_str(),&st)==0;const int stat_error=errno;
    if(read(path_,raw)){
        const std::string prefix="PIXEL_MUSEUM_TROPHIES\t";const auto end=raw.find('\n');std::uint64_t version=0;
        if(raw.rfind(prefix,0)==0&&end!=std::string::npos&&number(raw.substr(prefix.size(),end-prefix.size()),version)&&version!=1){writable_=false;error_="Newer or unsupported trophy state version preserved, including its backup";return false;}
        if(decode(raw,loaded)){state_=std::move(loaded);pending_.clear();error_.clear();writable_=true;return true;}
    }
    if(read(path_+".bak",raw)&&decode(raw,loaded)){state_=std::move(loaded);pending_.clear();error_="Recovered trophy progress from backup";writable_=true;return true;}
    if(!exists&&stat_error==ENOENT){state_=State{};pending_.clear();error_.clear();writable_=true;return true;}
    writable_=false;error_="Trophy state is unreadable or uses an unsupported version; original preserved";return false;
}
void Trophies::setDefinitions(std::vector<TrophyDefinition> definitions) {
    std::set<std::string> ids;unsigned ultimate=0;
    for(const auto& d:definitions){if(d.id.empty()||d.id.size()>192||!ids.insert(d.id).second||d.target==0){error_="Invalid/duplicate trophy definition";return;}if(d.trigger==TrophyTrigger::SecretCard&&(d.owner_id.empty()||d.card_index<0||!d.secret)){error_="Secret card must bind an actual owner/card";return;}if(d.trigger==TrophyTrigger::ExperienceStat&&d.stat_key.empty()){error_="Experience threshold requires a real statistic key";return;}}
    for(const auto& d:definitions)if(d.trigger==TrophyTrigger::AllOtherTrophies&&++ultimate>1){error_="Only one ultimate all-other-trophies definition is allowed";return;}
    definitions_=std::move(definitions);
    commit(state_);
}
std::uint64_t Trophies::progress(const TrophyDefinition& d,const State& s)const {
    switch(d.trigger){
    case TrophyTrigger::VisitCount:return s.visited.size();
    case TrophyTrigger::AllCatalogSnapshot:{std::unordered_set<std::string> seen(s.visited.begin(),s.visited.end());std::uint64_t n=0;for(const auto& id:s.snapshot)if(seen.count(id))++n;return n;}
    case TrophyTrigger::AllOtherTrophies:{std::uint64_t n=0;for(const auto& other:definitions_)if(other.id!=d.id&&s.unlocked.count(other.id))++n;return n;}
    case TrophyTrigger::SecretCard:return contains(s.seen_cards,cardKey(d.owner_id,d.card_index))?1:0;
    case TrophyTrigger::FirstMusic:return s.first_music?1:0;
    case TrophyTrigger::FirstVideo:return s.first_video?1:0;
    case TrophyTrigger::MaximumZoom:return s.max_zoom?1:0;
    case TrophyTrigger::FirstCulture:return s.culture.empty()?0:1;
    case TrophyTrigger::FirstToday:return s.first_today?1:0;
    case TrophyTrigger::ExperienceStat:{auto i=s.stats.find(d.stat_key);return i==s.stats.end()?0:i->second;}
    }return 0;
}
bool Trophies::commit(State next) {
    if(!writable_){error_="Trophy state remains protected after load failure";return false;}
    std::vector<TrophyUnlock> events;const auto now=std::uint64_t(std::max<std::time_t>(0,std::time(nullptr)));
    // Evaluate ordinary requirements first, then the single ultimate. A definition
    // reorder must never delay the ultimate or award it before the final unlock.
    for(unsigned pass=0;pass<2;++pass)for(const auto& d:definitions_)if(!next.unlocked.count(d.id)&&
        (d.trigger==TrophyTrigger::AllOtherTrophies)==(pass==1)){
        const auto target=d.trigger==TrophyTrigger::AllCatalogSnapshot?next.snapshot.size():
            d.trigger==TrophyTrigger::AllOtherTrophies?definitions_.size()-1:d.target;
        if(target&&progress(d,next)>=target){next.unlocked[d.id]=now;events.push_back({d.id,d.title,d.description,d.badge,d.rank,now});}
    }
    auto encoded=encode(next);if(encoded==encode(state_))return false;
    State validated;if(!decode(encoded,validated)){error_="Trophy state exceeds its bounded version1 format";return false;}
    std::string old;State checked;
    if(read(path_,old)&&decode(old,checked)&&!atomic(path_+".bak",old)){error_="Could not preserve trophy backup";return false;}
    if(!atomic(path_,encoded)){error_="Could not persist trophy progress";return false;}
    state_=std::move(next);pending_.insert(pending_.end(),events.begin(),events.end());error_.clear();return true;
}
bool Trophies::reset(){
    if(!writable_){error_="Trophy state remains protected after load failure";return false;}
    State fresh;fresh.snapshot=state_.snapshot;
    if(encode(fresh)!=encode(state_)&&!commit(std::move(fresh)))return false;
    pending_.clear();error_.clear();return true;
}
bool Trophies::setEligibleCatalogSnapshot(const std::vector<std::string>& ids){if(!state_.snapshot.empty())return false;State n=state_;for(const auto& id:ids)add(n.snapshot,id);return n.snapshot.empty()?false:commit(std::move(n));}
bool Trophies::visit(const std::string& id){if(id.empty()||contains(state_.visited,id))return false;State n=state_;if(!add(n.visited,id))return false;return commit(std::move(n));}
bool Trophies::card(const std::string& id,int index){if(id.empty()||index<0)return false;bool bound=false;for(const auto& d:definitions_)if(d.trigger==TrophyTrigger::SecretCard&&d.owner_id==id&&d.card_index==index)bound=true;if(!bound||contains(state_.seen_cards,cardKey(id,index)))return false;State n=state_;if(!add(n.seen_cards,cardKey(id,index)))return false;return commit(std::move(n));}
bool Trophies::musicProgress(const std::string& session,double seconds,bool ended){if(state_.first_music||session.empty()||!std::isfinite(seconds)||seconds<=0||(!ended&&seconds<10))return false;State n=state_;n.first_music=true;return commit(std::move(n));}
bool Trophies::videoProgress(const std::string& session,double seconds,bool ended){if(state_.first_video||session.empty()||!std::isfinite(seconds)||seconds<=0||(!ended&&seconds<30))return false;State n=state_;n.first_video=true;return commit(std::move(n));}
bool Trophies::zoomMaximum(){if(state_.max_zoom)return false;State n=state_;n.max_zoom=true;return commit(std::move(n));}
bool Trophies::cultureVisit(const std::string& id){if(id.empty()||contains(state_.culture,id))return false;State n=state_;if(!add(n.culture,id))return false;return commit(std::move(n));}
bool Trophies::todayVisit(const std::string& id){if(state_.first_today||id.empty())return false;State n=state_;n.first_today=true;return commit(std::move(n));}
bool Trophies::experienceResult(const std::string& id,const std::map<std::string,std::uint64_t>& stats){
    if(id.empty())return false;
    bool changed=false;
    for(const auto& p:stats)if(!p.first.empty()&&p.second){
        const auto found=state_.stats.find(id+":"+p.first);
        if(found==state_.stats.end()||found->second<p.second){changed=true;break;}
    }
    if(!changed)return false;
    State n=state_;
    for(const auto& p:stats)if(!p.first.empty()&&p.second)n.stats[id+":"+p.first]=std::max(n.stats[id+":"+p.first],p.second);
    return commit(std::move(n));
}
std::vector<TrophyView> Trophies::views(bool reveal_secrets)const {
    std::vector<TrophyView> out;for(const auto& d:definitions_){TrophyView v;v.id=d.id;v.badge=d.badge;v.rank=d.rank;v.secret=d.secret;auto u=state_.unlocked.find(d.id);v.unlocked=u!=state_.unlocked.end();if(v.unlocked)v.unlocked_at=u->second;if(reveal_secrets||!d.secret||v.unlocked){v.title=d.title;v.description=d.description;v.hint=d.hint;v.target=d.trigger==TrophyTrigger::AllCatalogSnapshot?state_.snapshot.size():d.trigger==TrophyTrigger::AllOtherTrophies?definitions_.size()-1:d.target;v.current=std::min(progress(d,state_),v.target);}out.push_back(std::move(v));}return out;
}
std::vector<TrophyUnlock> Trophies::drainUnlocks(){std::vector<TrophyUnlock> out;out.swap(pending_);return out;}
std::size_t Trophies::visitedCount()const{return state_.visited.size();}
} // namespace museum
