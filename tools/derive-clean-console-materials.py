#!/usr/bin/env python3
"""Non-generative UV-scoped material variants; no raster/geometry modification.

Original embedded image bytes and geometric buffers are retained exactly.
The original BY-NC-SA source masters remain in models/. The optional extras
are interpreted by Pixel Museum; other glTF viewers retain the original look.
"""
from pathlib import Path
import json,struct,hashlib
r=Path(__file__).resolve().parents[1];p=r/'models/derivations';p.mkdir(exist_ok=True)
settings={
'playstation-3':{
'Main_Body_Plastic':{'regions':[[0,0,.4,.52],[.48,0,1,.47]],'preserve':[[.065,.25,.315,.035]],'linear_colour_roughness':[.003,.003,.003,.18]},
'SideBack_Plastic':{'regions':[[.03,.045,.505,.64],[.52,.03,.918,.52]],'preserve':[],'linear_colour_roughness':[.008,.008,.008,.48]}},
'playstation-4':{
'Plastic_Smooth_Base':{'regions':[[0,.485,.80,.852]],'preserve':[[.028,.76,.105,.835],[.735,.57,.765,.63]],'linear_colour_roughness':[.002,.002,.002,.19]},
'Plastic_Grain_Base':{'regions':[[0,0,.79,.50]],'preserve':[[.015,.09,.06,.20]],'linear_colour_roughness':[.0035,.0035,.0035,.64]}}
}
# Rectangles are min-u,min-v,max-u,max-v in the original source atlas.
settings['playstation-3']['Main_Body_Plastic']['preserve']=[[.065,.25,.38,.29],[.495,.41,.99,.46],[.935,.04,.99,.14],[.935,.30,.99,.39]]
for materials in settings.values():
 for material in materials.values():material['preserve_ink']=[]
settings['playstation-3']['Main_Body_Plastic']['preserve_ink']=[settings['playstation-3']['Main_Body_Plastic']['preserve'].pop(0)]
for material in settings['playstation-4'].values():material['preserve_ink']=material['preserve'];material['preserve']=[]
settings['playstation-3']['Main_Body_Plastic']['regions'].append([0,.58,.448,.70])
settings['playstation-3']['Main_Body_Plastic']['preserve_ink'].append([.14,.667,.44,.695])
settings['playstation-4']['Plastic_Base_Bottom']={'regions':[[0,0,.86,.885]],'preserve':[[.27,.077,.525,.13]],'preserve_ink':[],'linear_colour_roughness':[.0035,.0035,.0035,.64]}
settings['playstation-4']['Plastic_Grain_Base']['preserve_ink']=[[.019,.095,.045,.124],[.019,.126,.045,.159],[.019,.160,.045,.188]]
expected={'playstation-3':'4c25029960e3e7a85466d22d53fa457d8ca97425c1dfe8f8ac72dad2a1aa7226','playstation-4':'ec9a1b59d13014be00a3e5b0d26b62681ea3043f934c80cc61290c1ee1fd00eb'}
for name,materials in settings.items():
 src=r/'models'/f'{name}.glb';b=src.read_bytes();assert hashlib.sha256(b).hexdigest()==expected[name],'Source version changed; UV restoration must be re-reviewed'
 n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);binary=b[20+n:]
 for m in j['materials']:
  if m.get('name') in materials:m.setdefault('extras',{})['museum_surface_restore']=materials[m['name']]
 data=json.dumps(j,separators=(',',':')).encode('utf8');data+=b' '*((-len(data))%4)
 out=struct.pack('<III',0x46546c67,2,20+len(data)+len(binary))+struct.pack('<II',len(data),0x4e4f534a)+data+binary
 target=r/'models'/f'{name}-clean-surface.glb';target.write_bytes(out)
 assert binary==out[20+len(data):]
 receipt={'source':src.relative_to(r).as_posix(),'source_sha256':hashlib.sha256(b).hexdigest(),'derived':target.relative_to(r).as_posix(),'derived_sha256':hashlib.sha256(out).hexdigest(),'license':'CC BY-NC-SA 4.0','creator':'Smoggybeard','changes':'Conventional non-generative UV-scoped material restoration. All embedded texture bytes, geometry, topology, UVs, decals and original masters retained byte-for-byte; selected shell surface weathering is masked at render time. Protected wordmark/label UV regions remain authored.','materials':materials,'status':'DERIVED_AWAITING_RENDER_RECEIPT'}
 (p/f'{name}-clean-surface.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print(name,len(out))
