from pathlib import Path
import struct,zlib
out=Path("build/photo-fixtures");out.mkdir(exist_ok=True)
def png(name,w,h,row):
 def chunk(t,b):return struct.pack(">I",len(b))+t+b+struct.pack(">I",zlib.crc32(t+b)&0xffffffff)
 compressor=zlib.compressobj();parts=[]
 for y in range(h):parts.append(compressor.compress(b"\0"+row(w,y)))
 parts.append(compressor.flush());data=chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))+chunk(b"IDAT",b"".join(parts))+chunk(b"IEND",b"")
 (out/name).write_bytes(b"\x89PNG\r\n\x1a\n"+data)
png("native-4k.png",3840,2160,lambda w,y:bytes([0,255,0,255] if y%2 else [255,0,0,255])*w)
png("wide.png",5120,2000,lambda w,y:bytes([0,0,255,255])*w)
png("small.png",200,100,lambda w,y:bytes([0,0,255,255])*w)
png("square.png",4096,4096,lambda w,y:bytes([120,40,80,255])*w)
png("medium.png",2048,2048,lambda w,y:bytes([120,40,80,255])*w)
# Header alone suffices for dimension preflight: no large decoder allocation.
sig=b"\x89PNG\r\n\x1a\n";data=struct.pack(">IIBBBBB",16384,8192,8,6,0,0,0);(out/"over-budget.png").write_bytes(sig+struct.pack(">I",len(data))+b"IHDR"+data+struct.pack(">I",zlib.crc32(b"IHDR"+data)&0xffffffff))
