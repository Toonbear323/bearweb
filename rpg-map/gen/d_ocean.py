"""Ocean dungeon: harbour + lighthouse, glass sea-tunnel and the Sunken Temple of the Tide."""
import math

from . import blocks as bl
from . import dkit as dk
from . import houses, kit
from .core import B, Mix
from .kit import Frame
from .layout import BIO_WARM, HARBOR, SEA, TEMPLE

AIR = 0
PB = B("prismarine", prismarine_block_type="bricks")
PD = B("prismarine", prismarine_block_type="dark")
PR = B("prismarine", prismarine_block_type="default")
SL = B("sea_lantern")
GLASS = B("glass")
W = bl.WATER
CORALS = ["tube", "brain", "bubble", "fire", "horn"]


def pmix():
    return Mix((PB, 7), (PR, 3), (PD, 1))


def seabed(w, x, z):
    """y of the highest solid non-water block."""
    for y in range(SEA, w.y0, -1):
        b = w.get(x, y, z)
        if b not in (0, W) and not w.wl[x - w.x0, z - w.z0, y - w.y0]:
            return y
    return w.y0


def coral_patch(w, cx, cz, r, rng):
    for (dx, dz) in kit.disc_cells(r):
        if rng.random() > 0.55 * (1 - math.hypot(dx, dz) / (r + 1)):
            continue
        x, z = cx + dx, cz + dz
        y = seabed(w, x, z)
        if y > SEA - 4 or y < 12 or w.get(x, y + 1, z) != W:
            continue
        kind = CORALS[int(rng.integers(0, 5))]
        h = int(rng.integers(1, 4))
        for i in range(h):
            if w.get(x, y + 1 + i, z) == W:
                w.set(x, y + 1 + i, z, B(kind + "_coral_block"))
                w.water(x, y + 1 + i, z, False)
        ty = y + 1 + h
        if w.get(x, ty, z) == W and ty < SEA - 1:
            r_ = rng.random()
            k2 = CORALS[int(rng.integers(0, 5))]
            if r_ < 0.45:
                w.set(x, ty, z, B(k2 + "_coral"))
            elif r_ < 0.8:
                w.set(x, ty, z, B(k2 + "_coral_fan", coral_fan_direction=int(rng.integers(0, 2))))
            else:
                w.set(x, ty, z, B("sea_pickle", cluster_count=int(rng.integers(0, 4)), dead_bit=False))
            w.water(x, ty, z, True)


def lighthouse(w, cx, cz, g, rng):
    r = 4.5
    h = 30
    stone = Mix((bl.block("stone_brick"), 6), (bl.block("cobblestone"), 2), (bl.block("mossy_stone_brick"), 2))
    w.cyl(cx, cz, r + 2.0, g - 6, g + 1, stone)
    for (dx, dz) in kit._ring(r + 2.0):
        w.set(cx + dx, g + 2, cz + dz, bl.stairs("stone_brick", kit._inward(dx, dz)))
    for y in range(g + 2, g + 2 + h):
        band = ((y - g - 2) // 5) % 2
        rr = r - (y - g - 2) * 0.035
        for (dx, dz) in kit.disc_cells(rr):
            d = math.hypot(dx, dz)
            if d > rr - 1.15:
                w.set(cx + dx, y, cz + dz, B("white_concrete") if band == 0 else B("red_concrete"))
            else:
                w.set(cx + dx, y, cz + dz, AIR)
    for y in range(g + 2, g + 2 + h):
        w.set(cx, y, cz - 2, bl.ladder("S"))
    for fy in range(g + 8, g + h, 6):
        for (dx, dz) in kit.disc_cells(r - 1.6):
            if (dx, dz) != (0, -2):
                w.set(cx + dx, fy, cz + dz, bl.planks("spruce"))
        w.set(cx + 2, fy + 2, cz, bl.lantern())
        for (dx, dz) in ((3, 0), (-3, 0), (0, 3)):
            w.set(cx + dx, fy + 2, cz + dz, B("glass_pane"))
    # door (north side faces the shore road)
    w.set(cx, g + 2, cz - 4, AIR)
    w.set(cx, g + 3, cz - 4, AIR)
    w.set(cx, g + 2, cz - 3, AIR)
    w.set(cx, g + 3, cz - 3, AIR)
    w.set(cx, g + 2, cz - 2, AIR)
    w.set(cx, g + 3, cz - 2, AIR)
    for y in range(g + 4, g + 2 + h):
        w.set(cx, y, cz - 2, bl.ladder("S"))
    w.set(cx, g + 2, cz + 2, bl.ladder("N")) if False else None
    top = g + 2 + h
    # gallery
    for (dx, dz) in kit.disc_cells(r + 1.5):
        w.set(cx + dx, top, cz + dz, bl.block("stone_brick"))
    w.set(cx, top, cz - 2, bl.ladder("S"))
    for (dx, dz) in kit._ring(r + 1.5):
        w.set(cx + dx, top - 1, cz + dz, bl.stairs("stone_brick", kit._inward(dx, dz), top=True))
        w.set(cx + dx, top + 1, cz + dz, bl.fence("dark_oak"))
    # lamp room
    for y in range(top + 1, top + 5):
        for (dx, dz) in kit._ring(2.5):
            w.set(cx + dx, y, cz + dz, GLASS if y < top + 4 else bl.block("stone_brick"))
    w.set(cx, top + 1, cz, B("gold_block"))
    w.set(cx, top + 2, cz, SL)
    w.set(cx, top + 3, cz, B("glowstone"))
    w.set(cx, top + 1, cz - 2, AIR)
    w.set(cx, top + 2, cz - 2, AIR)
    Fw = Frame(w, 0, 0, 0, 0)
    kit.cone_roof(Fw, cx, cz, top + 5, 2.5, "deepslate_tile", steep=1, spire=[B("lightning_rod", facing_direction=1)])
    dk.sign(w, cx + 1, g + 3, cz - 5, "N", "§l베어 등대\n§r바다 던전 입구는\n부두 끝에 있습니다", wood="spruce")
    w.set(cx + 1, g + 3, cz - 4, B("white_concrete"))


def boat(w, x, z, rng):
    """Small moored fishing boat built from blocks (bow to the south)."""
    y = SEA
    hull = bl.planks("spruce")
    for i in range(-5, 6):
        half = 2 if abs(i) < 3 else (1 if abs(i) < 5 else 0)
        for dx in range(-half, half + 1):
            w.set(x + dx, y, z + i, hull)
            w.set(x + dx, y + 1, z + i, AIR)
        for dx in (-half - 1, half + 1):
            if half > 0 or True:
                w.set(x + dx, y + 1, z + i, bl.stairs("dark_oak", "E" if dx < 0 else "W", top=True) if False else bl.planks(
                    "dark_oak"))
                w.set(x + dx, y, z + i, bl.planks("dark_oak")) if half < 2 else None
    for dx in (-1, 0, 1):
        w.set(x + dx, y + 1, z - 5, bl.planks("dark_oak"))
        w.set(x + dx, y + 1, z + 5, bl.planks("dark_oak")) if dx == 0 else None
    for i in range(1, 9):
        w.set(x, y + i, z, bl.log("spruce"))
    for i in range(3, 8):
        for dx in range(-2, 3):
            if abs(dx) <= (8 - i) // 2 + 1:
                w.set(x + dx, y + i, z + 1, B("white_wool"))
    w.set(x, y + 9, z, bl.fence("spruce"))
    w.set(x + 1, y + 1, z - 3, bl.barrel("U"))
    w.put(x - 1, y + 1, z + 2, bl.chest("N"), bl.be_chest([bl.item("cod", 6), bl.item("fishing_rod"), bl.item("string", 4)]))
    kit.auto_waterlog(w, x - 4, y - 1, z - 6, x + 4, y + 1, z + 6)


def harbor(w, T, rng):
    hx, hz = HARBOR
    g = SEA + 2
    F = Frame(w, 0, 0, 0, 0)
    xi, zi = hx - 40 - w.x0, hz - 30 - w.z0
    T.reserved[xi:xi + 80, zi:zi + 90] = True
    deck_y = g
    # quay along the shore
    quay = Mix((bl.block("stone_brick"), 6), (bl.block("cobblestone"), 3), (bl.block("mossy_stone_brick"), 2),
               (bl.block("andesite"), 2))
    for x in range(hx - 24, hx + 25):
        for z in range(hz - 8, hz + 3):
            top = w.top(x, z)
            w.fill(x, min(top or g, g) - 4, z, x, g, z, quay)
            w.fill(x, g + 1, z, x, g + 20, z, AIR)
    for x in range(hx - 24, hx + 25, 6):
        w.set(x, g + 1, hz + 2, bl.wall("stone_brick"))
        w.set(x, g + 2, hz + 2, bl.lantern())
    # pier
    z_end = hz + 46
    for z in range(hz + 3, z_end + 1):
        wide = 7 if z > z_end - 12 else 3
        for x in range(hx - wide, hx + wide + 1):
            w.set(x, deck_y, z, bl.planks("spruce") if (x + z) % 7 else bl.planks("dark_oak"))
            w.fill(x, deck_y + 1, z, x, deck_y + 12, z, AIR)
        for sx in (-wide, wide):
            if (z - hz) % 6 == 0:
                x = hx + sx
                yb = seabed(w, x, z)
                for y in range(yb + 1, deck_y):
                    w.set(x, y, z, bl.log("spruce"))
                w.set(x, deck_y, z, bl.log("spruce"))
                w.set(x, deck_y + 1, z, bl.fence("spruce"))
                w.set(x, deck_y + 2, z, bl.lantern() if (z - hz) % 12 == 0 else bl.fence("spruce"))
            else:
                if not (z > z_end - 12 and z < z_end - 9):
                    w.set(hx + sx, deck_y + 1, z, bl.fence("spruce"))
    for x in range(hx - 7, hx + 8):
        for z in (z_end - 11, z_end):
            if abs(x - hx) > 3 or z == z_end:
                w.set(x, deck_y + 1, z, bl.fence("spruce"))
    kit.crate_pile(F, hx - 6, deck_y + 1, z_end - 9, rng, 5)
    kit.crate_pile(F, hx + 5, deck_y + 1, z_end - 3, rng, 4)
    lighthouse(w, hx - 17, hz - 3, g - 1, rng)
    # dock house
    Fh = Frame.box(w, hx + 9, g, hz - 22, 13, 11, "S")
    info = houses.shell(Fh, 13, 11, floors=2, pal=houses.palette("oak"), chimney=("E", 3), sign="§l항구 창고")
    houses.furnish_home(Fh, info)
    boat(w, hx + 13, hz + 14, rng)
    boat(w, hx - 12, hz + 22, rng)
    dk.sign(w, hx - 4, deck_y + 2, hz + 3, "N", "§3§l바다 던전\n§r부두 끝 유리 계단을\n내려가세요", wood="spruce", standing=True)
    return z_end, deck_y


def tube_ring(w, x0, floor_y, z, rib, lamp):
    """One slice of the glass sea-tunnel centred on x0."""
    for x in range(x0 - 2, x0 + 3):
        w.set(x, floor_y, z, PB if abs(x - x0) < 2 else PD)
        w.water(x, floor_y, z, False)
        for y in range(floor_y + 1, floor_y + 5):
            edge = abs(x - x0) == 2 or y == floor_y + 4
            w.set(x, y, z, (PB if rib else GLASS) if edge else AIR)
            w.water(x, y, z, False)
    if rib:
        w.set(x0 - 2, floor_y + 4, z, PD)
        w.set(x0 + 2, floor_y + 4, z, PD)
        w.set(x0, floor_y + 4, z, SL)
    if lamp:
        w.set(x0, floor_y, z, SL)


def build(w, T, log=print):
    rng = w.rng
    tx, tz = TEMPLE
    z_end, deck_y = harbor(w, T, rng)
    pm = pmix()
    FLOOR = 37                           # dry floor level of atrium / vault
    xi, zi = tx - 48 - w.x0, z_end - 2 - w.z0
    T.reserved[xi:xi + 96, zi:min(w.sz, tz + 102 - w.z0)] = True
    # warm ocean biome for the reef basin
    for (dx, dz) in kit.disc_cells(105):
        xx, zz = tx + dx, tz + dz + 20
        if w.x0 <= xx < w.x1 and w.z0 <= zz < w.z1 and w.biome[xx - w.x0, zz - w.z0] in (0, 24):
            w.biome[xx - w.x0, zz - w.z0] = BIO_WARM
    # ------------------------------------------------------------------ glass stairway + tunnel
    z0 = z_end + 3
    # entrance pavilion on the pier head
    for (dx, dz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        for y in range(deck_y + 1, deck_y + 5):
            w.set(tx + dx, y, z_end - 4 + dz, B("quartz_block", chisel_type="lines", pillar_axis="y"))
    Fw = Frame(w, 0, 0, 0, 0)
    kit.hip_roof(Fw, tx - 3, z_end - 7, tx + 3, z_end - 1, deck_y + 5, "dark_prismarine", overhang=1,
                 cap="dark_prismarine")
    w.set(tx, deck_y + 4, z_end - 4, bl.lantern(True)) if False else None
    w.fill(tx - 2, deck_y, z_end - 6, tx + 2, deck_y, z_end - 2, PB)
    w.set(tx, deck_y, z_end - 4, SL)
    # stair mouth: cut through the pier head
    n_down = deck_y - FLOOR
    zs = z_end - 1
    for i in range(n_down + 1):
        z = zs + i
        fy = deck_y - i
        tube_ring(w, tx, fy, z, rib=(i % 4 == 0), lamp=False)
        for x in range(tx - 2, tx + 3):             # solid layer under the steps keeps the sea out
            w.set(x, fy - 1, z, PD)
            w.water(x, fy - 1, z, False)
        for x in (tx - 1, tx, tx + 1):
            w.set(x, fy, z, B("prismarine_bricks_stairs", weirdo_direction=3, upside_down_bit=False) if i > 0 else PB)
        if fy + 4 >= deck_y:
            for x in range(tx - 1, tx + 2):
                for y in range(max(fy + 1, deck_y), deck_y + 4):
                    w.set(x, y, z, AIR)
            for x in (tx - 2, tx + 2):
                for y in range(deck_y, deck_y + 2):
                    w.set(x, y, z, PB)
    z_lvl = zs + n_down + 1
    zt_end = tz - 23                     # atrium north wall
    for z in range(z_lvl, zt_end + 1):
        k = z - z_lvl
        tube_ring(w, tx, FLOOR, z, rib=(k % 4 == 0), lamp=(k % 4 == 2))
        if k % 8 == 0:                   # supports down to the sea floor
            yb = seabed(w, tx - 2, z)
            for x in (tx - 2, tx + 2):
                for y in range(min(yb, FLOOR - 1), FLOOR):
                    if w.get(x, y, z) == W:
                        w.set(x, y, z, PD)
    dk.plate(w, tx, FLOOR + 1, z_lvl + 2, "function bear/enter/ocean", kind="light_weighted_pressure_plate", floor=PB)
    # ------------------------------------------------------------------ masses
    ax0, ax1, az0, az1 = tx - 11, tx + 11, tz - 22, tz + 6            # atrium interior
    gx0, gx1, gz0, gz1 = tx - 8, tx + 8, tz, tz + 36                  # gallery interior (flooded)
    sc = (tx, tz + 54)                                                # sanctum centre
    SR = 14
    vx0, vx1, vz0, vz1 = tx - 6, tx + 6, tz + 71, tz + 83             # vault interior
    GF = 24                                                           # flooded floor block level
    # base under the atrium + gallery shell + vault base
    w.fill(ax0 - 2, 18, az0 - 2, ax1 + 2, FLOOR, gz0 - 3, pm)
    w.fill(gx0 - 3, 18, gz0 - 2, gx1 + 3, FLOOR, gz1 + 2, pm)
    w.fill(ax0 - 2, FLOOR, az0 - 2, ax1 + 2, FLOOR, az1 + 2, pm)
    w.fill(vx0 - 2, 18, vz0 - 4, vx1 + 2, FLOOR, vz1 + 2, pm)
    # sanctum shell (cylinder + dome)
    w.cyl(sc[0], sc[1], SR + 2.5, 18, GF + 9, pm)
    for (dx, dz) in kit.disc_cells(SR + 2.5):
        for dy in range(0, SR + 4):
            d = math.sqrt(dx * dx + dz * dz + (dy * 1.05) ** 2)
            if d <= SR + 2.5:
                ang = math.degrees(math.atan2(dz, dx)) % 45
                rib = min(ang, 45 - ang) * math.pi / 180 * math.hypot(dx, dz) < 0.8
                band = dy in (3, 4, 8)
                w.set(sc[0] + dx, GF + 9 + dy, sc[1] + dz, PD if rib else (B("light_blue_stained_glass") if band else pm))
    # carve the flooded interiors (water)
    w.fill(gx0, GF + 1, gz0, gx1, FLOOR - 2, gz1, W)
    w.cyl(sc[0], sc[1], SR, GF + 1, GF + 9, W)
    for (dx, dz) in kit.disc_cells(SR):
        for dy in range(0, SR + 1):
            if math.sqrt(dx * dx + dz * dz + (dy * 1.05) ** 2) <= SR:
                w.set(sc[0] + dx, GF + 9 + dy, sc[1] + dz, W)
    w.fill(tx - 1, GF + 1, gz1 + 1, tx + 1, GF + 4, sc[1] - SR + 1, W)          # gallery -> sanctum door
    w.fill(tx - 1, GF + 1, sc[1] + SR - 1, tx + 1, GF + 3, vz0 + 3, W)           # sanctum -> shaft passage
    w.fill(tx - 1, GF + 1, vz0 + 1, tx + 1, FLOOR, vz0 + 3, W)                   # shaft up to the vault pool
    # ------------------------------------------------------------------ atrium (dry)
    w.fill(ax0, FLOOR + 1, az0, ax1, FLOOR + 5, az1, AIR)
    for x in range(ax0 - 1, ax1 + 2):
        for z in range(az0 - 1, az1 + 2):
            edge = x in (ax0 - 1, ax1 + 1) or z in (az0 - 1, az1 + 1)
            w.set(x, FLOOR, z, (PD if (x + z) % 2 else PB))
            if edge:
                for y in range(FLOOR + 1, FLOOR + 6):
                    rib = (x - ax0) % 4 == 3 or (z - az0) % 4 == 3 or y in (FLOOR + 1, FLOOR + 5)
                    w.set(x, y, z, PB if rib else GLASS)
    # barrel vault of glass over the atrium
    rv = (ax1 - ax0) / 2 + 1.5
    for z in range(az0 - 1, az1 + 2):
        for dx in range(-13, 14):
            for dy in range(0, 14):
                d = math.hypot(dx, dy)
                if rv - 1.2 < d <= rv:
                    rib = (z - az0) % 4 == 3 or z in (az0 - 1, az1 + 1)
                    w.set(tx + dx, FLOOR + 5 + dy, z, PD if rib else GLASS)
                elif d <= rv - 1.2:
                    w.set(tx + dx, FLOOR + 5 + dy, z, AIR if z not in (az0 - 1, az1 + 1) else GLASS)
    for x in range(ax0, ax1 + 1):
        for z in range(az0, az1 + 1):
            for y in range(FLOOR + 1, FLOOR + 20):
                inside = y <= FLOOR + 5 or math.hypot(x - tx, y - FLOOR - 5) <= rv - 1.2
                if inside and w.get(x, y, z) == W:
                    w.set(x, y, z, AIR)
    w.fill(tx - 1, FLOOR + 1, az0 - 2, tx + 1, FLOOR + 3, az0 - 1, AIR)          # tunnel door
    # moon pool down into the gallery
    for x in range(tx - 2, tx + 3):
        for z in range(gz0 + 1, gz0 + 6):
            w.fill(x, FLOOR - 1, z, x, FLOOR, z, W)
    for x in range(tx - 3, tx + 4):
        for z in range(gz0, gz0 + 7):
            if x in (tx - 3, tx + 3) or z in (gz0, gz0 + 6):
                w.set(x, FLOOR, z, SL if (x + z) % 3 == 0 else PD)
    for (px, pz) in ((ax0 + 2, az0 + 3), (ax1 - 2, az0 + 3), (ax0 + 2, az0 + 13), (ax1 - 2, az0 + 13)):
        dk.pillar(w, px, FLOOR + 1, FLOOR + 5, pz, "prismarine_brick", body=PD)
        w.set(px, FLOOR + 3, pz, SL)
    dk.sign(w, tx - 3, FLOOR + 1, gz0 - 1, "N", "§3§l침수된 회랑\n§r이 아래는 물속!\n전달체가 숨을\n쉬게 해 줍니다", wood="warped", standing=True)
    dk.sign(w, tx + 3, FLOOR + 1, gz0 - 1, "N", "§l가라앉은 신전\n§r회랑 끝 성소에\n심해의 수호자", wood="warped", standing=True)
    w.put(ax0, FLOOR + 1, az0 + 8, bl.chest("E"),
          bl.be_chest([bl.item("potion", 1, 20), bl.item("potion", 1, 20), bl.item("cooked_cod", 8),
                       bl.item("potion", 1, 6)]))
    for z in (az0 + 6, az0 + 10):
        w.set(ax1, FLOOR + 1, z, bl.stairs("prismarine_brick", "E"))
    w.set(ax1, FLOOR + 1, az0 + 8, PB)
    w.set(ax1, FLOOR + 2, az0 + 8, SL)
    for (x, z, k) in ((ax0 + 1, az1 - 1, "brain"), (ax1 - 1, az1 - 1, "fire"), (ax0 + 1, az0 + 1, "tube"),
                      (ax1 - 1, az0 + 1, "horn")):
        w.set(x, FLOOR + 1, z, B(k + "_coral_block"))
        w.set(x, FLOOR, z, W)
        w.set(x + (1 if x < tx else -1), FLOOR, z, W) if False else None
    # ------------------------------------------------------------------ flooded gallery
    for z in range(gz0 + 3, gz1 - 1, 6):
        for x in (gx0 + 2, gx1 - 2):
            for y in range(GF + 1, FLOOR - 1):
                w.set(x, y, z, PD if y % 4 else SL)
        for x in (gx0 - 1, gx1 + 1):          # windows
            for y in range(GF + 4, GF + 8):
                w.set(x, y, z + 3, B("light_blue_stained_glass"))
                w.set(x - 1 if x < tx else x + 1, y, z + 3, B("light_blue_stained_glass"))
                w.set(x - 2 if x < tx else x + 2, y, z + 3, B("light_blue_stained_glass"))
    for x in range(gx0, gx1 + 1):
        for z in range(gz0, gz1 + 1):
            w.set(x, GF, z, PD if (x + z) % 4 == 0 else PB)
            if (x - tx) % 5 == 0 and (z - gz0) % 6 == 0:
                w.set(x, FLOOR - 1, z, SL)
    # conduit with a full frame in the middle of the gallery
    cxx, cyy, czz = tx, GF + 6, gz0 + 18
    for a in range(-2, 3):
        for b_ in range(-2, 3):
            if max(abs(a), abs(b_)) == 2:
                w.set(cxx + a, cyy + b_, czz, PB if (a + b_) % 2 else SL)
                w.set(cxx, cyy + a, czz + b_, PB if (a + b_) % 2 else SL)
                w.set(cxx + a, cyy, czz + b_, PB if (a + b_) % 2 else SL)
    w.put(cxx, cyy, czz, B("conduit"), {"id": "Conduit", "Active": bl.Byte(0), "Target": bl.Long(-1)})
    w.water(cxx, cyy, czz, True)
    dk.spawner(w, tx, GF + 1, gz1 - 3, "guardian")
    w.water(tx, GF + 1, gz1 - 3, True)
    dk.spawner(w, tx + 6, GF + 8, gz0 + 4, "guardian")
    w.water(tx + 6, GF + 8, gz0 + 4, True)
    w.set(tx + 6, GF + 7, gz0 + 4, PD)
    dk.spawner(w, tx - 6, GF + 1, gz0 + 8, "drowned")
    w.water(tx - 6, GF + 1, gz0 + 8, True)
    for (x, z, f) in ((gx0, gz0 + 15, "E"), (gx1, gz0 + 27, "W")):
        dk.chest(w, x, GF + 1, z, f, 3, rng)
        w.water(x, GF + 1, z, True)
    for _ in range(60):
        x, z = int(rng.integers(gx0, gx1 + 1)), int(rng.integers(gz0, gz1 + 1))
        if w.get(x, GF + 1, z) == W:
            r_ = rng.random()
            if r_ < 0.5:
                w.set(x, GF + 1, z, B("seagrass", sea_grass_type="default"))
            elif r_ < 0.75:
                w.set(x, GF + 1, z, B(CORALS[int(rng.integers(0, 5))] + "_coral"))
            else:
                w.set(x, GF + 1, z, B("sea_pickle", cluster_count=int(rng.integers(0, 4)), dead_bit=False))
            w.water(x, GF + 1, z, True)
    # ------------------------------------------------------------------ sanctum
    for (dx, dz) in kit.disc_cells(SR):
        w.set(sc[0] + dx, GF, sc[1] + dz, PD if (dx * dx + dz * dz) % 7 < 2 else PB)
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        px, pz = sc[0] + int(round(10 * math.cos(a))), sc[1] + int(round(10 * math.sin(a)))
        for y in range(GF + 1, GF + 12):
            w.set(px, y, pz, PD if y % 5 else SL)
    w.fill(sc[0] - 1, GF + 1, sc[1] - 1, sc[0] + 1, GF + 2, sc[1] + 1, PD)
    w.fill(sc[0], GF + 1, sc[1], sc[0], GF + 3, sc[1], B("gold_block"))
    w.set(sc[0], GF + 4, sc[1], SL)
    for (dx, dz) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        w.set(sc[0] + dx, GF + 1, sc[1] + dz, B("wet_sponge") if False else B("sponge", sponge_type="wet"))
    # boss trigger: repeating command block hidden under the floor
    w.put(sc[0], GF - 2, sc[1], bl.cmd("repeat", "U"),
          bl.be_cmd("execute if entity @a[x=%d,y=%d,z=%d,dx=%d,dy=%d,dz=%d] run function bear/boss/ocean" % (
              sc[0] - SR, GF + 1, sc[1] - SR, 2 * SR, 24, 2 * SR), auto=True, tick_delay=20, repeat=True))
    # ------------------------------------------------------------------ vault (dry)
    w.fill(vx0 - 1, FLOOR, vz0 - 1, vx1 + 1, FLOOR + 7, vz1 + 1, pm)
    w.fill(vx0, FLOOR + 1, vz0, vx1, FLOOR + 5, vz1, AIR)
    for x in range(vx0, vx1 + 1):
        for z in range(vz0, vz1 + 1):
            w.set(x, FLOOR, z, PD if (x + z) % 2 else B("gold_block") if (x * z) % 11 == 0 else PB)
            w.set(x, FLOOR + 6, z, SL if (x - tx) % 4 == 0 and (z - vz0) % 4 == 2 else PB)
    for x in range(tx - 1, tx + 2):
        for z in range(vz0 + 1, vz0 + 4):
            w.set(x, FLOOR, z, W)
    for x in range(tx - 2, tx + 3):
        for z in range(vz0, vz0 + 5):
            if x in (tx - 2, tx + 2) or z in (vz0, vz0 + 4):
                w.set(x, FLOOR, z, PD)
    dk.reward_altar(w, tx, FLOOR + 1, vz1, "N", "ocean", "바다 던전 보상")
    dk.chest(w, vx0, FLOOR + 1, vz1 - 2, "E", 3, rng, extra=[bl.item("sponge", 4), bl.item("prismarine_crystals", 12)])
    dk.chest(w, vx1, FLOOR + 1, vz1 - 2, "W", 3, rng, extra=[bl.item("heart_of_the_sea", 1), bl.item("diamond", 3)])
    dk.chest(w, vx0, FLOOR + 1, vz1 - 6, "E", 2, rng, extra=[bl.item("nautilus_shell", 4)])
    dk.exit_pad(w, vx1 - 2, FLOOR + 1, vz1 - 6, None)
    dk.sign(w, vx1 - 2, FLOOR + 2, vz1 - 4, "N", "§b§l마을로 귀환") if False else None
    for (x, z) in ((vx0, vz0), (vx1, vz0)):
        w.set(x, FLOOR + 1, z, B("gold_block"))
        w.set(x, FLOOR + 2, z, SL)
    # ------------------------------------------------------------------ exterior dressing
    for z in range(gz0 + 3, gz1, 6):            # buttress fins along the gallery
        for sx in (-1, 1):
            for k in range(0, 6):
                x = tx + sx * (11 + k)
                yb = seabed(w, x, z)
                top = FLOOR - 1 - k * 2
                for y in range(min(yb, top), top + 1):
                    if w.get(x, y, z) in (W, 0):
                        w.set(x, y, z, PD if k % 2 else PB)
                if w.get(x, top + 1, z) == W:
                    w.set(x, top + 1, z, bl.stairs("dark_prismarine", "E" if sx < 0 else "W"))
    for z in range(gz0 - 1, gz1 + 2, 4):
        w.set(tx, FLOOR + 1, z, SL) if w.get(tx, FLOOR + 1, z) == W else None
    for (px, pz) in ((tx - 20, tz - 26), (tx + 20, tz - 26), (tx - 22, tz + 54), (tx + 22, tz + 54),
                     (tx - 16, tz + 90), (tx + 16, tz + 90)):
        yb = seabed(w, px, pz)
        for y in range(yb + 1, yb + 14):
            w.set(px, y, pz, PD if (y - yb) % 4 else PB)
            for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if y - yb < 3:
                    w.set(px + dx, y, pz + dz, PB)
        w.set(px, yb + 14, pz, SL)
        w.set(px, yb + 15, pz, bl.slab("prismarine_brick"))
    # coral reef + kelp around the temple and along the tunnel
    for _ in range(46):
        a = rng.random() * 2 * math.pi
        rr = 22 + rng.random() * 62
        coral_patch(w, tx + int(rr * math.cos(a)), tz + 30 + int(rr * 0.9 * math.sin(a)), 3 + rng.random() * 4, rng)
    for z in range(z_lvl - 10, zt_end, 9):
        for sx in (-1, 1):
            coral_patch(w, tx + sx * int(rng.integers(6, 14)), z + int(rng.integers(-3, 4)), 3.5, rng)
    for _ in range(700):
        x, z = tx + int(rng.integers(-90, 91)), tz + int(rng.integers(-110, 95))
        if not (w.x0 <= x < w.x1 and w.z0 <= z < w.z1):
            continue
        yb = seabed(w, x, z)
        if yb < 14 or yb > SEA - 6 or w.get(x, yb + 1, z) != W:
            continue
        if w.get(x, yb, z) in (PB, PD, PR, GLASS, SL):
            continue
        n = int(rng.integers(2, max(3, min(16, SEA - yb - 3))))
        for i in range(1, n + 1):
            if w.get(x, yb + i, z) != W:
                break
            w.set(x, yb + i, z, B("kelp", kelp_age=25 if i == n else int(rng.integers(0, 20))))
            w.water(x, yb + i, z, True)
    kit.auto_waterlog(w, tx - 95, 10, z_end - 20, tx + 95, SEA, min(w.z1 - 1, tz + 110))
    # registry
    dk.warp("ocean", 0, tx + 0.5, deck_y + 1, z_end - 12.5, (tx, deck_y + 1, z_end))
    dk.zone(0, tx - 40, 8, z_end - 14, tx + 40, SEA - 1, tz + 100)
    dk.zone(0, tx - 30, SEA - 6, HARBOR[1] - 26, tx + 30, 120, z_end + 4)
    bx, by, bz = sc[0], GF + 8, sc[1] + 6
    dk.boss("ocean", {
        "pos": (sc[0], GF + 3, sc[1]),
        "spawn": [
            'summon elder_guardian "§3심해의 수호자" %d %d %d' % (bx, by, bz),
            "tag @e[type=elder_guardian,x=%d,y=%d,z=%d,r=4,c=1] add boss_ocean" % (bx, by, bz),
            "effect @e[tag=boss_ocean] resistance 99999 0 true",
            "summon guardian %d %d %d" % (bx - 6, by - 3, bz - 8),
            "summon guardian %d %d %d" % (bx + 6, by - 3, bz - 8),
            "summon guardian %d %d %d" % (bx, by + 3, bz - 12),
            "summon drowned %d %d %d" % (bx - 4, GF + 1, bz - 4),
            "summon drowned %d %d %d" % (bx + 4, GF + 1, bz - 4),
        ],
        "title": "§3심해의 수호자", "sub": "§7가라앉은 신전의 주인",
    })
