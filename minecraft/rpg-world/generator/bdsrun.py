"""Run a world folder on Bedrock Dedicated Server, type console commands, return the console log.

The world is copied to <BDS>/worlds/test_<name> (the copy keeps the chunks the server saved, so you
can diff them afterwards with bdsdiff.py). Numbers in the command list are pauses in seconds.

    from bdsrun import run
    log = run("out/world", [20, "scriptevent at:diag", "tickingarea add 0 0 0 111 0 111 a true", 30,
                            "testforblock 5 65 5 lantern"], bds_dir="bds")

CLI:  python bdsrun.py <world_dir> 20 "scriptevent at:diag" 5     (BDS dir from $BDS_DIR or ./bds)

Useful console commands for checking a world without a client:
  scriptevent <ns:id> <msg>        -> your script prints with console.warn (content log goes to console)
  tickingarea add x1 0 z1 x2 0 z2 name true   -> load/tick chunks (max 10 areas, ~100 chunks each)
  testforblock x y z <block> ["state"=value]   -> "Successfully found the block" / "did not match"
  scoreboard players list *        -> check that your setup function ran (fake-player scores)
  testfor @e[type=npc]             -> "Found <name>" when your NPCs were summoned
  function <name>, execute ... run ... (say/tellraw output does not reach the console)
The server has no players, so anything that needs a player (right-click, sneaking, pressing
buttons, NPC dialogue clicks) cannot be tested here - say so when you report results.
"""
import os
import shutil
import subprocess
import sys
import threading
import time

DEFAULT_BDS = os.environ.get("BDS_DIR", os.path.join(os.getcwd(), "bds"))
NOISE = ("TELEMETRY", "telemetry", "llow list", "allowlist")


def run(world_dir, commands, settle=12, gap=1.5, extra_props=None, bds_dir=None):
    bds = os.path.abspath(bds_dir or DEFAULT_BDS)
    name = "test_" + os.path.basename(os.path.abspath(world_dir).rstrip("/"))
    dst = os.path.join(bds, "worlds", name)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(world_dir, dst)
    props_path = os.path.join(bds, "server.properties")
    props = open(props_path).read().splitlines()
    want = {"level-name": name, "allow-cheats": "true", "content-log-console-output-enabled": "true",
            "content-log-file-enabled": "false"}
    want.update(extra_props or {})
    out, seen = [], set()
    for line in props:
        k = line.split("=")[0]
        if k in want:
            out.append(k + "=" + want[k])
            seen.add(k)
        else:
            out.append(line)
    out += [k + "=" + v for k, v in want.items() if k not in seen]
    open(props_path, "w").write("\n".join(out) + "\n")
    p = subprocess.Popen(["./bedrock_server"], cwd=bds, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, env=dict(os.environ, LD_LIBRARY_PATH="."), text=True,
                         encoding="utf-8", errors="replace")
    lines = []

    def reader():
        for l in p.stdout:
            lines.append(l.rstrip())

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    time.sleep(settle)
    for c in commands:
        if isinstance(c, (int, float)):
            time.sleep(c)
            continue
        if p.poll() is not None:
            break
        lines.append(">>> " + c)
        p.stdin.write(c + "\n")
        p.stdin.flush()
        time.sleep(gap)
    if p.poll() is None:
        p.stdin.write("stop\n")
        p.stdin.flush()
    try:
        p.wait(60)
    except Exception:
        p.kill()
    t.join(2)
    return [l for l in lines if not any(n in l for n in NOISE)]


def saved_world(world_dir, bds_dir=None):
    """Path of the server's copy of a world (after run()), for bdsdiff.compare()."""
    bds = os.path.abspath(bds_dir or DEFAULT_BDS)
    return os.path.join(bds, "worlds", "test_" + os.path.basename(os.path.abspath(world_dir).rstrip("/")))


if __name__ == "__main__":
    args = [float(a) if a.replace(".", "").isdigit() else a for a in sys.argv[2:]]
    for l in run(sys.argv[1], args):
        print(l)
