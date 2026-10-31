"""One ordinary metadata request; no retries, media downloads or stream URL storage.

Browser authentication must be explicitly authorized before using --browser.
"""
from pathlib import Path
import argparse,json,re,subprocess
from datetime import datetime, timezone, timedelta

def decode(raw):
    try:return raw.decode('utf-8-sig')
    except UnicodeDecodeError:return raw.decode('cp1252',errors='replace')

def failure(text):
    s=text.lower()
    if '429' in s or 'too many requests' in s:return 'RATE_LIMITED'
    if 'sign in to confirm' in s and 'bot' in s:return 'AUTHENTICATION_REQUIRED'
    if 'private video' in s:return 'PRIVATE_VIDEO'
    if 'video unavailable' in s or 'video has been removed' in s:return 'UNAVAILABLE'
    if 'timed out' in s:return 'NETWORK_TIMEOUT'
    return 'EXTRACTOR_ERROR'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('video_id');p.add_argument('--output',type=Path,required=True)
    p.add_argument('--browser',choices=['chrome','edge','firefox'])
    p.add_argument('--extractor',type=Path,default=Path('C:/Users/Andrea/homebrew/plugins/themedeck/yt-dlp.exe'))
    a=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]{11}',a.video_id)
    root=Path(__file__).resolve().parents[1];out=a.output.resolve()
    if not out.is_relative_to(root/'build/research') or out.exists():p.error('Use a new receipt inside build/research')
    rate_state=root/'build/research/youtube-metadata-rate-limit-state.json'
    now=datetime.now(timezone.utc)
    if rate_state.exists():
        state=json.loads(rate_state.read_text(encoding='utf8'))
        if datetime.fromisoformat(state['retry_after_utc'])>now:
            result={'requested_id':a.video_id,'requested_at_utc':now.isoformat(),'status':'RATE_LIMIT_COOLDOWN','aac_format_observed':False,'metadata_only':True,'media_downloaded':False,'external_request_made':False,'retry_after_utc':state['retry_after_utc']}
            out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            print(json.dumps(result,ensure_ascii=False));return
    cmd=[str(a.extractor),'--ignore-config','--dump-single-json','--skip-download','--no-playlist','--retries','0','--fragment-retries','0','--extractor-retries','0','--socket-timeout','12']
    if a.browser:cmd+=['--cookies-from-browser',a.browser]
    cmd+=['https://www.youtube.com/watch?v='+a.video_id]
    result={'requested_id':a.video_id,'requested_at_utc':now.isoformat(),'metadata_only':True,'media_downloaded':False,'browser_auth_requested':bool(a.browser),'external_request_made':True}
    try:
        r=subprocess.run(cmd,capture_output=True,timeout=65)
        # Read bytes first: Windows CP1252 errors must never crash a reader thread.
        stdout,stderr=decode(r.stdout),decode(r.stderr)
        try:data=json.loads(stdout)
        except json.JSONDecodeError:data=None
        if r.returncode==0 and isinstance(data,dict):
            result.update({k:data.get(k)for k in ['id','title','description','channel','channel_id','duration','availability','upload_date','chapters']})
            formats=data.get('formats')or[]
            result['aac_format_observed']=any(str(f.get('acodec','')).startswith('mp4a')for f in formats)
            result['avc_format_observed']=any(str(f.get('vcodec','')).startswith('avc1')for f in formats)
            result['status']='PUBLIC_METADATA_FORMATS_VERIFIED'if result['aac_format_observed']else'METADATA_NO_AAC_FORMAT'
        else:
            result.update(status=failure(stderr),returncode=r.returncode,aac_format_observed=False)
        # Keep diagnostic text, excluding any lines that could expose account data.
        result['diagnostic_lines']=[line for line in stderr.splitlines()if not any(k in line.lower()for k in ['cookie','token','authorization','password'])][-12:]
    except subprocess.TimeoutExpired:result.update(status='NETWORK_TIMEOUT',aac_format_observed=False)
    if result.get('status')=='RATE_LIMITED':
        state={'status':'RATE_LIMITED','last_rate_limit_utc':datetime.now(timezone.utc).isoformat(),'retry_after_utc':(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat(),'trigger_video_id':a.video_id,'trigger_receipt':out.relative_to(root).as_posix()}
        rate_state.parent.mkdir(parents=True,exist_ok=True);rate_state.write_text(json.dumps(state,indent=2)+'\n',encoding='utf8')
    elif result.get('status')=='PUBLIC_METADATA_FORMATS_VERIFIED' and rate_state.exists():
        state=json.loads(rate_state.read_text(encoding='utf8'));state.update(status='RECOVERED',recovered_at_utc=datetime.now(timezone.utc).isoformat(),last_success_video_id=a.video_id,last_success_receipt=out.relative_to(root).as_posix())
        rate_state.write_text(json.dumps(state,indent=2)+'\n',encoding='utf8')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:result[k]for k in ['requested_id','status','aac_format_observed']},ensure_ascii=False))

if __name__=='__main__':main()
