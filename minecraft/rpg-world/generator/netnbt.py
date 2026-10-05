import struct
def varint(b, o):
    r=0; s=0
    while True:
        x=b[o]; o+=1
        r|=(x&0x7f)<<s; s+=7
        if not x&0x80: return r,o
def zz(n): return (n>>1)^-(n&1)
def rstr(b,o):
    n,o=varint(b,o); return b[o:o+n].decode('utf8'),o+n
def payload(t,b,o):
    if t==1: return struct.unpack_from('b',b,o)[0],o+1
    if t==2: return struct.unpack_from('<h',b,o)[0],o+2
    if t==3: v,o=varint(b,o); return zz(v),o
    if t==4: v,o=varint(b,o); return zz(v),o
    if t==5: return struct.unpack_from('<f',b,o)[0],o+4
    if t==6: return struct.unpack_from('<d',b,o)[0],o+8
    if t==8: return rstr(b,o)
    if t==9:
        et=b[o]; o+=1; n,o=varint(b,o); n=zz(n); l=[]
        for _ in range(n): v,o=payload(et,b,o); l.append(v)
        return l,o
    if t==10:
        d={}
        while True:
            tt=b[o]; o+=1
            if tt==0: return d,o
            k,o=rstr(b,o); v,o=payload(tt,b,o); d[k]=v
    raise Exception('tag %d'%t)
def load_all(path):
    b=open(path,'rb').read(); o=0; out=[]
    while o<len(b):
        t=b[o]; o+=1; _,o=rstr(b,o); v,o=payload(t,b,o); out.append(v)
    return out
