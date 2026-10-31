"""Pixel Museum original interface sound design. No imported SFX or recordings.

New damped resonators, felt transients and filtered-noise gestures accompany
the original score's D-minor/F-major instruments. All destinations stay in
this review folder until root integrates the approved bank.
"""
from pathlib import Path
import hashlib,json,math,re,subprocess,sys,wave
import numpy as np
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[1]; P=ROOT/'build/research/interface-audio-original-20261031'; SR=48000
sys.path.insert(0,str(ROOT/'music'))
import compose as score
score.SR=SR
BANK=P/'bank/glass'; PAD=P/'controller'; PREVIEW=P/'preview'
for d in [BANK,PAD,PREVIEW]:d.mkdir(parents=True,exist_ok=True)
def hz(n):return 440*2**((n-69)/12)
def env(t,attack,decay,end):
 return (1-np.exp(-t/attack))*np.exp(-t/decay)*np.minimum(1,np.maximum(0,(end-t)/.012))**2
def noise(t,seed,lo=350,hi=3300):
 rng=np.random.default_rng(seed);x=rng.standard_normal(len(t));f=np.fft.rfftfreq(len(t),1/SR)
 filt=(1-np.exp(-(f/lo)**4))/np.sqrt(1+(f/hi)**8)
 x=np.fft.irfft(np.fft.rfft(x)*filt,n=len(t));return x/(np.sqrt(np.mean(x*x))+1e-12)
def tap(t,f=380,decay=.020,seed=1):
 # A damped contact, not an oscillator carrying a sustained musical note.
 x=sum(a*np.sin(2*np.pi*f*r*t)*np.exp(-t/(decay/(1+i*.8)))for i,(r,a)in enumerate([(1,1),(2.73,.17),(5.18,.045)]))
 return x*env(t,.0009,decay,t[-1])+.22*noise(t,seed,650,3600)*env(t,.0006,.003,t[-1])
def brush(t,seed=2,rise=False):
 d=t[-1];shape=env(t,.004,.035,d)
 if rise:shape=(np.sin(np.pi*np.minimum(t/max(d-.018,.001),1))**2)*np.minimum(1,(d-t)/.018)
 return noise(t,seed,350,2700)*shape
def felt(t,note=74,decay=.05):
 f=hz(note);phase=2*np.pi*f*t
 x=np.sin(phase+.28*np.exp(-t/.018)*np.sin(phase*2))+.06*np.sin(phase*3)*np.exp(-t/.02)
 return x*env(t,.0025,decay,t[-1])
def put(dst,x,at,gain=1):
 i=int(at*SR);n=min(len(x),len(dst)-i)
 if n>0:dst[i:i+n]+=x[:n]*gain
def key(dst,note,at,duration,gain):
 # The app's actual original felt/FM instrument, newly articulated here.
 put(dst,score.voice(note,duration,'keys',6,note),at,gain)
def stereo(x,width=.10):
 out=np.column_stack((x,x))*.70710678
 for delay,gain,side in[(.005,.08,1),(.011,.045,0)]:
  k=int(delay*SR)
  if len(x)>k:out[k:,side]+=x[:-k]*gain*width/.10
 return out
def finish(x,peak):
 x=np.asarray(x,float);x-=np.mean(x,axis=0)
 n=min(120,len(x));r=np.sin(np.linspace(0,np.pi/2,n))**2
 x[:n]*=r[:,None]if x.ndim==2 else r
 n=min(720,len(x));r=np.linspace(1,0,n)**2
 x[-n:]*=r[:,None]if x.ndim==2 else r
 x*=peak/max(float(np.max(np.abs(x))),1e-8);x[0]=x[-1]=0
 return x
def write(path,x):
 pcm=np.rint(np.clip(x,-1,1)*32767).astype('<i2')
 with wave.open(str(path),'wb')as w:
  w.setnchannels(2 if x.ndim==2 else 1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
 return {'file':str(path.relative_to(P)).replace('\\','/'),'seconds':len(x)/SR,'channels':2 if x.ndim==2 else 1,'peak_dbfs':round(20*np.log10(max(np.max(np.abs(x)),1e-12)),2),'rms_dbfs':round(20*np.log10(max(np.sqrt(np.mean(x*x)),1e-12)),2),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

LENGTHS={'focus':.060,'select':.190,'back':.150,'tab':.170,'open':.260,'modal_open':.210,'modal_close':.170,'toggle':.095,'slider':.050,'error':.190,'notify':.540,'launch':.420,'favorite_on':.300,'favorite_off':.230,'saved':.310,'welcome':.760,'resume':.240,'type':.048,'erase':.065,'tick':.032}
SFX_UI_ALIASES={'type','erase','tick'}
PEAKS={'focus':.28,'slider':.23,'toggle':.29,'error':.27,'notify':.35,'welcome':.35,'launch':.36}
DESIGN={
 'focus':'small felt contact with short damped wooden modes',
 'select':'two tactile contacts and a quiet felt-key bloom',
 'back':'soft return contact followed by a disappearing cloth tail',
 'tab':'sideways paper-like brush with a compact resonant landing',
 'open':'rising airy envelope and a warm three-part felt bloom',
 'modal_open':'cushioned latch followed by a sheltered interior resonance',
 'modal_close':'shorter closing contact with a low damping tail',
 'toggle':'dry two-part latch with no sustained note',
 'slider':'very short restrained granular detent',
 'error':'low soft double knock, no alarm or abrasive buzzer',
 'notify':'three warm score-aligned partials over a light brushed swell',
 'launch':'a widening air gesture settling into the original felt timbre',
 'favorite_on':'a small bright fleck joining a warm contact',
 'favorite_off':'the same material with a shorter descending release',
 'saved':'two settled contacts and a stable D/A resonance',
 'welcome':'a brief open D-minor/add-nine felt signature',
 'resume':'a cushioned forward contact with a small breath of air',
 'type':'small felt keycap contact, short enough to avoid stacking at fast typing rates',
 'erase':'a short brushed release of a keycap',
 'tick':'a fine muted detent for small UI values'}

def weighted_window_level(x):
 # Ungated K-weighted 32ms maximum RMS, suitable for these short transients.
 # Never uses the loudness gate intended for long programmes.
 if x.ndim==2:x=x.mean(axis=1)
 f=np.fft.rfftfreq(len(x),1/SR);z=np.exp(-2j*np.pi*f/SR)
 h=(1.53512485958697-2.69169618940638*z+1.19839281085285*z*z)/(1-1.69065929318241*z+.73248077421585*z*z)
 h*=(1-2*z+z*z)/(1-1.99004745483398*z+.99007225036621*z*z)
 y=np.fft.irfft(np.fft.rfft(x)*h,n=len(x));n=min(round(.032*SR),len(y))
 sums=np.cumsum(np.r_[0,y*y]);return float(np.sqrt(np.max((sums[n:]-sums[:-n])/n)))

def calibrate(cue,x):
 # Reference is the accepted timeline step: UI bus .18, event gain .6.
 ref=make('focus',0);target=weighted_window_level(ref*.18*.6)
 event_gain=.6 if cue in ['focus','slider','tick']else 1.
 bus=1. if cue in SFX_UI_ALIASES else .18
 if cue in ['notify','welcome','launch']:target*=10**(-1.5/20)
 if cue in ['type','erase']:target*=10**(-.7/20)
 factor=target/max(weighted_window_level(x*bus*event_gain),1e-12)
 factor=min(factor,.65/max(float(np.max(np.abs(x))),1e-9))
 return x*factor,{'bus_gain':bus,'reference_event_gain':event_gain,'linear_calibration_gain':factor,'post_route_k32_dbfs':round(20*np.log10(max(weighted_window_level(x*factor*bus*event_gain),1e-12)),2)}

def make(cue,v=0):
 d=LENGTHS[cue];t=np.arange(round(d*SR))/SR;x=np.zeros(len(t));seed=1729+v*317+list(LENGTHS).index(cue)*71
 contact=lambda at,f=380,dec=.021,g=1:put(x,tap(t,f,dec,seed),at,g)
 if cue=='focus':contact(0,410+v*9,.012,.9);x+=.08*brush(t,seed)
 elif cue=='type':contact(0,570+v*8,.009,.70);x+=.10*brush(t,seed)
 elif cue=='erase':contact(0,410,.010,.56);x+=.22*brush(t,seed)
 elif cue=='tick':contact(0,525+v*6,.005,.50)
 elif cue=='slider':contact(0,590+v*13,.006,.75);x+=.15*brush(t,seed)
 elif cue=='select':
  contact(0,370,.018,.7);contact(.032,630,.012,.23);key(x,74,.013,.155,.42);key(x,81,.038,.135,.16)
 elif cue=='back':
  contact(0,410+v*7,.012,.65);contact(.022,370,.010,.24)
  key(x,74,.006,.085,.20);key(x,69,.025,.065,.09)
 elif cue=='tab':x+=.60*brush(t,seed,True);contact(.026,455+v*5,.018,.6);key(x,74,.032,.12,.11)
 elif cue=='open':
  x+=.27*brush(t,seed,True);contact(.010,330,.025,.35)
  for at,n,g in[(.019,62,.19),(.043,69,.20),(.070,76,.15)]:key(x,n,at,.18,g)
 elif cue=='modal_open':contact(0,315,.026,.7);contact(.021,560,.018,.22);key(x,69,.027,.17,.16)
 elif cue=='modal_close':contact(0,400,.017,.5);contact(.025,290,.021,.6);x+=.13*brush(t,seed)
 elif cue=='toggle':contact(0,690,.007,.7);contact(.019,390,.010,.8);x+=.09*brush(t,seed)
 elif cue=='error':contact(0,180,.022,.65);contact(.048,158,.018,.5);x+=.09*brush(t,seed)
 elif cue in['notify','welcome']:
  x+=.08*brush(t,seed,True)
  notes=[(0,69),(.075,74),(.145,81)]if cue=='notify'else[(0,62),(.075,69),(.145,76),(.21,77)]
  for at,n in notes:key(x,n,at,d-at-.02,.22)
  contact(0,470,.012,.12)
 elif cue=='launch':
  x+=.23*brush(t,seed,True)
  for at,n in[(.025,62),(.068,69),(.12,81)]:key(x,n,at,d-at-.02,.18)
 elif cue=='favorite_on':contact(0,520,.015,.45);key(x,77,.015,.22,.17);key(x,81,.060,.20,.20)
 elif cue=='favorite_off':contact(0,470,.014,.45);key(x,77,.012,.19,.17);key(x,74,.047,.16,.13)
 elif cue=='saved':contact(0,355,.016,.45);contact(.047,355,.012,.25);key(x,62,.025,.26,.12);key(x,69,.060,.23,.14)
 elif cue=='resume':contact(0,365,.020,.6);x+=.12*brush(t,seed,True);key(x,74,.030,.18,.14)
 return finish(stereo(x),PEAKS.get(cue,.33))

def gun(mono=False):
 d=.115;t=np.arange(round(d*SR))/SR
 # A rapid exponential voltage drop gives the blast a beginning and body.
 # No fixed musical note is held. Noise supplies the sharp muzzle transient.
 f0=1700.;f1=105.;k=48.;phase=2*np.pi*(f1*t+(f0-f1)*(1-np.exp(-k*t))/k)
 body=np.tanh(1.45*(np.sin(phase+.52*np.sin(phase*.5))+.18*np.sin(phase*2)))
 body*=env(t,.0007,.024,d)
 hiss=noise(t,42042,1000,6500)*env(t,.00018,.0045,d)
 tail=noise(t,42043,450,2800)*env(t,.0015,.019,d)
 x=.80*body+.32*hiss+.12*tail
 return finish(x if mono else stereo(x,.045),.44)

def speaker(cue):
 if cue=='invader_shot':return gun(True)
 name={'ui_focus':'focus','ui_confirm':'select','ui_back':'back','timeline_culture':'open','timeline_games':'tab'}[cue]
 s=make(name).mean(axis=1)
 if cue=='timeline_games':s=np.concatenate((s,np.zeros(int(.06*SR))))
 # The tiny pad speaker benefits from keeping the useful midrange present.
 f=np.fft.rfftfreq(len(s),1/SR);spec=np.fft.rfft(s)
 spec*=(1-np.exp(-(f/350)**4))/np.sqrt(1+(f/4600)**8)
 return finish(np.fft.irfft(spec,n=len(s)),.34)

def startup():
 d=.38;t=np.arange(round(d*SR))/SR
 # A4 root is retained for the intro's existing pitch multiplier contract.
 return finish(.90*felt(t,69,.095)+.04*tap(t,880,.007,501),.34)

def main():
 clips=[];sounds={}
 for cue in LENGTHS:
  count=3 if cue in['focus','slider','type']else 2 if cue in['select','back','tab','toggle','erase','tick']else 1
  for v in range(count):
   name=f'{cue}_{v+1:02}';x,cal=calibrate(cue,make(cue,v));sounds[name]=x;row=write(BANK/(name+'.wav'),x);row.update(cue=cue,variation=v+1,design=DESIGN[cue],calibration=cal);clips.append(row)
 shot=gun();sounds['invader_shot_01']=shot;row=write(BANK/'invader_shot_01.wav',shot);row.update(cue='invader_shot',scope='explicit gameplay exception, accepted player shots only');clips.append(row)
 (BANK/'index.txt').write_text('\n'.join(sorted(x.name for x in BANK.glob('*.wav')))+'\n',encoding='ascii')
 pad=[]
 for cue in['ui_focus','ui_confirm','ui_back','timeline_culture','timeline_games','startup_pixel','invader_shot']:
  x=startup()if cue=='startup_pixel'else speaker(cue)
  if cue not in['startup_pixel','invader_shot']:
   gain=.14 if cue.startswith('timeline_')else .085
   target=weighted_window_level(speaker('ui_focus')*.085)
   if cue.startswith('timeline_'):target*=10**(-1/20)
   factor=target/max(weighted_window_level(x*gain),1e-12)
   x*=min(factor,.60/max(float(np.max(np.abs(x))),1e-9))
  pad.append(dict(cue=cue,**write(PAD/(cue+'.wav'),x)))
 # Listening reference applies one fixed monitor gain to the actual UI bus.
 out=np.zeros((round(46*SR),2));events=[]
 def event(at,name,label,gain=1):
  bus=1. if name.rsplit('_',1)[0]in SFX_UI_ALIASES else .18
  x=sounds[name]*bus*gain; i=round(at*SR);out[i:i+len(x)]+=x;events.append({'seconds':at,'event':label,'clip':name,'runtime_bus_gain':bus,'event_gain':gain})
 for i in range(5):event(.35+i*.19,f'focus_{i%3+1:02}','Timeline / card movement',.6)
 seq=[(1.8,'select','Confirm'),(2.8,'back','Return'),(3.8,'tab','Decade / filter'),(4.9,'open','Open panel'),(6.0,'modal_open','Open settings'),(7.0,'modal_close','Close dialog'),(8.0,'toggle','Toggle'),(10.0,'error','Unavailable action'),(11.2,'notify','Museum notification'),(12.8,'favorite_on','Favourite on'),(13.9,'favorite_off','Favourite off'),(15.0,'saved','Saved'),(16.1,'resume','Resume content'),(17.2,'launch','Launch'),(18.5,'welcome','Welcome')]
 for at,name,label in seq:event(at,name+'_01',label)
 for i in range(6):event(8.8+i*.095,f'slider_{i%3+1:02}','Fine slider / image zoom',.6)
 for j,cue in enumerate(['ui_focus','ui_confirm','ui_back','timeline_culture','timeline_games']):
  f=PAD/(cue+'.wav')
  with wave.open(str(f),'rb')as w:x=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(float)/32768
  gain=.14 if cue.startswith('timeline_')else .085
  at=20+j*.72;i=round(at*SR);out[i:i+len(x)]+=stereo(x)*gain;events.append({'seconds':at,'event':'DualSense '+cue,'reference_gain':gain})
 # End with the app's real score and ordinary navigation at its runtime level.
 ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();bedfile=ROOT/'music/eras/1990.ogg'
 p=subprocess.run([ffmpeg,'-v','error','-i',str(bedfile),'-t','8','-f','f32le','-ar',str(SR),'-ac','2','pipe:1'],stdout=subprocess.PIPE,check=True)
 bed=np.frombuffer(p.stdout,'<f4').reshape(-1,2).astype(float);n=min(len(bed),8*SR)
 bed=bed[:n]*.32;bed[:SR//4]*=np.linspace(0,1,SR//4)[:,None];bed[-SR//2:]*=np.linspace(1,0,SR//2)[:,None];out[25*SR:25*SR+n]+=bed
 events.append({'seconds':25,'event':'Original museum 1990 score plus UI, runtime-relative balance','music_file':'music/eras/1990.ogg','music_gain':.32})
 for i in range(7):event(25.7+i*.22,f'focus_{i%3+1:02}','Navigation over museum score',.6)
 event(27.8,'select_01','Confirm over museum score');event(29,'tab_01','Filter over museum score');event(30.3,'back_01','Back over museum score')
 for at in[34.2,35.2,35.39,35.58]:
  i=round(at*SR);out[i:i+len(shot)]+=shot*.20;events.append({'seconds':at,'event':'Space Invaders accepted shot — explicit exception','clip':'invader_shot_01','preview_gain':.20,'runtime_sfx_bus':1,'recommended_event_gain':.20})
 for i in range(10):event(38.0+i*.11,f'focus_{i%3+1:02}','Keyboard focus, same reference as timeline',.6)
 for i in range(12):event(39.5+i*.09,f'type_{i%3+1:02}','Rapid typing — original SFX bus compensated')
 for i in range(10):event(41.2+i*.09,f'erase_{i%2+1:02}','Held backspace — original SFX bus compensated')
 event(42.6,'select_01','Search confirmation')
 for i in range(5):event(43.5+i*.15,f'focus_{i%3+1:02}','Return to ordinary navigation',.6)
 out*=3.2;peak=float(np.max(np.abs(out)));assert peak<.94,peak
 preview=write(PREVIEW/'Pixel Museum - Original Interface Preview.wav',out)
 subprocess.run([ffmpeg,'-v','error','-y','-i',str(PREVIEW/'Pixel Museum - Original Interface Preview.wav'),'-codec:a','libmp3lame','-b:a','192k',str(PREVIEW/'Pixel Museum - Original Interface Preview.mp3')],check=True)
 result={'sample_rate':SR,'bits':16,'ui_channels':2,'controller_channels':1,'source':'Entirely original DSP, using the app composer’s own felt/FM timbre as one quiet layer; no ProsperoUI audio files, recordings or downloaded assets.','music_references':['music/compose.py','music/compose_culture.py','music/compose_onboarding.py','music/compose_home.py'],'ui_semantic_cues':list(LENGTHS),'ui_cue_count':len(LENGTHS),'controller_ui_cue_count':6,'gameplay_exception':'Space Invaders player shot only','preserve_existing_gameplay':['all other SpeakerCue values','all study sound(note) calls','experience_audio scores','restart_01.wav used by the legacy workshop'],'ui_clips':clips,'controller_clips':pad,'preview':preview,'preview_fixed_monitor_gain':3.2,'preview_timeline':sorted(events,key=lambda r:r['seconds']),'recommended_ui_bus_gain':.18,'loudness_method':'Ungated K-weighted 32ms maximum RMS after actual bus gain and typical event gain. Longer signatures are 1.5dB below reference, typing/deletion 0.7dB below. No compressor, gating or limiter. Short key tails avoid overlap at keyboard repeat_interval0.09s.','routing_discovery':'Cue::type, erase and tick use SFX bus gain1 while navigation uses UI bus0.18 and event gain0.4–0.6; missing recordings formerly selected loud fallback tones. New aliases are calibrated for their real SFX routing.','integration_notes':['Keep SoundBank pitch jitter disabled.','Merge index.txt with unchanged legacy restart_01.wav if replacing the active bank directory.','The invader_shot filename needs its own Cue enum/table entry; do not replace MIDI note76 globally.','Only startup events with pixel_ordinal>=0 may use the new startup timbre; other study notes retain their existing route.','Native PS5 trophy notifications use system psfx names and are not ProsperoUI bank clips.']}
 (P/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'ui_cues':len(LENGTHS),'wav_files':len(clips),'controller_clips':len(pad),'preview':preview['file'],'preview_peak_dbfs':preview['peak_dbfs']},indent=2))
if __name__=='__main__':main()
