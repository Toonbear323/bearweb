"""Where every region sits.  All numbers are world coordinates (x east, z south)."""
import numpy as np

from mcw import B
from gen_common import fbm, smoothstep
from rpg_world import World, blob, poly_mask, poly_floor, X0, Z0, SX, SZ, SEA, G

# region centres / key points (also used by the area builders)
SPAWN_C = (0, -2)
FARM_C = (-132, -8)
VILLAGE_C = (0, 222)
HQ_C = (-146, 226)
CRATER_C = (193, 516)
NETHER_BOX = (138, 286, 252, 424)          # x1, z1, x2, z2 of the volcano / nether cavern
DEEPDARK_BOX = (-14, 456, 108, 590)
CAVE_BOX = (-44, 60, 50, 160)
MONUMENT_C = (-122, 404)

PASS_FARM = [(-44, -5), (-62, -9), (-80, -10), (-98, -8)]
PASS_FARM_H = [64, 69, 69, 64]
PASS_HQ = [(-54, 226), (-70, 229), (-86, 229), (-104, 227)]
PASS_HQ_H = [64, 69, 69, 65]
PASS_BEACH = [(22, 276), (22, 284), (22, 294), (22, 312)]
PASS_BEACH_H = [64, 70, 70, 65]


def shore_z(x):
    """z of the waterline for the beach (land is north of it)."""
    return 342 + 6 * np.sin(x / 19.0) + 4 * np.sin(x / 7.3 + 1.3)


def define_regions(W: World):
    X, Z = W.X, W.Z
    s = W.seed
    W.add_region("spawn", blob(X, Z, *SPAWN_C, 54, 50, p=2.6, amp=0.08, seed=s + 1), G, 0, "plains")
    W.add_region("farm", blob(X, Z, *FARM_C, 46, 44, p=2.6, amp=0.08, seed=s + 2), G, 0, "plains")
    W.add_region("village", blob(X, Z, *VILLAGE_C, 62, 56, p=2.8, amp=0.08, seed=s + 3), G, 0, "plains")
    W.add_region("hq", blob(X, Z, *HQ_C, 52, 56, p=2.6, amp=0.10, seed=s + 4), G + 1, 0, "roofed_forest")
    # passes are flat so the gatehouses built on them sit level
    for name, pts, w, hs in (("pass_farm", PASS_FARM, 11, PASS_FARM_H), ("pass_hq", PASS_HQ, 11, PASS_HQ_H),
                             ("pass_beach", PASS_BEACH, 11, PASS_BEACH_H)):
        m = poly_mask(X, Z, pts, w)
        r = W.add_region(name, m, poly_floor(X, Z, pts, hs, m), 0)
        W.regions[name]["flat"] = True
    # coast: beach strip + bay
    bay = blob(X, Z, -58, 382, 150, 76, p=2.3, amp=0.07, seed=s + 6)
    strip = blob(X, Z, 62, 328, 66, 32, p=3.2, amp=0.05, seed=s + 7)
    coast = (bay | strip) & (Z >= 296)
    sz = shore_z(X.astype(float))
    land = (Z < sz) & (X > -56)
    dsh = np.clip(Z - sz, 0, None)                      # distance seaward (approx.)
    # west of the beach the bay touches the hills directly: measure from x too
    dsh = np.where(X <= -56, np.maximum(dsh, (-56 - X) * 0.9 + np.clip(Z - 300, 0, None) * 0.2), dsh)
    n = fbm(SX, SZ, 16, 3, s + 8)
    seabed = SEA - 1 - np.minimum(dsh * 0.55, 34) - (n - 0.5) * 3
    seabed = np.maximum(seabed, 27)
    beachfl = SEA + 1 + np.clip((sz - Z) / 9.0, 0, 3)
    floor = np.where(land, beachfl, np.minimum(seabed, SEA - 2))
    W.add_region("coast", coast, floor, 1, "beach", top=B("sand"), sub=B("sand"))
    W.regions["coast"]["flat"] = True
    W.regions["coast"]["noclamp"] = True
    ocean = coast & ~land
    W.a.bio[ocean] = 40                                  # warm ocean
    W.a.bio[ocean & (seabed < 40)] = 24                  # deep ocean
    W.ocean = ocean
    W.water[ocean] = SEA
    W.land_beach = coast & land
    # demon castle crater
    W.add_region("crater", blob(X, Z, *CRATER_C, 64, 66, p=2.3, amp=0.09, seed=s + 9), G + 2, 3,
                 "basalt_deltas", top=B("blackstone"), sub=B("blackstone"))
    W.regions["crater"]["flat"] = True
    W.regions["crater"]["noclamp"] = True
    # mountains must cover the underground regions
    x1, z1, x2, z2 = CAVE_BOX
    W.min_h[W.rect(x1 - 6, z1 + 12, x2 + 6, z2 - 14)] = 86
    W.min_h[W.rect(-8, 150, 34, 161)] = 82            # cliff holding the cave exit gallery
    W.min_h[W.rect(-10, 49, 10, 66)] = 80              # cliff above the cave entrance
    x1, z1, x2, z2 = DEEPDARK_BOX
    W.min_h[W.rect(x1 - 6, z1 - 4, x2 + 6, z2 + 6)] = 72
    x1, z1, x2, z2 = NETHER_BOX
    W.min_h[W.rect(x1, z1, x2, z2)] = 114


def post_terrain(W: World):
    """Mountain styles that do not follow the nearest valley: the volcano and the dark lands."""
    X, Z = W.X, W.Z
    mount = W.open_id == 0
    x1, z1, x2, z2 = NETHER_BOX
    cx, cz = (x1 + x2) / 2, (z1 + z2) / 2
    d = np.sqrt(((X - cx) / ((x2 - x1) / 2 + 14)) ** 2 + ((Z - cz) / ((z2 - z1) / 2 + 14)) ** 2)
    volc = mount & (d < 1.0)
    W.style[volc] = 2
    n = fbm(SX, SZ, 12, 3, W.seed + 40)
    cone = 150 - d * 30 + (n - 0.5) * 10
    W.H = np.where(volc, np.maximum(W.H, np.minimum(cone, 152)).astype(np.int32), W.H)
    # summit crater of the volcano (shallow dip, still solid above the cavern)
    top = volc & (d < 0.18)
    W.H[top] = np.minimum(W.H[top], 138)
    x1, z1, x2, z2 = DEEPDARK_BOX
    n2 = fbm(SX, SZ, 20, 2, W.seed + 41)
    dark = mount & (Z + (n2 - 0.5) * 36 > z1 - 14) & (X + (n - 0.5) * 36 > x1 - 34)
    W.style[dark] = 3
