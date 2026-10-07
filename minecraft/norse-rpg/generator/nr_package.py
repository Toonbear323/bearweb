"""World packaging: LevelDB written region by region, level.dat, both packs attached, .mcworld + .mcpack files."""
import json
import os
import shutil
import tempfile

from mcw import write_level_dat, zip_dir
from worldkit import level_changes, TEMPLATE


class DB:
    """Open LevelDB; regions are encoded and written one at a time so only one Area lives in memory."""

    def __init__(self, path):
        from leveldb import LevelDB
        os.makedirs(path, exist_ok=True)
        self.db = LevelDB(path, create_if_missing=True)
        self.keys = 0

    def put_area(self, area):
        for cx, cz in area.chunks():
            batch = area.encode_chunk(cx, cz)
            self.db.putBatch(batch)
            self.keys += len(batch)

    def close(self):
        self.db.close(compact=True)


def attach_packs(wdir, packs):
    bpd = os.path.join(wdir, "behavior_packs", os.path.basename(packs["bp"]))
    rpd = os.path.join(wdir, "resource_packs", os.path.basename(packs["rp"]))
    for src, dst in ((packs["bp"], bpd), (packs["rp"], rpd)):
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)
    json.dump([{"pack_id": packs["bp_uuid"], "version": packs["version"]}],
              open(os.path.join(wdir, "world_behavior_packs.json"), "w"), indent=2)
    json.dump([{"pack_id": packs["rp_uuid"], "version": packs["version"]}],
              open(os.path.join(wdir, "world_resource_packs.json"), "w"), indent=2)


def finish(wdir, out_file, name, spawn, packs=None, icon=None, overrides=None, db=None):
    if db is not None:
        db.close()
    changes = level_changes(name, spawn)
    changes.update(overrides or {})
    write_level_dat(os.path.join(wdir, "level.dat"), TEMPLATE, changes)
    open(os.path.join(wdir, "levelname.txt"), "w", encoding="utf8").write(name)
    if packs:
        attach_packs(wdir, packs)
    if icon is not None:
        icon.convert("RGB").save(os.path.join(wdir, "world_icon.jpeg"), quality=92)
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
    if os.path.exists(out_file):
        os.remove(out_file)
    zip_dir(wdir, out_file)
    print("wrote %s (%.2f MB, %d leveldb keys)" % (out_file, os.path.getsize(out_file) / 1e6, db.keys if db else -1))
    return wdir


def new_world_dir(keep=None):
    work = keep or tempfile.mkdtemp(prefix="nrpg_")
    wdir = os.path.join(work, "world")
    shutil.rmtree(wdir, ignore_errors=True)
    os.makedirs(wdir)
    return wdir
