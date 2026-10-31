#!/usr/bin/env python3
"""Generate original neutral glTF material fixtures; no museum asset changes."""
from pathlib import Path
import json,math,struct,zlib
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"build/material-fixtures";OUT.mkdir(exist_ok=True)
def png(width,height,pixels):
 def chunk(kind,data):return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
 raw=b"".join(b"\0"+bytes(pixels[y*width*4:(y+1)*width*4]) for y in range(height))
 return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",width,height,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(raw))+chunk(b"IEND",b"")
def srgb(c):return round(255*(12.92*c if c<=.0031308 else 1.055*c**(1/2.4)-.055))
def decode(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def expected(base,metal,rough,ao=1):
 # Independent numerical evaluation of the neutral front-facing swatch.
 nv=1.;result=0.;f0=.04*(1-metal)+base*metal
 for direction,radiance in [((-.65,.85,1.2),3.1),((.8,.15,.6),.70),((-.4,.25,-1.),.30)]:
  length=math.sqrt(sum(x*x for x in direction));l=[x/length for x in direction];nl=max(l[2],0)
  if nl==0:continue
  h=[l[0],l[1],l[2]+1];length=math.sqrt(sum(x*x for x in h));h=[x/length for x in h];nh=h[2];vh=nh
  alpha=rough*rough;a2=alpha*alpha;d=a2/(math.pi*(nh*nh*(a2-1)+1)**2)
  vis=.5/(nl*math.sqrt(nv*nv*(1-a2)+a2)+nv*math.sqrt(nl*nl*(1-a2)+a2))
  fresnel=f0+(1-f0)*(1-vh)**5
  result+=((1-fresnel)*(1-metal)*base/math.pi+fresnel*d*vis)*radiance*nl
 result+=((1-f0)*(1-metal)*base*.51+f0*.51*(1-.5*rough))*ao
 return srgb(min(result,1))
def make(name,material,texture=None,sampler=None,uv=(.5,.5),mirror=False,tangent_sign=1,expected_rgb=None,stats=None,uv1=None,required=False,error=None,note=None):
 data=bytearray();views=[];access=[]
 def add(raw,component,count,kind):
  data.extend(b"\0"*((-len(data))%4));offset=len(data);data.extend(raw);views.append({"buffer":0,"byteOffset":offset,"byteLength":len(raw)});access.append({"bufferView":len(views)-1,"componentType":component,"count":count,"type":kind});return len(access)-1
 positions=[-.6,-.6,0,.6,-.6,0,.6,.6,0,-.6,.6,0]
 attributes={"POSITION":add(struct.pack("<12f",*positions),5126,4,"VEC3"),"NORMAL":add(struct.pack("<12f",*([0,0,1]*4)),5126,4,"VEC3"),"TEXCOORD_0":add(struct.pack("<8f",*(list(uv) if len(uv)==8 else list(uv)*4)),5126,4,"VEC2"),"TANGENT":add(struct.pack("<16f",*([1,0,0,tangent_sign]*4)),5126,4,"VEC4")}
 if uv1 is not None:attributes["TEXCOORD_1"]=add(struct.pack("<8f",*(list(uv1)*4)),5126,4,"VEC2")
 indices=add(struct.pack("<6H",0,1,2,0,2,3),5123,6,"SCALAR")
 doc={"asset":{"version":"2.0"},"scene":0,"scenes":[{"nodes":[0]}],"nodes":[{"mesh":0}],"meshes":[{"primitives":[{"attributes":attributes,"indices":indices,"material":0}]}],"materials":[material],"bufferViews":views,"accessors":access}
 if required:doc["extensionsRequired"]=["KHR_materials_specular"]
 if mirror:doc["nodes"][0]["scale"]=[-1,1,1]
 if texture:
  image=png(*texture);data.extend(b"\0"*((-len(data))%4));views.append({"buffer":0,"byteOffset":len(data),"byteLength":len(image)});data.extend(image)
  doc["images"]=[{"bufferView":len(views)-1,"mimeType":"image/png"}];doc["textures"]=[{"source":0,"sampler":0}];doc["samplers"]=[sampler or {"magFilter":9729,"minFilter":9729}]
 doc["buffers"]=[{"byteLength":len(data)}];data.extend(b"\0"*((-len(data))%4))
 encoded=json.dumps(doc,separators=(",",":")).encode();encoded+=b" "*((-len(encoded))%4)
 (OUT/(name+".glb")).write_bytes(struct.pack("<III",0x46546c67,2,28+len(encoded)+len(data))+struct.pack("<II",len(encoded),0x4e4f534a)+encoded+struct.pack("<II",len(data),0x004e4942)+data)
 return {"file":name+".glb","expected_rgb":expected_rgb,"expected_stats":stats or {},"expected_error":error,"expected_note":note}
unlit={"pbrMetallicRoughness":{"baseColorFactor":[.18,.18,.18,1]},"extensions":{"KHR_materials_unlit":{}},"emissiveFactor":[1,1,1]}
cases=[make("unlit-linear-factor",unlit,expected_rgb=[srgb(.18)]*3)]
base={"pbrMetallicRoughness":{"baseColorTexture":{"index":0}},"extensions":{"KHR_materials_unlit":{}}}
redblue=(2,1,[255,0,0,255,0,0,255,255])
cases.append(make("srgb-linear-filter",base,redblue,expected_rgb=[188,0,188]))
cases.append(make("srgb-nearest-filter",base,redblue,{"magFilter":9728,"minFilter":9728},expected_rgb=[0,0,255]))
cases.append(make("repeat-nearest",base,redblue,{"magFilter":9728,"minFilter":9728,"wrapS":10497},uv=(1.25,.5),expected_rgb=[255,0,0]))
cases.append(make("clamp-nearest",base,redblue,{"magFilter":9728,"minFilter":9728,"wrapS":33071},uv=(1.25,.5),expected_rgb=[0,0,255]))
# A512-pixel checker is minified in the actual renderer: mip filtering must
# average sRGB in linear light rather than retaining nearest black pixels.
checker=(512,512,[v for y in range(512) for x in range(512) for v in ([255,255,255,255] if (x+y)%2 else [0,0,0,255])])
cases.append(make("srgb-mip-checker",base,checker,{"magFilter":9729,"minFilter":9987},expected_rgb=[188,188,188]))
for metal in [0,1]:
 for rough in [.15,.5,1]:
  value=expected(.18,metal,rough);cases.append(make(f"metal-{metal}-rough-{rough}",{"pbrMetallicRoughness":{"baseColorFactor":[.18,.18,.18,1],"metallicFactor":metal,"roughnessFactor":rough}},expected_rgb=[value]*3))
for strength in [0,.5,1]:
 material={"pbrMetallicRoughness":{"baseColorFactor":[.18,.18,.18,1],"metallicFactor":0,"roughnessFactor":1},"occlusionTexture":{"index":0,"strength":strength}}
 value=expected(.18,0,1,1-strength);cases.append(make(f"ambient-occlusion-{strength}",material,(1,1,[0,0,0,255]),expected_rgb=[value]*3,stats={"linear_textures":1,"srgb_textures":0}))
material={"pbrMetallicRoughness":{"baseColorFactor":[.18,.18,.18,1],"baseColorTexture":{"index":0},"metallicFactor":0,"roughnessFactor":1},"occlusionTexture":{"index":0}}
value=expected(.18*decode(128/255),0,1,128/255);cases.append(make("dual-colour-data",material,(1,1,[128,128,128,255]),expected_rgb=[value]*3,stats={"linear_textures":1,"srgb_textures":1,"dual_role_texture_bytes":4}))
material={"pbrMetallicRoughness":{"baseColorFactor":[.18,.18,.18,1],"metallicFactor":0,"roughnessFactor":1},"occlusionTexture":{"index":0,"texCoord":1}}
cases.append(make("occlusion-own-uv",material,(2,1,[0,0,0,255,255,255,255,255]),sampler={"magFilter":9728,"minFilter":9728},uv=(.25,.5),uv1=(.75,.5),expected_rgb=[expected(.18,0,1)]*3))
for mirror in [False,True]:
 material={"pbrMetallicRoughness":{"baseColorFactor":[.18,.18,.18,1],"metallicFactor":0,"roughnessFactor":1},"normalTexture":{"index":0}}
 cases.append(make("normal-mirrored" if mirror else "normal-authored",material,(1,1,[128,255,128,255]),mirror=mirror,stats={"tangent_vertices":4,"linear_textures":1}))

def specular_expected(factor,color,metal=0,rough=.5):
 # Separate reference integration: dielectric and metal lobes are mixed only
 # after max-channel dielectric energy has been removed from diffuse.
 base=.18;result=[0.,0.,0.];f0=[min(.04*c,1)*factor for c in color]
 for direction,radiance in [((-.65,.85,1.2),3.1),((.8,.15,.6),.70),((-.4,.25,-1.),.30)]:
  length=math.sqrt(sum(x*x for x in direction));l=[x/length for x in direction];nl=max(l[2],0)
  if not nl:continue
  h=[l[0],l[1],l[2]+1];length=math.sqrt(sum(x*x for x in h));vh=h[2]/length
  a2=rough**4;d=a2/(math.pi*(vh*vh*(a2-1)+1)**2);vis=.5/(nl+math.sqrt(nl*nl*(1-a2)+a2))
  dielectric=[f+(factor-f)*(1-vh)**5 for f in f0];mf=base+(1-base)*(1-vh)**5
  diffuse=(1-max(dielectric))*(1-metal)*base/math.pi
  for i in range(3):result[i]+=(diffuse+((1-metal)*dielectric[i]+metal*mf)*d*vis)*radiance*nl
 for i in range(3):result[i]+=((1-max(f0))*(1-metal)*base+((1-metal)*f0[i]+metal*base)*(1-.5*rough))*.51
 return [srgb(min(v,1)) for v in result]

def spec_material(factor=1,color=(1,1,1),metal=0):
 return {"pbrMetallicRoughness":{"baseColorFactor":[.18,.18,.18,1],"metallicFactor":metal,"roughnessFactor":.5},"extensions":{"KHR_materials_specular":{"specularFactor":factor,"specularColorFactor":list(color)}}}
for factor in [0,.657178,1]:
 cases.append(make(f"specular-factor-{factor}",spec_material(factor),expected_rgb=specular_expected(factor,(1,1,1))))
for name,color in [("zero",(0,0,0)),("tint",(4,.5,.1)),("saturated",(40,1,0)),("huge",(1e100,1,0))]:
 cases.append(make("specular-colour-"+name,spec_material(.7,color),expected_rgb=specular_expected(.7,color)))
for factor,color in [(0,(1,0,0)),(1,(40,1,0))]:
 cases.append(make(f"specular-metal-unchanged-{factor}",spec_material(factor,color,1),expected_rgb=specular_expected(factor,color,1)))
cases.append(make("specular-required-scalar",spec_material(.657178),required=True,expected_rgb=specular_expected(.657178,(1,1,1))))
for mapname in ["specularTexture","specularColorTexture"]:
 material=spec_material(.657178);material["extensions"]["KHR_materials_specular"][mapname]={"index":0}
 cases.append(make("specular-optional-"+mapname,material,note="KHR_materials_specular."+mapname,expected_rgb=specular_expected(.657178,(1,1,1))))
 cases.append(make("specular-required-"+mapname,material,required=True,error="texture maps are not supported"))
for name,factor,color in [("negative",-.1,(1,1,1)),("over-one",1.1,(1,1,1)),("string","bad",(1,1,1)),("negative-colour",1,(-1,1,1)),("short-colour",1,(1,1))]:
 cases.append(make("specular-invalid-"+name,spec_material(factor,color),error="Invalid GLB specular"))

# Shared-image role unions and exact sampled-channel packing regression cases.
for wrap in [10497,33071,33648]:
 for mip in [9729,9987]:
  image=(512,512,[v for y in range(512) for x in range(512) for v in ((x*17+y*3)%256,(x+y*11)%256,(x*7+y*5)%256,(x+y)%256)])
  mat={"pbrMetallicRoughness":{"baseColorFactor":[.4,.3,.2,1],"metallicRoughnessTexture":{"index":0}}}
  cases.append(make(f"packed-orm-{wrap}-{mip}",mat,image,{"magFilter":9729,"minFilter":mip,"wrapS":wrap,"wrapT":wrap},uv=(1.25,-.25)))
  mat["occlusionTexture"]={"index":0}
  cases.append(make(f"union-orm-ao-{wrap}-{mip}",mat,image,{"magFilter":9729,"minFilter":mip,"wrapS":wrap,"wrapT":wrap},uv=(1.25,-.25)))
  mat={"pbrMetallicRoughness":{"baseColorFactor":[.4,.3,.2,1],"metallicFactor":0,"roughnessFactor":1},"occlusionTexture":{"index":0}}
  cases.append(make(f"packed-ao-{wrap}-{mip}",mat,image,{"magFilter":9729,"minFilter":mip,"wrapS":wrap,"wrapT":wrap},uv=(1.25,-.25)))
# Constant maps must remain equivalent under real UV derivatives/minification,
# wrap modes, nearest/linear/mip sampling and colour/data role unions.
for wrap in [10497,33071,33648]:
 for mip in [9728,9729,9987]:
  sampler={"magFilter":9728 if mip==9728 else 9729,"minFilter":mip,"wrapS":wrap,"wrapT":wrap}
  for role in ["colour","orm","union"]:
   mat={"pbrMetallicRoughness":{"baseColorFactor":[.4,.3,.2,1]}}
   if role=="colour":mat["pbrMetallicRoughness"]["baseColorTexture"]={"index":0};mat["alphaMode"]="MASK";mat["alphaCutoff"]=.4
   else:mat["pbrMetallicRoughness"]["metallicRoughnessTexture"]={"index":0}
   if role=="union":mat["normalTexture"]={"index":0};mat["occlusionTexture"]={"index":0}
   cases.append(make(f"uniform-{role}-{wrap}-{mip}",mat,(512,512,[128,192,255,192]*(512*512)),sampler,uv=(-12,-12,24,-12,24,24,-12,24)))
almost=[128,192,255,192]*(512*512);almost[-4]=129
cases.append(make("notuniform-single-code-value",{"pbrMetallicRoughness":{"metallicRoughnessTexture":{"index":0}}},(512,512,almost),uv=(-12,-12,24,-12,24,24,-12,24)))

# A UV-scoped restoration must leave labelled areas and other UV islands
# byte-equivalent at the renderer output; original source texture is reused.
import copy
restore_base={"pbrMetallicRoughness":{"baseColorFactor":[1,1,1,1],"baseColorTexture":{"index":0}},"extensions":{"KHR_materials_unlit":{}},"extras":{"museum_surface_restore":{"regions":[[.1,.1,.9,.9]],"preserve":[[.4,.4,.6,.6]],"linear_colour_roughness":[.1,.2,.3,.4]}}}
original_pixel=(1,1,[30,100,200,255])
cases.append(make("surface-restore-panel",copy.deepcopy(restore_base),original_pixel,uv=(.25,.25),expected_rgb=[srgb(.1),srgb(.2),srgb(.3)]))
cases.append(make("surface-restore-protected-decal",copy.deepcopy(restore_base),original_pixel,uv=(.5,.5),expected_rgb=[30,100,200]))
cases.append(make("surface-restore-outside-island",copy.deepcopy(restore_base),original_pixel,uv=(.95,.95),expected_rgb=[30,100,200]))
m=copy.deepcopy(restore_base);m["extras"]["museum_surface_restore"]["preserve"]=[];m["extras"]["museum_surface_restore"]["preserve_ink"]=[[.4,.4,.6,.6]]
cases.append(make("surface-restore-preserve-ink",copy.deepcopy(m),original_pixel,uv=(.5,.5),expected_rgb=[30,100,200]))
cases.append(make("surface-restore-no-dark-logo-patch",copy.deepcopy(m),(1,1,[1,1,1,255]),uv=(.5,.5),expected_rgb=[srgb(.1),srgb(.2),srgb(.3)]))
for label,bad in [("reversed",[[.8,.1,.2,.9]]),("out-of-range",[[-.1,.1,.9,.9]]),("too-many",[[.1,.1,.9,.9]]*5)]:
 m=copy.deepcopy(restore_base);m["extras"]["museum_surface_restore"]["regions"]=bad
 cases.append(make("surface-restore-invalid-"+label,m,original_pixel,error="Invalid restoration UV rectangle"))
(OUT/"manifest.json").write_text(json.dumps({"cases":cases},indent=2)+"\n")
print(f"Generated {len(cases)} original neutral material fixtures")
