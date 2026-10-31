#!/usr/bin/env python3
"""Remove a redundant static glTF skin only after checking every bind matrix.

Original positions, normals, indices and embedded image bytes are unchanged.
A source with animation or a non-identity bind correction is rejected.
"""
from pathlib import Path
import hashlib
import json
import math
import struct
import sys

IDENTITY=[1.,0,0,0,0,1.,0,0,0,0,1.,0,0,0,0,1.]
def multiply(a,b):return [sum(a[k*4+r]*b[c*4+k] for k in range(4)) for c in range(4) for r in range(4)]
def local_matrix(node):
    if "matrix" in node:return node["matrix"]
    x,y,z,w=node.get("rotation",[0,0,0,1]);sx,sy,sz=node.get("scale",[1,1,1]);t=node.get("translation",[0,0,0])
    return [(1-2*y*y-2*z*z)*sx,(2*x*y+2*w*z)*sx,(2*x*z-2*w*y)*sx,0,(2*x*y-2*w*z)*sy,(1-2*x*x-2*z*z)*sy,(2*y*z+2*w*x)*sy,0,(2*x*z+2*w*y)*sz,(2*y*z-2*w*x)*sz,(1-2*x*x-2*y*y)*sz,0,*t,1]
def inverse(matrix):
    rows=[[matrix[c*4+r]for c in range(4)]+[float(c==r)for c in range(4)]for r in range(4)]
    for col in range(4):
        pivot=max(range(col,4),key=lambda row:abs(rows[row][col]));rows[col],rows[pivot]=rows[pivot],rows[col]
        factor=rows[col][col]
        if abs(factor)<1e-12:raise ValueError("Singular node transform")
        rows[col]=[value/factor for value in rows[col]]
        for row in range(4):
            if row!=col:
                factor=rows[row][col];rows[row]=[a-factor*b for a,b in zip(rows[row],rows[col])]
    return [rows[row][4+col]for col in range(4)for row in range(4)]
def prepare(source,target):
    data=source.read_bytes()
    if len(data)>160*1024*1024:raise ValueError("Source exceeds the runtime document limit")
    magic,version,total=struct.unpack_from("<III",data)
    if magic!=0x46546c67 or version!=2 or total!=len(data):raise ValueError("Not a complete GLB2")
    json_length,json_kind=struct.unpack_from("<II",data,12)
    if json_kind!=0x4e4f534a:raise ValueError("Missing JSON chunk")
    document=json.loads(data[20:20+json_length])
    binary_header=20+json_length
    binary_length,binary_kind=struct.unpack_from("<II",data,binary_header)
    if binary_kind!=0x004e4942 or binary_header+8+binary_length!=len(data):raise ValueError("Unsupported GLB chunks")
    binary=data[binary_header+8:]
    if document.get("animations"):raise ValueError("Animated poses require actual skinning; refusing to flatten")
    nodes=document["nodes"];world={};visiting=set()
    def walk(index,parent):
        if index in visiting:raise ValueError("Cyclic scene")
        visiting.add(index);world[index]=multiply(parent,local_matrix(nodes[index]))
        for child in nodes[index].get("children",[]):walk(child,world[index])
        visiting.remove(index)
    for root in document["scenes"][document.get("scene",0)]["nodes"]:walk(root,IDENTITY)
    largest=0.;skinned=0
    for index,node in enumerate(nodes):
        if "skin" not in node:continue
        if index not in world:raise ValueError("Skinned node outside the default scene")
        skin=document["skins"][node["skin"]];accessor=document["accessors"][skin["inverseBindMatrices"]]
        view=document["bufferViews"][accessor["bufferView"]]
        if accessor["type"]!="MAT4" or accessor["componentType"]!=5126 or accessor["count"]!=len(skin["joints"]) or "sparse" in accessor:raise ValueError("Unsupported bind accessor")
        offset=view.get("byteOffset",0)+accessor.get("byteOffset",0);stride=view.get("byteStride",64)
        inv_node=inverse(world[index])
        for joint_index,joint in enumerate(skin["joints"]):
            bind=struct.unpack_from("<16f",binary,offset+joint_index*stride)
            correction=multiply(multiply(inv_node,world[joint]),bind)
            difference=max(abs(a-b)for a,b in zip(correction,IDENTITY))
            if not math.isfinite(difference) or difference>2e-5:raise ValueError(f"Nontrivial bind correction: {difference}")
            largest=max(largest,difference)
        skinned+=1
    if not skinned:raise ValueError("Source has no redundant skin")
    for node in nodes:node.pop("skin",None)
    document.pop("skins",None)
    for mesh in document.get("meshes",[]):
        for primitive in mesh.get("primitives",[]):
            attributes=primitive.get("attributes",{})
            for key in list(attributes):
                if key.startswith("JOINTS_") or key.startswith("WEIGHTS_"):del attributes[key]
    note="Redundant static bind-pose skin declarations removed after numerical identity verification. No animations were present. Original vertex, normal, index, UV and embedded image bytes are unchanged."
    document.setdefault("asset",{}).setdefault("extras",{})["pixel_museum_modification"]=note
    encoded=json.dumps(document,ensure_ascii=False,separators=(",",":")).encode("utf-8");encoded+=b" "*((-len(encoded))%4)
    output=struct.pack("<III",0x46546c67,2,12+8+len(encoded)+8+len(binary))+struct.pack("<II",len(encoded),0x4e4f534a)+encoded+struct.pack("<II",len(binary),0x004e4942)+binary
    target.write_bytes(output)
    report={"source_file":source.name,"source_sha256":hashlib.sha256(data).hexdigest(),"derived_file":target.name,"derived_sha256":hashlib.sha256(output).hexdigest(),"binary_chunk_sha256":hashlib.sha256(binary).hexdigest(),"binary_chunk_identical":True,"skinned_mesh_nodes":skinned,"maximum_bind_matrix_difference":largest,"modifications":note}
    target.with_suffix(".modifications.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
if __name__=="__main__":prepare(Path(sys.argv[1]),Path(sys.argv[2]))
