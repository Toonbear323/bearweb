"""Preview helpers: perspective shots aimed at a target point, block-light aware."""
import math

import numpy as np

import lighting
import render


def look(cam, target):
    dx, dy, dz = target[0] - cam[0], target[1] - cam[1], target[2] - cam[2]
    yaw = math.degrees(math.atan2(-dx, dz)) % 360
    pitch = math.degrees(math.atan2(-dy, math.hypot(dx, dz)))
    return yaw, pitch


def free_cam(area, cam, up=40):
    """Move the camera up until it and the block above are air (so it never sits inside rock)."""
    x, y, z = int(math.floor(cam[0])), int(math.floor(cam[1])), int(math.floor(cam[2]))
    for k in range(up):
        if area.get(x, y + k, z) == 0 and area.get(x, y + k + 1, z) == 0:
            return (cam[0], y + k + 0.6, cam[2])
    return cam


def shot(area, path, cam, target, W=800, H=450, fov=70, fog=(160, 180, 210), fog_dist=320, light=True, reach=90, steps=900):
    cam = free_cam(area, cam)
    yaw, pitch = look(cam, target)
    L = None
    if light:
        a = area
        cx, cy, cz = cam
        tx, ty, tz = target
        x1, x2 = int(min(cx, tx)) - reach, int(max(cx, tx)) + reach
        z1, z2 = int(min(cz, tz)) - reach, int(max(cz, tz)) + reach
        sl = (slice(max(0, x1 - a.x0), max(0, min(a.sx, x2 - a.x0))), slice(0, a.sy), slice(max(0, z1 - a.z0), max(0, min(a.sz, z2 - a.z0))))
        L = np.zeros(a.blk.shape, np.int8)
        L[sl] = lighting.block_light(a.blk[sl])
    render.persp(area, path, cam, yaw, pitch, W=W, H=H, fov=fov, block_light=L, fog_col=fog, fog_dist=fog_dist, max_steps=steps)
    return yaw, pitch
