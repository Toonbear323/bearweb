"""Voxel sculpting -> Bedrock cubes.

A Vox is a real 3D voxel volume (occupancy + a colour per voxel for its side / top / bottom
faces).  Volumes are sculpted with 3D shape functions, shaded with baked ambient occlusion and
then merged into as few boxes as possible (greedy meshing).  Only faces that are actually
exposed are exported.

Grid convention (same as the reference art grid): voxel (i, j, k) covers
  columns  c0 + i*s .. c0 + (i+1)*s      (model X = column - CX)
  rows     r0 + j*s .. r0 + (j+1)*s      (model Y = GY - row, rows run downward)
  depth    z0 + k*s .. z0 + (k+1)*s      (model Z, -Z = front)
"""
import numpy as np

CX, GY = 28.0, 46.0
#            name      index step that lies in front of the face
DIRS = {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (-1, 0, 0), 'west': (1, 0, 0), 'up': (0, -1, 0), 'down': (0, 1, 0)}


class Vox:
    def __init__(self, c0, c1, r0, r1, z0, z1, s=1.0):
        self.c0, self.r0, self.z0, self.s = c0, r0, z0, s
        self.nx, self.ny, self.nz = int(round((c1 - c0) / s)), int(round((r1 - r0) / s)), int(round((z1 - z0) / s))
        shp = (self.nx, self.ny, self.nz)
        self.occ = np.zeros(shp, bool)
        self.col = np.zeros(shp + (3,))        # side faces
        self.colU = np.zeros(shp + (3,))       # top faces
        self.colD = np.zeros(shp + (3,))       # bottom faces
        self.dec = np.zeros(shp, bool)         # front face carries a fine decal
        i, j, k = np.meshgrid(np.arange(self.nx), np.arange(self.ny), np.arange(self.nz), indexing='ij')
        self.I, self.J, self.K = i, j, k
        self.C = c0 + (i + .5) * s             # column / row / depth of every voxel centre
        self.R = r0 + (j + .5) * s
        self.Z = z0 + (k + .5) * s

    # ---- sculpting
    def add(self, mask, col=None, up=None, down=None):
        self.occ |= mask
        if col is not None:
            self.paint(mask, col, up, down)

    def cut(self, mask):
        self.occ &= ~mask

    def paint(self, mask, col, up=None, down=None):
        col = np.broadcast_to(col, self.col.shape)
        self.col[mask] = col[mask]
        self.colU[mask] = (np.broadcast_to(up, self.col.shape) if up is not None else col)[mask]
        self.colD[mask] = (np.broadcast_to(down, self.col.shape) if down is not None else col * 0.8)[mask]

    def front(self):
        """mask of the first occupied voxel of every (column,row) seen from the front"""
        cum = np.cumsum(self.occ, axis=2)
        return self.occ & (cum == 1)

    def back(self):
        cum = np.cumsum(self.occ[:, :, ::-1], axis=2)[:, :, ::-1]
        return self.occ & (cum == 1)

    def surface(self):
        p = np.pad(self.occ, 1)
        inner = p[2:, 1:-1, 1:-1] & p[:-2, 1:-1, 1:-1] & p[1:-1, 2:, 1:-1] & p[1:-1, :-2, 1:-1] & p[1:-1, 1:-1, 2:] & p[1:-1, 1:-1, :-2]
        return self.occ & ~inner

    # ---- baked ambient occlusion (one value per voxel face)
    def bake_ao(self, strength=0.55):
        p = np.pad(self.occ, 2).astype(float)
        self.ao = {}
        for name, d in DIRS.items():
            axes = [a for a in range(3) if d[a] == 0]

            def sh(di, dj, dk):
                return p[2 + di:2 + di + self.nx, 2 + dj:2 + dj + self.ny, 2 + dk:2 + dk + self.nz]
            e = np.zeros(self.occ.shape)
            c = np.zeros(self.occ.shape)
            for a in (-1, 1):
                for ax in axes:
                    o = list(d)
                    o[ax] += a
                    e += sh(*o)
                for b in (-1, 1):
                    o = list(d)
                    o[axes[0]] += a
                    o[axes[1]] += b
                    c += sh(*o)
            self.ao[name] = np.clip(1 - strength * (0.10 * e + 0.045 * c), 0.72, 1.0)

    # ---- greedy meshing
    def boxes(self):
        occ = self.occ
        done = np.zeros_like(occ)
        out = []
        for j in range(self.ny):
            for k in range(self.nz):
                i = 0
                while i < self.nx:
                    if not occ[i, j, k] or done[i, j, k]:
                        i += 1
                        continue
                    i1 = i + 1
                    while i1 < self.nx and occ[i1, j, k] and not done[i1, j, k]:
                        i1 += 1
                    k1 = k + 1
                    while k1 < self.nz and (occ[i:i1, j, k1] & ~done[i:i1, j, k1]).all():
                        k1 += 1
                    j1 = j + 1
                    while j1 < self.ny and (occ[i:i1, j1, k:k1] & ~done[i:i1, j1, k:k1]).all():
                        j1 += 1
                    done[i:i1, j:j1, k:k1] = True
                    out.append((i, i1, j, j1, k, k1))
                    i = i1
        return out

    def exposed(self, b):
        i0, i1, j0, j1, k0, k1 = b
        o = self.occ
        f = []
        if k0 == 0 or not o[i0:i1, j0:j1, k0 - 1].all():
            f.append('north')
        if k1 == self.nz or not o[i0:i1, j0:j1, k1].all():
            f.append('south')
        if i0 == 0 or not o[i0 - 1, j0:j1, k0:k1].all():
            f.append('east')
        if i1 == self.nx or not o[i1, j0:j1, k0:k1].all():
            f.append('west')
        if j0 == 0 or not o[i0:i1, j0 - 1, k0:k1].all():
            f.append('up')
        if j1 == self.ny or not o[i0:i1, j1, k0:k1].all():
            f.append('down')
        return f

    # ---- export
    def painter(self, decal=None):
        s = self

        def f(ctx):
            P = ctx.P
            N = ctx.N
            h = s.s * 0.5
            i = np.clip(np.floor((P[..., 0] - N[0] * h + CX - s.c0) / s.s).astype(int), 0, s.nx - 1)
            j = np.clip(np.floor((GY - (P[..., 1] - N[1] * h) - s.r0) / s.s).astype(int), 0, s.ny - 1)
            k = np.clip(np.floor((P[..., 2] - N[2] * h - s.z0) / s.s).astype(int), 0, s.nz - 1)
            arr = s.colU if ctx.face == 'up' else (s.colD if ctx.face == 'down' else s.col)
            rgb = arr[i, j, k]
            if ctx.face == 'north' and decal is not None:
                m = s.dec[i, j, k]
                if m.any():
                    rgb = np.where(m[..., None], decal(P[..., 0] + CX, GY - P[..., 1]), rgb)
            return rgb * s.ao[ctx.face][i, j, k][..., None]
        return f

    def emit(self, bone, decal=None):
        """add the volume to a mclib Bone as merged boxes; returns the number of cubes"""
        self.bake_ao()
        mat = self.painter(decal)
        n = 0
        tex = int(round(1 / self.s))          # one texel per voxel
        for b in self.boxes():
            faces = self.exposed(b)
            if not faces:
                continue
            i0, i1, j0, j1, k0, k1 = b
            s = self.s
            hasdec = decal is not None and 'north' in faces and self.dec[i0:i1, j0:j1, k0].any()
            bone.box(self.c0 + i0 * s - CX, GY - (self.r0 + j1 * s), self.z0 + k0 * s,
                     self.c0 + i1 * s - CX, GY - (self.r0 + j0 * s), self.z0 + k1 * s,
                     mat, faces=tuple(faces), d=(4 if hasdec else tex), ds=tex)
            n += 1
        return n
