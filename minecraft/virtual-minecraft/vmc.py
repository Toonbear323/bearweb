#!/usr/bin/env python3
"""가상 마인크래프트 테스트 도구 (Virtual Minecraft tester)

화면 없는 공식 Bedrock 전용 서버(BDS)에 월드를 올려서
  - 월드가 제대로 열리는지, 행동/리소스 팩과 스크립트에 오류가 없는지
  - 명령어(시나리오 파일)를 차례로 실행하고 결과가 맞는지
  - 일정 시간 돌린 뒤 블록·엔티티가 어떻게 바뀌었는지 (물이 새는지, 블록이 떨어지는지 등)
를 확인합니다. 원본 월드 파일은 건드리지 않고, 서버 폴더에 복사본을 만들어 씁니다.

  python vmc.py                      메뉴
  python vmc.py setup                서버(BDS) 내려받기/업데이트
  python vmc.py test 월드.mcworld     [--script 시나리오.txt] [--seconds 60] [--area auto]
  python vmc.py console 월드.mcworld  서버를 켜고 직접 명령 입력 (내 게임으로 접속도 가능)
  python vmc.py info 월드.mcworld
  python vmc.py diff 이전월드 이후월드

Python 3.8 이상, 표준 라이브러리만 사용합니다.
"""
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                 # the portable Windows Python does not add the script folder
    sys.path.insert(0, HERE)

import argparse
import collections
import datetime
import hashlib
import json
import platform
import re
import shutil
import socket
import struct
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import zipfile
import zlib

import bedrock_db as bdb

SERVER_DIR = os.path.join(HERE, "server")
RESULTS_DIR = os.path.join(HERE, "results")
WORK_DIR = os.path.join(HERE, "work")
IS_WIN = os.name == "nt"
EXE = "bedrock_server.exe" if IS_WIN else "bedrock_server"
LINKS_API = "https://net-secondary.web.minecraft-services.net/api/v1.0/download/links"
UA = "Mozilla/5.0 (vmc world tester)"
TEST_WORLD, CONSOLE_WORLD = "vmc_test", "vmc_console"
NOISE = ("TELEMETRY", "Telemetry", "telemetry", "ALLOW LIST", "llow list", "allowlist", "handheld/src-server",
         "=======", "NO LOG FILE!")
LOG_RE = re.compile(r"^\[(\d{4}-\d\d-\d\d [\d:]+) (INFO|WARN|ERROR|VERBOSE|DEBUG)\] ?(.*)$")
COLOR_RE = re.compile("§.")
GAMEMODES = {0: "survival", 1: "creative", 2: "adventure"}
DIFFICULTIES = {0: "peaceful", 1: "easy", 2: "normal", 3: "hard"}

try:
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except Exception:
    pass


def clean(s):
    return COLOR_RE.sub("", s)


def ask(prompt, default=""):
    try:
        v = input(prompt).strip()
    except EOFError:
        return default
    return v or default


def clean_path(p):
    p = p.strip().strip('"').strip("'").strip()
    if p.startswith("file://"):
        p = urllib.parse.unquote(urllib.parse.urlparse(p).path)
    if not IS_WIN:
        p = p.replace("\\ ", " ")
    return os.path.expanduser(p)


def safe_name(s):
    s = re.sub(r"[^\w\-]+", "_", clean(s), flags=re.UNICODE).strip("_")
    return s[:40] or "world"


# ============================================================================ server install


def server_exe():
    return os.path.join(SERVER_DIR, EXE)


def server_version():
    try:
        return open(os.path.join(SERVER_DIR, "version.txt")).read().strip()
    except OSError:
        return None


def latest_link(preview=False):
    system = platform.system()
    if system == "Windows":
        kind = "serverBedrockWindows"
    elif system == "Linux":
        kind = "serverBedrockLinux"
    else:
        raise SystemExit("Bedrock 전용 서버는 Windows와 Linux용만 있습니다 (현재: %s)." % system)
    if preview:
        kind = kind.replace("serverBedrock", "serverBedrockPreview")
    req = urllib.request.Request(LINKS_API, headers={"User-Agent": UA})
    data = json.load(urllib.request.urlopen(req, timeout=60))
    for link in data["result"]["links"]:
        if link["downloadType"] == kind:
            return link["downloadUrl"]
    raise SystemExit("공식 사이트에서 %s 링크를 찾지 못했습니다." % kind)


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    part = dest + ".part"
    with urllib.request.urlopen(req, timeout=120) as r, open(part, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        got, last = 0, -1
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
            pct = got * 100 // total if total else 0
            if pct != last:
                last = pct
                sys.stdout.write("\r  내려받는 중 %3d%%  (%.0f / %.0f MB)" % (pct, got / 1e6, total / 1e6))
                sys.stdout.flush()
    print()
    os.replace(part, dest)


def setup(preview=False, yes=False, url=None, force=False):
    if platform.machine().lower() not in ("amd64", "x86_64", "x64", ""):
        print("주의: Bedrock 전용 서버는 x86-64(일반 PC) CPU용입니다. 이 PC(%s)에서는 실행되지 않을 수 있습니다."
              % platform.machine())
    print("Minecraft Bedrock 전용 서버(BDS)를 공식 사이트(minecraft.net)에서 내려받습니다.")
    print("내려받으면 Minecraft 최종 사용자 사용권 계약(https://www.minecraft.net/eula)과")
    print("개인정보 처리방침(https://go.microsoft.com/fwlink/?LinkId=521839)에 동의하는 것입니다.")
    if not yes and ask("동의하면 y 를 입력하세요 (y/n): ").lower() not in ("y", "yes", "ㅛ"):
        print("취소했습니다.")
        return False
    url = url or latest_link(preview)
    ver = os.path.splitext(os.path.basename(urllib.parse.urlparse(url).path))[0].replace("bedrock-server-", "")
    if not force and server_version() == ver and os.path.exists(server_exe()):
        print("이미 최신 버전(%s)이 설치되어 있습니다." % ver)
        return ensure_vc_runtime()
    os.makedirs(SERVER_DIR, exist_ok=True)
    zpath = os.path.join(HERE, "server_download.zip")
    print("버전 %s" % ver)
    download(url, zpath)
    print("  압축 푸는 중...")
    keep = {}
    for fn in ("allowlist.json", "permissions.json"):          # keep the user's lists on update
        p = os.path.join(SERVER_DIR, fn)
        if os.path.exists(p):
            keep[fn] = open(p, "rb").read()
    with zipfile.ZipFile(zpath) as z:
        z.extractall(SERVER_DIR)
    for fn, data in keep.items():
        open(os.path.join(SERVER_DIR, fn), "wb").write(data)
    os.remove(zpath)
    if not IS_WIN:
        os.chmod(server_exe(), 0o755)
    open(os.path.join(SERVER_DIR, "version.txt"), "w").write(ver + "\n")
    print("설치 완료: %s (버전 %s)" % (SERVER_DIR, ver))
    return ensure_vc_runtime()


def ensure_server():
    if os.path.exists(server_exe()):
        return ensure_vc_runtime()
    print("서버(BDS)가 아직 설치되지 않았습니다.")
    return setup()


# ============================================================================ Visual C++ runtime (Windows)
# bedrock_server.exe needs msvcp140.dll, vcruntime140.dll and vcruntime140_1.dll. Many PCs lack them and
# installing the redistributable needs administrator rights, so the DLLs are taken out of Microsoft's
# official vc_redist.x64.exe (signature checked, never run) and put next to bedrock_server.exe.

VC_URL = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
VC_NEEDED = ("msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll")
VC_KNOWN_SHA256 = {"cc0ff0eb1dc3f5188ae6300faef32bf5beeba4bdd6e8e445a9184072096b713b": "14.44.35211"}


def _cab_parse(data):
    """Header of a Microsoft cabinet -> (folders [(offset, blocks, compression)], files [(name, size, offset,
    folder)], bytes reserved per data block)."""
    if data[:4] != b"MSCF":
        raise ValueError("not a cabinet")
    coff, = struct.unpack_from("<I", data, 16)
    nfold, nfile, flags = struct.unpack_from("<HHH", data, 26)
    o, cb_fold, cb_data = 36, 0, 0
    if flags & 4:
        cb_hdr, cb_fold, cb_data = struct.unpack_from("<HBB", data, 36)
        o = 40 + cb_hdr
    for bit in (1, 2):                       # previous / next cabinet names
        if flags & bit:
            for _ in range(2):
                o = data.index(b"\0", o) + 1
    folders = []
    for _ in range(nfold):
        start, ndata, ctype = struct.unpack_from("<IHH", data, o)
        folders.append((start, ndata, ctype & 0xF))
        o += 8 + cb_fold
    files, o = [], coff
    for _ in range(nfile):
        size, off, ifold, _date, _time, attr = struct.unpack_from("<IIHHHH", data, o)
        end = data.index(b"\0", o + 16)
        files.append((data[o + 16:end].decode("utf-8" if attr & 0x80 else "latin-1"), size, off, ifold))
        o = end + 1
    return folders, files, cb_data


def cab_extract(data, want=lambda name: True):
    """Files of a stored or MSZIP cabinet -> {name: bytes}."""
    folders, files, cb_data = _cab_parse(data)
    streams, out = {}, {}
    for name, size, off, ifold in files:
        if not want(name):
            continue
        if ifold not in streams:
            start, ndata, ctype = folders[ifold]
            buf, prev, p = bytearray(), b"", start
            for _ in range(ndata):
                _csum, cbd, _cbu = struct.unpack_from("<IHH", data, p)
                p += 8 + cb_data
                blk = data[p:p + cbd]
                p += cbd
                if ctype == 0:
                    chunk = blk
                elif ctype == 1 and blk[:2] == b"CK":          # MSZIP: deflate, previous block as history
                    d = zlib.decompressobj(-15, zdict=prev) if prev else zlib.decompressobj(-15)
                    chunk = d.decompress(blk[2:]) + d.flush()
                else:
                    raise ValueError("unsupported cabinet compression %d" % ctype)
                buf += chunk
                prev = bytes(chunk[-32768:])
            streams[ifold] = bytes(buf)
        out[name] = streams[ifold][off:off + size]
    return out


def runtime_from_vc_redist(exe):
    """{dll name: bytes} of the x64 runtime packed inside vc_redist.x64.exe (a WiX bundle of cabinets)."""
    for m in re.finditer(b"MSCF\0\0\0\0", exe):
        size, = struct.unpack_from("<I", exe, m.start() + 8)
        if size < 64 or m.start() + size > len(exe):
            continue
        try:
            outer = cab_extract(exe[m.start():m.start() + size])
        except (ValueError, struct.error, zlib.error):
            continue
        for blob in outer.values():
            if not blob.startswith(b"MSCF"):
                continue
            try:
                names = [f[0].lower() for f in _cab_parse(blob)[1]]
            except (ValueError, struct.error):
                continue
            if "vcruntime140_1.dll_amd64" in names:
                inner = cab_extract(blob, lambda n: n.lower().endswith(".dll_amd64") and n.lower().startswith(
                    ("msvcp140", "vcruntime140", "concrt140")))
                return {n[:-len("_amd64")].lower(): b for n, b in inner.items()}
    return {}


def microsoft_signed(path):
    """(ok, detail): Authenticode signature of a file is valid and belongs to Microsoft (checked by Windows)."""
    ps = ("$s = Get-AuthenticodeSignature -LiteralPath $env:VMC_FILE; "
          "if ($s.Status -eq 'Valid' -and $s.SignerCertificate.Subject -like '*O=Microsoft Corporation*') { exit 0 }; "
          "Write-Output ([string]$s.Status + ' / ' + [string]$s.SignerCertificate.Subject); exit 1")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                           env=dict(os.environ, VMC_FILE=path), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=180)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, "PowerShell 을 실행하지 못함 (%s)" % e
    return r.returncode == 0, r.stdout.decode("utf-8", "replace").strip()


def vc_runtime_ready():
    return not IS_WIN or all(os.path.exists(os.path.join(SERVER_DIR, d)) for d in VC_NEEDED)


def vc_manual_hint():
    print("  직접 해결하려면 Microsoft 공식 'Visual C++ 재배포 패키지(x64)'를 설치하세요 (관리자 권한 필요):")
    print("  " + VC_URL)


def ensure_vc_runtime():
    if vc_runtime_ready():
        return True
    print()
    print("서버 프로그램에 필요한 Microsoft Visual C++ 런타임 파일(msvcp140.dll, vcruntime140.dll, "
          "vcruntime140_1.dll)을 준비합니다.")
    print("Microsoft 공식 재배포 패키지(약 25MB)를 받아서, 설치는 하지 않고 필요한 파일만 서버 폴더에 넣습니다.")
    print("(관리자 권한이 필요 없고 PC 설정도 바꾸지 않습니다.)")
    exe = os.path.join(HERE, "vc_redist_download.exe")
    try:
        download(VC_URL, exe)
        data = open(exe, "rb").read()
        if hashlib.sha256(data).hexdigest() not in VC_KNOWN_SHA256:
            ok, why = microsoft_signed(exe)
            if not ok:
                print("[중단] 받은 파일이 Microsoft 서명 파일인지 확인하지 못했습니다: %s" % why)
                vc_manual_hint()
                return False
        dlls = runtime_from_vc_redist(data)
        missing = [d for d in VC_NEEDED if d not in dlls]
        if missing:
            print("[중단] 재배포 패키지 안에서 %s 를 찾지 못했습니다." % ", ".join(missing))
            vc_manual_hint()
            return False
        for name, blob in sorted(dlls.items()):
            open(os.path.join(SERVER_DIR, name), "wb").write(blob)
        print("  런타임 파일 %d개를 서버 폴더에 넣었습니다." % len(dlls))
        return True
    except Exception as e:
        print("[중단] 런타임 파일을 준비하지 못했습니다: %r" % e)
        vc_manual_hint()
        return False
    finally:
        for p in (exe, exe + ".part"):
            if os.path.exists(p):
                os.remove(p)


# ============================================================================ worlds


def find_world_root(folder):
    for root, _dirs, files in os.walk(folder):
        if "level.dat" in files and os.path.isdir(os.path.join(root, "db")):
            return root
    return None


def open_world_source(path):
    """A .mcworld/.zip/.mctemplate file, a world folder or its level.dat -> world folder path."""
    path = clean_path(path)
    if not os.path.exists(path):
        raise SystemExit("파일이나 폴더를 찾을 수 없습니다: %s" % path)
    if os.path.isfile(path) and os.path.basename(path) == "level.dat":
        path = os.path.dirname(path)
    if os.path.isdir(path):
        root = find_world_root(path)
        if not root:
            raise SystemExit("월드 폴더가 아닙니다 (level.dat 과 db 폴더가 있어야 합니다): %s" % path)
        return root
    if not zipfile.is_zipfile(path):
        raise SystemExit(".mcworld 파일이나 월드 폴더를 넣어 주세요: %s" % path)
    dst = os.path.join(WORK_DIR, safe_name(os.path.splitext(os.path.basename(path))[0]) + "_src")
    shutil.rmtree(dst, ignore_errors=True)
    with zipfile.ZipFile(path) as z:
        z.extractall(dst)
    root = find_world_root(dst)
    if not root:
        raise SystemExit("압축 파일 안에 월드(level.dat, db)가 없습니다: %s" % path)
    return root


def copy_world(src, name):
    dst = os.path.join(SERVER_DIR, "worlds", name)
    shutil.rmtree(dst, ignore_errors=True)
    try:
        shutil.copytree(src, dst)
    except (OSError, shutil.Error) as e:
        raise SystemExit("월드를 서버 폴더로 복사하지 못했습니다 (%s).\n이전에 켠 서버가 아직 돌고 있을 수 있습니다. "
                         "작업 관리자에서 bedrock_server 를 끄고 다시 해 보세요." % e)
    return dst


def pack_names(world_dir):
    """uuid -> (pack name, 'behavior'|'resource') for packs stored inside the world folder."""
    out = {}
    for sub, kind in (("behavior_packs", "behavior"), ("resource_packs", "resource")):
        base = os.path.join(world_dir, sub)
        if not os.path.isdir(base):
            continue
        for d in os.listdir(base):
            m = _read_json(os.path.join(base, d, "manifest.json"))
            if isinstance(m, dict) and isinstance(m.get("header"), dict):
                out[str(m["header"].get("uuid", "")).lower()] = (clean(str(m["header"].get("name", d))), kind)
    return out


def _read_json(path):
    try:
        text = open(path, encoding="utf-8-sig").read()
    except OSError:
        return None
    try:
        return json.loads(text)
    except ValueError:
        text = re.sub(r"(?m)^\s*//.*$", "", text)               # Bedrock JSON may carry comments
        try:
            return json.loads(text)
        except ValueError:
            return None


def world_packs(world_dir):
    """[(uuid, kind)] the world asks the server to load."""
    out = []
    for fn, kind in (("world_behavior_packs.json", "behavior"), ("world_resource_packs.json", "resource")):
        data = _read_json(os.path.join(world_dir, fn))
        for e in data if isinstance(data, list) else []:
            if isinstance(e, dict) and e.get("pack_id"):
                out.append((str(e["pack_id"]).lower(), kind))
    return out


# ============================================================================ the server process


class Server:
    def __init__(self, world_name, props, echo=False):
        self.world_name = world_name
        self.props = props
        self.echo = echo
        self.lines = []                  # (time, text)
        self.cv = threading.Condition()
        self.proc = None
        self.started_at = None

    def write_props(self):
        path = os.path.join(SERVER_DIR, "server.properties")
        try:
            lines = open(path, encoding="utf-8").read().splitlines()
        except OSError:
            lines = []
        want = dict(self.props, **{"level-name": self.world_name})
        out, seen = [], set()
        for line in lines:
            k = line.split("=", 1)[0].strip()
            if k in want and not line.lstrip().startswith("#"):
                out.append("%s=%s" % (k, want[k]))
                seen.add(k)
            else:
                out.append(line)
        out += ["%s=%s" % (k, v) for k, v in want.items() if k not in seen]
        open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")

    def start(self, timeout=180):
        self.write_props()
        kw = {}
        env = dict(os.environ)
        if IS_WIN:
            kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kw["start_new_session"] = True
            env["LD_LIBRARY_PATH"] = "."
        self.proc = subprocess.Popen([server_exe()], cwd=SERVER_DIR, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, env=env, **kw)
        threading.Thread(target=self._reader, daemon=True).start()
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.proc.poll() is not None:
                return False
            if any("Server started." in l for _t, l in self.lines):
                self.started_at = time.time()
                return True
            time.sleep(0.2)
        return self.proc.poll() is None

    def _reader(self):
        for raw in self.proc.stdout:
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            if any(n in line for n in NOISE):
                continue
            with self.cv:
                self.lines.append((time.time(), line))
                self.cv.notify_all()
            if self.echo:
                print(clean(line))
        with self.cv:
            self.cv.notify_all()

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def send(self, cmd):
        if not self.alive():
            return False
        try:
            self.proc.stdin.write((cmd + "\n").encode("utf-8"))
            self.proc.stdin.flush()
            return True
        except OSError:
            return False

    def command(self, cmd, quiet=0.7, max_wait=6.0):
        """Send one console command and collect the lines that answer it."""
        with self.cv:
            self.lines.append((time.time(), ">>> " + cmd))
            start = len(self.lines)
        if not self.send(cmd):
            return []
        t0 = time.time()
        last_n, last_t = start, t0
        while True:
            with self.cv:
                self.cv.wait(0.1)
                n = len(self.lines)
            now = time.time()
            if n != last_n:
                last_n, last_t = n, now
            if n > start and now - last_t >= quiet:
                break
            if now - t0 >= max_wait or not self.alive():
                break
        return [l for _t, l in self.lines[start:]]

    def wait(self, seconds):
        end = time.time() + seconds
        while time.time() < end and self.alive():
            time.sleep(min(0.5, max(0.0, end - time.time())))

    def stop(self, timeout=120):
        if self.alive():
            self.lines.append((time.time(), ">>> stop"))
            self.send("stop")
            try:
                self.proc.wait(timeout)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(10)
        return self.proc.returncode if self.proc else None

    def log_text(self):
        return "\n".join(l for _t, l in self.lines)


def judge(lines):
    """'ok' / 'fail' / 'none' for the answer of one console command.
    Content-log lines ([Scripting], [Commands], ...) can land in any answer window, so they do not count."""
    seen = False
    for l in lines:
        m = LOG_RE.match(l)
        if not m or m.group(3).startswith("["):
            continue
        seen = True
        if m.group(2) == "ERROR":
            return "fail"
    return "ok" if seen else "none"


def server_props(level, port, lan, allow_list=True):
    return {
        "allow-cheats": "true",
        "content-log-console-output-enabled": "true",
        "content-log-file-enabled": "false",
        "gamemode": GAMEMODES.get(level.get("GameType", 0), "survival"),
        "difficulty": DIFFICULTIES.get(level.get("Difficulty", 2), "normal"),
        "server-port": str(port),
        "server-portv6": str(port + 1),
        "enable-lan-visibility": "true" if lan else "false",
        "allow-list": "true" if allow_list else "false",
    }


def start_failure_hint(srv):
    code = srv.proc.returncode if srv.proc else None
    if code is not None and code < 0:
        code &= 0xFFFFFFFF
    if code == 0xC0000135:
        return ("서버 실행에 필요한 DLL 파일이 없습니다 (Visual C++ 런타임). server 폴더의 msvcp140.dll / "
                "vcruntime140.dll / vcruntime140_1.dll 을 지우고 다시 실행하면 새로 받습니다.")
    if code in (0xC0000139, 0xC000007B):
        return "DLL 파일이 맞지 않습니다. server 폴더의 msvcp140.dll / vcruntime140*.dll 을 지우고 다시 실행하세요."
    text = srv.log_text()
    if "port occupied" in text.lower() or "address already in use" in text.lower():
        return "포트가 이미 사용 중입니다. 다른 서버를 끄거나 --port 로 다른 번호를 지정하세요."
    if "eula" in text.lower():
        return "EULA 관련 오류입니다. python vmc.py setup 을 다시 실행하세요."
    return "서버 로그 끝부분을 확인하세요."


# ============================================================================ scenario files

WAIT_WORDS = ("대기", "wait")
CHECK_WORDS = ("확인", "check")
CHECKFAIL_WORDS = ("실패확인", "checkfail")


def read_text(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", "replace")


def parse_scenario(path):
    """-> [(kind, payload, expected text, line no)] with kind in wait/run/check/checkfail."""
    steps = []
    for no, line in enumerate(read_text(clean_path(path)).splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        word, _, rest = s.partition(" ")
        lw = word.lower()
        if lw in WAIT_WORDS:
            try:
                steps.append(("wait", float(rest.strip() or 1), None, no))
            except ValueError:
                raise SystemExit("%s:%d 대기 시간은 숫자로 써 주세요: %s" % (path, no, s))
            continue
        kind = "run"
        if lw in CHECKFAIL_WORDS:
            kind, s = "checkfail", rest.strip()
        elif lw in CHECK_WORDS:
            kind, s = "check", rest.strip()
        expect = None
        if "=>" in s:
            s, _, expect = s.partition("=>")
            s, expect = s.strip(), expect.strip()
        if s.startswith("/"):
            s = s[1:]
        if s:
            steps.append((kind, s, expect, no))
    return steps


# ============================================================================ ticking areas


def plan_areas(world, mode, slots=10, max_rounds=3, focus=()):
    """-> (rounds [[(x1, z1, x2, z2), ...], ...], covered chunks, total chunks).
    Tiles holding a focus point (x, z) - coordinates written in the scenario - go into the first round."""
    sx, _sy, sz = world.spawn
    if mode == "none":
        return [[]], 0, 0
    if mode == "spawn":
        return [[(sx - 72, sz - 72, sx + 71, sz + 71)]], 0, 0
    if isinstance(mode, list):
        rects = mode
        return [rects[i:i + slots] for i in range(0, len(rects), slots)] or [[]], 0, 0
    chunks = world.chunk_keys(0)
    if not chunks:
        return [[(sx - 72, sz - 72, sx + 71, sz + 71)]], 0, 0
    have = {(cx, cz) for _d, cx, cz in chunks}
    minx = min(c[0] for c in have)
    minz = min(c[1] for c in have)
    tiles = collections.defaultdict(list)
    for cx, cz in have:
        tiles[((cx - minx) // 10, (cz - minz) // 10)].append((cx, cz))
    scx, scz = sx // 16, sz // 16
    rects = []
    for cs in tiles.values():
        x1, x2 = min(c[0] for c in cs), max(c[0] for c in cs)
        z1, z2 = min(c[1] for c in cs), max(c[1] for c in cs)
        d = (max(x1 - scx, 0, scx - x2) ** 2 + max(z1 - scz, 0, scz - z2) ** 2)
        hit = any(x1 * 16 <= fx <= x2 * 16 + 15 and z1 * 16 <= fz <= z2 * 16 + 15 for fx, fz in focus)
        rects.append((0 if hit else 1, d, (x1 * 16, z1 * 16, x2 * 16 + 15, z2 * 16 + 15), len(cs)))
    rects.sort()
    rects = rects[:slots * max_rounds]
    covered = sum(r[3] for r in rects)
    rects = [r[2] for r in rects]
    return [rects[i:i + slots] for i in range(0, len(rects), slots)], covered, len(have)


def scenario_points(steps):
    """(x, z) of every 'x y z' triple of plain numbers written in the scenario commands."""
    pts = []
    for kind, payload, _e, _n in steps:
        if kind == "wait":
            continue
        for m in re.finditer(r"(?<![~^\w.-])(-?\d+)\s+(-?\d+)\s+(-?\d+)(?![\w.])", payload):
            pts.append((int(m.group(1)), int(m.group(3))))
    return pts


def parse_area(s):
    try:
        x1, z1, x2, z2 = [int(float(v)) for v in re.split(r"[,\s]+", s.strip())]
    except ValueError:
        raise SystemExit("--area 는 auto, spawn, none 또는 x1,z1,x2,z2 형식입니다: %s" % s)
    return (min(x1, x2), min(z1, z2), max(x1, x2), max(z1, z2))


def ticking_in_use(srv):
    lines = srv.command("tickingarea list all-dimensions")
    for l in reversed(lines):
        m = re.search(r"(\d+)/(\d+) ticking areas in use", l)
        if m:
            return int(m.group(1)), int(m.group(2))
    return 0, 10


# ============================================================================ block change labels

WATER = {"water", "flowing_water"}
LAVA = {"lava", "flowing_lava"}
FALLING = {"sand", "red_sand", "gravel", "anvil", "chipped_anvil", "damaged_anvil", "dragon_egg", "scaffolding",
           "pointed_dripstone", "suspicious_sand", "suspicious_gravel", "snow_layer"}
FIRE = {"fire", "soul_fire"}
GROW_WORDS = ("vine", "mushroom", "amethyst_bud", "amethyst_cluster", "kelp", "bamboo", "cactus", "reeds",
              "sugar_cane", "chorus", "dripstone", "sapling", "pumpkin", "melon", "cocoa", "lichen")
ATTACH_WORDS = ("torch", "lantern", "sign", "banner", "button", "lever", "carpet", "rail", "flower", "sapling",
                "tallgrass", "short_grass", "tall_grass", "fern", "bush", "vine", "ladder", "redstone_wire",
                "repeater", "comparator", "candle", "pressure_plate", "door", "bed", "mushroom", "chain", "bell",
                "lily_pad", "waterlily", "head", "skull", "frame", "dripleaf", "azalea", "rose", "tulip", "daisy",
                "orchid", "allium", "cornflower", "dandelion", "poppy", "lilac", "peony", "sunflower", "kelp",
                "seagrass", "coral_fan", "sea_pickle", "glow_lichen", "hanging_roots", "spore_blossom",
                "tripwire", "cake", "pot", "amethyst_bud", "amethyst_cluster", "cactus", "sugar_cane", "reeds",
                "bamboo", "wheat", "carrots", "potatoes", "beetroot", "nether_wart", "cocoa", "berry")
STATE_HINTS = (
    (("age", "growth", "bite_counter", "berries"), "작물·식물이 자람 (정상)", False),
    (("redstone_signal", "powered_bit", "button_pressed_bit", "open_bit", "output_subtract_bit",
      "output_lit_bit", "lit", "toggle_bit", "triggered_bit", "active"), "작동/켜짐 상태가 바뀜", False),
    (("liquid_depth",), "액체 흐름 단계가 바뀜 — 물·용암이 흐르는 중일 수 있음", True),
    (("persistent_bit", "update_bit"), "나뭇잎 상태값이 바뀜 (보통 정상)", False),
    (("stability", "stability_check"), "비계(스캐폴딩) 지지 상태가 바뀜", True),
    (("dead_bit",), "산호가 죽음 (물 밖에 있는 산호)", True),
    (("height",), "눈 높이가 바뀜", False),
    (("cracked_state", "turtle_egg_count", "hatch"), "알이 부화하는 중", False),
)


def describe_change(layer, ka, kb):
    """(warn?, Korean label, short text) for one before->after pair."""
    a, b = ka[0], kb[0]
    lay = "물잠김층: " if layer else ""
    if a == b:
        sa, sb = dict(ka[1]), dict(kb[1])
        added = [k for k in sb if k not in sa]
        changed = [k for k in sa if k in sb and sa[k] != sb[k]]
        removed = [k for k in sa if k not in sb]
        if not changed and not removed:
            return False, lay + "서버가 자동으로 채운 속성 (연결 모양·계단 모서리 등, 정상)", "%s +%s" % (a, ",".join(
                k.replace("minecraft:", "") for k in added))
        for keys, text, warn in STATE_HINTS:
            if any(any(w in k for w in keys) for k in changed + added):
                detail = ", ".join("%s %s→%s" % (k.replace("minecraft:", ""), sa.get(k), sb.get(k)) for k in changed)
                return warn, lay + text, "%s (%s)" % (a, detail)
        detail = ", ".join("%s %s→%s" % (k.replace("minecraft:", ""), sa.get(k), sb.get(k)) for k in changed + removed)
        return False, lay + "블록 속성이 바뀜", "%s (%s)" % (a, detail)
    pair = "%s → %s" % (a, b)
    if a in ("ice", "frosted_ice") and b in WATER | {"air"}:
        return True, lay + "얼음이 녹음 (주변이 밝으면 녹습니다)", pair
    if a in ("snow_layer", "snow") and b == "air":
        return True, lay + "눈이 녹음", pair
    if b in WATER and a not in WATER:
        return True, lay + "물이 흘러 들어감 — 물이 새는 곳이 있는지 확인", pair
    if b in LAVA and a not in LAVA:
        return True, lay + "용암이 흘러 들어감 — 용암이 새는 곳이 있는지 확인", pair
    if a in WATER and b in WATER:
        return False, lay + "물이 고인 물/흐르는 물로 바뀜", pair
    if a in LAVA and b in LAVA:
        return False, lay + "용암이 고인 용암/흐르는 용암으로 바뀜", pair
    if a in WATER and b == "air":
        return True, lay + "물이 빠짐 (물이 흘러나간 자리)", pair
    if a in LAVA and b == "air":
        return True, lay + "용암이 빠짐", pair
    if a in FIRE or b in FIRE:
        return True, lay + "불이 붙거나 꺼짐", pair
    if a in FALLING and b in {"air"} | WATER:
        return True, lay + "중력 블록(모래·자갈 등)이 아래로 떨어짐", pair
    if b in FALLING and a in {"air"} | WATER:
        return True, lay + "떨어진 중력 블록이 쌓임", pair
    if a.endswith("leaves") and b == "air":
        return True, lay + "나무와 떨어진 나뭇잎이 사라짐", pair
    if (a in ("grass_block", "grass", "grass_path", "mycelium", "podzol", "dirt_with_roots") and b == "dirt") or (
            a in ("crimson_nylium", "warped_nylium") and b == "netherrack"):
        return False, lay + "위가 막혀 잔디·길·나일리엄이 흙/네더랙으로 바뀜 (자연스러운 변화)", pair
    if a == "dirt" and b in ("grass_block", "grass", "mycelium"):
        return False, lay + "흙에 잔디가 번짐 (자연스러운 변화)", pair
    if a == "farmland" and b == "dirt":
        return True, lay + "물이 없는 경작지가 흙으로 바뀜", pair
    if "coral" in a and b.startswith("dead_"):
        return True, lay + "산호가 죽음 (물 밖에 있는 산호)", pair
    if "copper" in a and "copper" in b:
        return False, lay + "구리가 산화됨", pair
    if b == "air" and a in ("reeds", "sugar_cane", "cactus"):
        return True, lay + ("사탕수수·선인장이 부서짐 (사탕수수는 밑 블록 바로 옆에 물이 있어야 하고, "
                            "선인장은 옆에 블록이 없어야 합니다)"), pair
    if a == "air" and any(w in b for w in GROW_WORDS):
        return False, lay + "식물·자수정 등이 자라남 (정상)", pair
    if b == "air":
        if any(w in a for w in ATTACH_WORDS):
            return True, lay + "받침이 없어 떨어져 나간 블록 (밑이나 뒤에 붙을 블록이 있는지 확인)", pair
        return True, lay + "블록이 사라짐", pair
    if a == "air":
        return True, lay + "블록이 새로 생김", pair
    return False, lay + "블록 이름이 바뀜 (서버 버전에서 이름이 바뀐 블록이면 정상, 예: chain → iron_chain)", pair


def fmt_pos(p):
    dim, x, y, z = p
    return ("%d %d %d" % (x, y, z)) + ("" if dim == 0 else " (%s)" % bdb.DIM_NAMES.get(dim, dim))


def change_section(res, out, limit=25):
    out.append("  비교한 서브청크 %d개 중 %d개에서 변화, 새로 생긴 청크 %d개" % (
        res["compared"], res["changed_subchunks"], len(res["new_chunks"])))
    if res["unreadable"]:
        out.append("  (읽을 수 없는 옛 형식 서브청크 %d개는 건너뜀)" % res["unreadable"])
    groups = collections.OrderedDict()
    for layer, ka, kb, n, ex in res["blocks"]:
        warn, label, short = describe_change(layer, ka, kb)
        g = groups.setdefault((warn, label), dict(n=0, items=collections.Counter(), ex={}))
        g["n"] += n
        g["items"][short] += n
        g["ex"].setdefault(short, ex)
    if not groups:
        out.append("  블록 변화 없음")
    for warn_flag, title in ((True, "주의해서 볼 변화"), (False, "자연스러운 변화 (대부분 괜찮음)")):
        items = [(k, g) for k, g in groups.items() if k[0] == warn_flag]
        if not items:
            continue
        out.append("  %s:" % title)
        items.sort(key=lambda kg: -kg[1]["n"])
        for (_w, label), g in items[:limit]:
            out.append("    - %s: 총 %d개" % (label, g["n"]))
            for short, n in g["items"].most_common(4):
                out.append("        %s  %d개  예) %s" % (short, n, ", ".join(fmt_pos(p) for p in g["ex"][short][:2])))
            if len(g["items"]) > 4:
                out.append("        외 %d종류" % (len(g["items"]) - 4))
    if res["new_chunks"]:
        out.append("  새로 생긴 청크 %d개: 원래 월드에 없던 땅을 서버가 새로 만들었습니다 (테스트 범위가 월드 밖까지"
                   " 닿았거나 월드가 무한 생성 월드인 경우)." % len(res["new_chunks"]))


ENTITY_KO = {"item": "떨어진 아이템", "xp_orb": "경험치 구슬", "arrow": "화살", "npc": "NPC",
             "armor_stand": "갑옷 거치대", "falling_block": "떨어지는 블록", "tnt": "점화된 TNT",
             "lightning_bolt": "번개", "player": "플레이어"}


def entity_section(res, out):
    changed = [(k, a, b) for k, a, b in res["entities"] if a != b]
    ta = sum(a for _k, a, _b in res["entities"])
    tb = sum(b for _k, _a, b in res["entities"])
    out.append("  전체 %d → %d" % (ta, tb))
    if not changed:
        out.append("  종류별 변화 없음")
    for k, a, b in sorted(changed, key=lambda e: -abs(e[2] - e[1]))[:30]:
        out.append("    %-28s %4d → %-4d %s" % (k, a, b, ENTITY_KO.get(k, "")))
    if res["block_entities_lost"]:
        out.append("  [주의] 사라진 블록 데이터 (상자 내용물, 표지판 글 등이 지워졌을 수 있음):")
        for k, n in res["block_entities_lost"][:15]:
            out.append("    %s %d개" % (k, n))
        out.append("    예) " + ", ".join(fmt_pos(p) for p in res["block_entities_lost_at"][:6]))
    if res["block_entities_new"]:
        out.append("  서버가 새로 만든 블록 데이터 (보통 문제없음): " + ", ".join(
            "%s %d" % (k, n) for k, n in res["block_entities_new"][:12]))


# ============================================================================ log analysis


def analyze_log(lines):
    """-> (pack stack lines, [(level, message, count)] errors/warnings)."""
    packs, msgs, order = [], collections.Counter(), []
    for l in lines:
        m = LOG_RE.match(l)
        if not m:
            continue
        level, msg = m.group(2), m.group(3).strip()
        if "Pack Stack" in msg:
            packs.append(msg)
        if level in ("WARN", "ERROR") and msg:
            key = (level, clean(msg))
            if key not in msgs:
                order.append(key)
            msgs[key] += 1
    return packs, [(lv, m, msgs[(lv, m)]) for lv, m in order]


def split_command_errors(lines):
    """Messages that were answers to our own commands (expected failures) are not content errors."""
    answers = set()
    in_answer = False
    for l in lines:
        if l.startswith(">>> "):
            in_answer = True
            continue
        m = LOG_RE.match(l)
        if m and in_answer and m.group(2) == "ERROR" and "[" not in m.group(3)[:1]:
            answers.add(clean(m.group(3).strip()))
        if m and m.group(2) == "INFO":
            in_answer = False
    return answers


# ============================================================================ test


def run_test(world_path, script=None, seconds=60, area="auto", port=19142, max_rounds=3, load_wait=10,
             quiet=False):
    if not ensure_server():
        return 2
    src = open_world_source(world_path)
    print("월드 읽는 중: %s" % src)
    before = bdb.World(src)
    steps = parse_scenario(script) if script else []
    has_own_areas = any(k != "wait" and p.lower().startswith("tickingarea") for k, p, _e, _n in steps)
    if area == "auto" and has_own_areas:
        area = "none"
    areas_mode = area if area in ("auto", "spawn", "none") else [parse_area(a) for a in area.split(";")]
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = os.path.join(RESULTS_DIR, "%s_%s" % (safe_name(before.name), stamp))
    os.makedirs(out_dir, exist_ok=True)
    copy_world(src, TEST_WORLD)
    srv = Server(TEST_WORLD, server_props(before.level, port, lan=False))
    print("서버 시작 중... (서버 버전 %s)" % (server_version() or "?"))
    t_start = time.time()
    results, rounds_info, started, covered, total = [], [], False, 0, 0
    try:
        started = srv.start()
        if not started:
            print("서버가 시작되지 않았습니다. " + start_failure_hint(srv))
        else:
            print("서버 시작됨 (%.1f초)" % (srv.started_at - t_start))
            used, cap = ticking_in_use(srv)
            slots = max(cap - used, 0)
            if slots:
                rounds, covered, total = plan_areas(before, areas_mode, slots, max_rounds, scenario_points(steps))
            else:
                print("  월드에 이미 실행 범위(tickingarea)가 %d개 있어서 더 추가하지 않습니다." % used)
                rounds = [[]]
            for ri, rects in enumerate(rounds):
                names = []
                for i, (x1, z1, x2, z2) in enumerate(rects):
                    nm = "vmc%d" % i
                    ans = srv.command("tickingarea add %d 0 %d %d 0 %d %s true" % (x1, z1, x2, z2, nm), quiet=0.3)
                    if judge(ans) == "fail":
                        print("  실행 범위 추가 실패: %s" % " / ".join(clean(a) for a in ans))
                    else:
                        names.append(nm)
                rounds_info.append(rects)
                if rects:
                    print("%d회차: 실행 범위 %d곳을 불러오는 중..." % (ri + 1, len(rects)))
                t_round = time.time()
                if ri == 0:
                    srv.wait(load_wait if rects else 2)
                    for kind, payload, expect, no in steps:
                        if not srv.alive():
                            break
                        if kind == "wait":
                            print("  대기 %g초" % payload)
                            srv.wait(payload)
                            continue
                        ans = srv.command(payload)
                        verdict = judge(ans)
                        text = [clean(a) for a in ans]
                        passed = None
                        if kind == "check":
                            if expect:
                                passed = any(expect.lower() in t.lower() for t in text)
                            else:
                                passed = verdict == "ok"
                        elif kind == "checkfail":
                            passed = verdict == "fail" and (not expect or any(expect.lower() in t.lower() for t in text))
                        results.append(dict(kind=kind, cmd=payload, expect=expect, line=no, answer=text,
                                            verdict=verdict, passed=passed))
                        mark = {True: "통과", False: "실패", None: ""}[passed]
                        first = LOG_RE.sub(r"\3", text[0]) if text else "(응답 없음)"
                        print("  %s> %s%s" % ("[%s] " % mark if mark else "", payload,
                                              "" if quiet else "\n      " + first[:160]))
                remain = seconds - (time.time() - t_round)
                if remain > 0 and srv.alive():
                    print("  %d초 동안 월드를 돌리는 중..." % remain)
                    srv.wait(remain)
                for nm in names:
                    srv.command("tickingarea remove %s" % nm, quiet=0.3, max_wait=3)
    except KeyboardInterrupt:
        print("\n중단했습니다. 서버를 끄는 중...")
    finally:
        code = srv.stop()
    log_lines = [l for _t, l in srv.lines]
    open(os.path.join(out_dir, "server.log"), "w", encoding="utf-8").write("\n".join(log_lines) + "\n")
    saved = os.path.join(SERVER_DIR, "worlds", TEST_WORLD)
    diff = None
    if started:
        print("저장된 월드와 원본 비교 중...")
        try:
            diff = bdb.diff_worlds(before, bdb.World(saved))
        except Exception as e:                       # report what we have rather than crash
            print("  비교 실패: %r" % e)
    report = build_report(before, src, srv, started, code, results, rounds_info, diff, seconds, log_lines,
                          time.time() - t_start, covered, total)
    path = os.path.join(out_dir, "report.txt")
    open(path, "w", encoding="utf-8-sig").write(report)
    print()
    print(report)
    print("결과 저장 위치: %s" % out_dir)
    failed = (not started) or any(r["passed"] is False for r in results)
    return 1 if failed else 0


def build_report(world, src, srv, started, code, results, rounds, diff, seconds, log_lines, elapsed, covered,
                 total):
    out = []
    lv = world.level
    out.append("=" * 70)
    out.append(" 가상 마인크래프트 테스트 결과")
    out.append("=" * 70)
    out.append("월드: %s   (%s)" % (clean(world.name), src))
    out.append("스폰: %d %d %d   게임 모드: %s   난이도: %s" % (world.spawn + (
        GAMEMODES.get(lv.get("GameType"), lv.get("GameType")), DIFFICULTIES.get(lv.get("Difficulty"), "?"))))
    out.append("서버 버전: %s   테스트 시각: %s   걸린 시간: %.0f초" % (
        server_version() or "?", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), elapsed))
    out.append("")
    out.append("[1] 서버 실행")
    if started:
        out.append("  정상적으로 월드를 열었습니다." + ("" if code in (0, None) else " (종료 코드 %s)" % code))
    else:
        out.append("  [실패] 서버가 월드를 열지 못했습니다. 아래 로그 끝부분:")
        out += ["    " + clean(l) for l in log_lines[-25:]]
    packs, msgs = analyze_log(log_lines)
    out.append("")
    out.append("[2] 행동 팩 / 리소스 팩")
    names = pack_names(src)
    wanted = world_packs(src)
    if not wanted and not packs:
        out.append("  월드에 연결된 팩이 없습니다.")
    for uuid, kind in wanted:
        nm = names.get(uuid, ("(월드 폴더 안에 없는 팩)", kind))[0]
        ok = any(uuid in p.lower() for p in packs)
        out.append("  - %s 팩 '%s' (%s…): %s" % ("행동" if kind == "behavior" else "리소스", nm, uuid[:8],
                                               "불러옴" if ok else "[주의] 서버가 불러오지 않음"))
        if not ok and uuid not in names:
            out.append("      월드 폴더 안에 이 팩이 없습니다. 게임에서 월드를 내보낼 때 팩이 같이 들어갔는지 확인하세요.")
    for p in packs:
        out.append("    서버 기록: " + clean(p)[:150])
    answers = split_command_errors(log_lines)
    content = [(lv_, m, n) for lv_, m, n in msgs if m not in answers]
    errors = [x for x in content if x[0] == "ERROR"]
    warns = [x for x in content if x[0] == "WARN"]
    out.append("")
    out.append("[3] 콘텐츠 로그 (팩·스크립트·함수 오류)")
    out.append("  오류 %d종류, 경고 %d종류" % (len(errors), len(warns)))
    for lv_, m, n in (errors + warns)[:40]:
        out.append("  %s %s%s" % ("[오류]" if lv_ == "ERROR" else "[경고]", m[:200], "  (x%d)" % n if n > 1 else ""))
    if len(errors + warns) > 40:
        out.append("  ... 나머지는 server.log 에 있습니다.")
    if warns and all("[Scripting]" in m for _l, m, _n in warns):
        out.append("  (스크립트의 console.warn 출력도 경고로 표시됩니다.)")
    out.append("")
    out.append("[4] 명령 / 확인 결과")
    if not results:
        out.append("  실행한 시나리오 명령 없음")
    checks = [r for r in results if r["passed"] is not None]
    if checks:
        npass = sum(1 for r in checks if r["passed"])
        out.append("  확인 %d개 중 %d개 통과, %d개 실패" % (len(checks), npass, len(checks) - npass))
    for r in results:
        tag = {True: "[통과]", False: "[실패]", None: "      "}[r["passed"]]
        want = ""
        if r["kind"] == "checkfail":
            want = "  (실패해야 통과)"
        if r["expect"]:
            want += "  (기대 문구: %s)" % r["expect"]
        out.append("  %s %d행: %s%s" % (tag, r["line"], r["cmd"], want))
        ans = [LOG_RE.sub(r"\3", a) for a in r["answer"] if a.strip()] or ["(응답 없음)"]
        for a in ans[:6]:
            out.append("           %s" % a[:180])
    out.append("")
    out.append("[5] 블록 변화 (서버를 돌린 뒤 저장된 월드와 원본 비교)")
    nar = sum(len(r) for r in rounds)
    if nar:
        out.append("  실행 범위: %d곳, %d회차, 회차마다 %d초%s" % (nar, len(rounds), seconds, (
            ", 월드 청크 %d개 중 %d개" % (total, covered)) if total else ""))
        if total and covered < total:
            out.append("  (청크가 많아 스폰에서 가까운 곳부터 일부만 돌렸습니다. --max-rounds 로 늘릴 수 있습니다.)")
    else:
        out.append("  실행 범위를 따로 추가하지 않았습니다 (시나리오의 tickingarea 명령 또는 --area none).")
    if diff is None:
        out.append("  비교하지 못했습니다.")
    else:
        try:
            change_section(diff, out)
        except Exception as e:                       # keep the rest of the report
            out.append("  블록 변화를 정리하다 오류가 났습니다: %r" % e)
    out.append("")
    out.append("[6] 엔티티 · 블록 데이터 (전 → 후)")
    if diff is not None:
        try:
            entity_section(diff, out)
        except Exception as e:
            out.append("  엔티티 변화를 정리하다 오류가 났습니다: %r" % e)
    out.append("")
    out.append("[참고] 서버에는 접속한 플레이어가 없어서 우클릭, 버튼·문 누르기, 상자·NPC 화면, 실제 화면 모습은")
    out.append("       시험되지 않습니다. 그런 것은 'console' 모드로 서버를 켜고 내 게임으로 접속해 확인하세요.")
    out.append("       서버를 돌리지 않은 청크(실행 범위 밖)는 변화가 없는 것으로 나옵니다.")
    return "\n".join(out) + "\n"


# ============================================================================ console


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def run_console(world_path, port=19132, keep=False, export_ask=True):
    if not ensure_server():
        return 2
    saved = os.path.join(SERVER_DIR, "worlds", CONSOLE_WORLD)
    if keep and os.path.isdir(saved):
        print("지난번 콘솔 월드를 이어서 엽니다: %s" % saved)
        level = bdb.read_level_dat(os.path.join(saved, "level.dat"))
    else:
        src = open_world_source(world_path)
        copy_world(src, CONSOLE_WORLD)
        level = bdb.read_level_dat(os.path.join(src, "level.dat"))
    srv = Server(CONSOLE_WORLD, server_props(level, port, lan=True, allow_list=False))
    print("서버 시작 중...")
    if not srv.start():
        print("서버가 시작되지 않았습니다. " + start_failure_hint(srv))
        print("\n".join(clean(l) for _t, l in srv.lines[-20:]))
        srv.stop()
        return 1
    # without players no chunk is loaded, so commands like testforblock would fail: keep the world ticking
    names = []
    used, cap = ticking_in_use(srv)
    if cap - used > 0:
        rounds, _c, _t = plan_areas(bdb.World(saved), "auto", cap - used, 1)
        for i, (x1, z1, x2, z2) in enumerate(rounds[0]):
            nm = "vmc%d" % i
            ans = srv.command("tickingarea add %d 0 %d %d 0 %d %s true" % (x1, z1, x2, z2, nm), quiet=0.3, max_wait=3)
            if judge(ans) != "fail":
                names.append(nm)
    srv.echo = True
    print()
    print("-" * 70)
    print(" 서버가 켜졌습니다. 명령어를 입력하고 Enter (앞에 / 없이). 끝내려면 stop 또는 Ctrl+C")
    print(" 예) time set day   |   testforblock 0 64 0 stone   |   function 내함수   |   op 내닉네임")
    if names:
        print(" 명령이 닿도록 스폰 근처부터 실행 범위(tickingarea) %d곳을 켜 두었습니다 (끝낼 때 지웁니다)." % len(names))
    print(" 내 게임으로 접속: 플레이 → 서버 → 서버 추가 → 주소 %s (다른 기기) 또는 127.0.0.1 (같은 PC), 포트 %d"
          % (local_ip(), port))
    print("-" * 70)
    try:
        while srv.alive():
            try:
                cmd = input()
            except EOFError:
                break
            cmd = cmd.strip()
            if not cmd:
                continue
            if cmd.startswith("/"):
                cmd = cmd[1:]
            if cmd.lower() in ("stop", "exit", "quit", "종료"):
                break
            srv.send(cmd)
    except KeyboardInterrupt:
        print()
    srv.wait(1.5)                      # let the answer to the last command arrive
    print("서버를 끄는 중...")
    srv.echo = False
    for nm in names:
        srv.command("tickingarea remove %s" % nm, quiet=0.3, max_wait=3)
    srv.stop()
    if export_ask and ask("바뀐 월드를 .mcworld 파일로 저장할까요? (y/n): ").lower() in ("y", "yes", "ㅛ"):
        os.makedirs(RESULTS_DIR, exist_ok=True)
        name = safe_name(clean(str(level.get("LevelName", "world"))))
        dst = os.path.join(RESULTS_DIR, "%s_console_%s.mcworld" % (name, datetime.datetime.now().strftime(
            "%Y%m%d-%H%M%S")))
        zip_world(saved, dst)
        print("저장했습니다: %s" % dst)
    return 0


def zip_world(folder, dst):
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _dirs, files in os.walk(folder):
            for fn in files:
                if fn == "LOCK":
                    continue
                p = os.path.join(root, fn)
                z.write(p, os.path.relpath(p, folder))


# ============================================================================ info / diff


def run_info(world_path):
    src = open_world_source(world_path)
    w = bdb.World(src)
    lv = w.level
    chunks = {}
    for dim in (0, 1, 2):
        ks = w.chunk_keys(dim)
        if ks:
            xs = [k[1] for k in ks]
            zs = [k[2] for k in ks]
            chunks[dim] = (len(ks), min(xs) * 16, min(zs) * 16, max(xs) * 16 + 15, max(zs) * 16 + 15)
    print("월드 이름: %s" % clean(w.name))
    print("폴더: %s" % src)
    print("스폰: %d %d %d" % w.spawn)
    print("게임 모드: %s   난이도: %s   치트: %s" % (GAMEMODES.get(lv.get("GameType"), lv.get("GameType")),
                                            DIFFICULTIES.get(lv.get("Difficulty"), lv.get("Difficulty")),
                                            "켜짐" if lv.get("commandsEnabled") else "꺼짐"))
    ver = lv.get("lastOpenedWithVersion")
    if isinstance(ver, list):
        print("마지막으로 연 게임 버전: %s" % ".".join(str(v) for v in ver))
    for dim, (n, x1, z1, x2, z2) in chunks.items():
        print("%s: 청크 %d개, 범위 x %d~%d, z %d~%d" % (bdb.DIM_NAMES[dim], n, x1, x2, z1, z2))
    names = pack_names(src)
    for uuid, kind in world_packs(src):
        print("%s 팩: %s (%s)" % ("행동" if kind == "behavior" else "리소스",
                                names.get(uuid, ("월드 폴더 안에 없음", kind))[0], uuid))
    ents = collections.Counter(e[0] for e in w.entities())
    print("엔티티 %d개: %s" % (sum(ents.values()), ", ".join("%s %d" % kv for kv in ents.most_common(15)) or "없음"))
    named = [e for e in w.entities() if e[2]]
    for ident, pos, nm in named[:20]:
        print("    %s '%s' at %s" % (ident, clean(nm), " ".join("%g" % p for p in pos)))
    be = collections.Counter(w.block_entities().values())
    print("블록 데이터 %d개: %s" % (sum(be.values()), ", ".join("%s %d" % kv for kv in be.most_common(12)) or "없음"))
    rules = [k for k in ("dodaylightcycle", "doweathercycle", "domobspawning", "keepinventory", "falldamage",
                         "firedamage", "mobgriefing", "pvp", "showcoordinates") if k in lv]
    if rules:
        print("게임 규칙: " + ", ".join("%s=%s" % (k, lv[k]) for k in rules))
    return 0


def run_diff(a_path, b_path):
    a = bdb.World(open_world_source(a_path))
    b = bdb.World(open_world_source(b_path))
    print("비교: '%s' → '%s'" % (clean(a.name), clean(b.name)))
    res = bdb.diff_worlds(a, b)
    out = ["[블록 변화]"]
    change_section(res, out)
    out.append("[엔티티 · 블록 데이터]")
    entity_section(res, out)
    print("\n".join(out))
    return 0


# ============================================================================ menu


def menu(world=None):
    while True:
        print()
        print("=" * 60)
        print(" 가상 마인크래프트 테스트 도구")
        print("=" * 60)
        ver = server_version() if os.path.exists(server_exe()) else None
        print(" 서버: %s" % ("버전 %s" % ver if ver else "설치 안 됨 (6번으로 설치)"))
        print(" 월드: %s" % (world or "(아직 고르지 않음)"))
        print()
        print(" 1. 월드 테스트 — 열리는지, 팩·스크립트 오류, 1분 돌린 뒤 블록 변화")
        print(" 2. 시나리오로 테스트 — 명령 파일을 차례로 실행하고 결과 확인")
        print(" 3. 콘솔 — 서버를 켜고 직접 명령 입력 (내 게임으로 접속도 가능)")
        print(" 4. 월드 정보 보기")
        print(" 5. 두 월드 비교")
        print(" 6. 서버 설치 / 업데이트")
        print(" 7. 다른 월드 고르기")
        print(" 0. 끝내기")
        c = ask("\n번호: ")
        try:
            if c == "0" or c.lower() in ("q", "exit"):
                return 0
            if c == "6":
                setup()
                continue
            if c == "7":
                world = None
            if c in ("1", "2", "3", "4", "5", "7") and not world:
                world = clean_path(ask("월드 파일(.mcworld)이나 월드 폴더를 이 창에 끌어다 놓고 Enter: "))
                if not world:
                    continue
            if c == "1":
                secs = ask("몇 초 동안 돌릴까요? [60]: ", "60")
                run_test(world, seconds=float(secs))
            elif c == "2":
                sc = clean_path(ask("시나리오 파일(.txt)을 끌어다 놓고 Enter: "))
                if sc:
                    secs = ask("시나리오가 끝난 뒤 포함해서 몇 초 동안 돌릴까요? [30]: ", "30")
                    run_test(world, script=sc, seconds=float(secs))
            elif c == "3":
                run_console(world)
            elif c == "4":
                run_info(world)
            elif c == "5":
                other = clean_path(ask("비교할 다른 월드(바뀐 뒤)를 끌어다 놓고 Enter: "))
                if other:
                    run_diff(world, other)
        except SystemExit as e:
            if e.code not in (None, 0):
                print(e.code if isinstance(e.code, str) else "오류가 발생했습니다.")
        except Exception as e:
            print("오류: %r" % e)
        ask("\nEnter 를 누르면 메뉴로 돌아갑니다...")


# ============================================================================ main


def main(argv=None):
    ap = argparse.ArgumentParser(prog="vmc", description="가상 마인크래프트(Bedrock 전용 서버) 월드 테스트 도구")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("setup", help="서버(BDS) 내려받기 / 업데이트")
    p.add_argument("--yes", action="store_true", help="EULA 동의를 묻지 않음")
    p.add_argument("--preview", action="store_true", help="미리보기(베타) 서버 받기")
    p.add_argument("--url", help="직접 지정한 서버 zip 주소")
    p.add_argument("--force", action="store_true", help="같은 버전이어도 다시 받기")
    p = sub.add_parser("test", help="월드 테스트")
    p.add_argument("world")
    p.add_argument("--script", help="시나리오 파일 (명령 목록)")
    p.add_argument("--seconds", type=float, default=60, help="회차마다 월드를 돌릴 시간 (기본 60초)")
    p.add_argument("--area", default="auto",
                   help="auto(월드 전체, 기본) | spawn | none | 'x1,z1,x2,z2;x1,z1,x2,z2'")
    p.add_argument("--max-rounds", type=int, default=3, help="auto 범위일 때 최대 회차 (회차마다 10곳)")
    p.add_argument("--port", type=int, default=19142, help="테스트 서버 포트 (기본 19142)")
    p.add_argument("--load-wait", type=float, default=10, help="실행 범위를 불러오는 대기 시간 (기본 10초)")
    p = sub.add_parser("console", help="서버를 켜고 직접 명령 입력")
    p.add_argument("world", nargs="?")
    p.add_argument("--port", type=int, default=19132)
    p.add_argument("--keep", action="store_true", help="지난번 콘솔 월드를 이어서 열기")
    p.add_argument("--no-export", action="store_true", help="끝날 때 저장 여부를 묻지 않음")
    p = sub.add_parser("info", help="월드 정보")
    p.add_argument("world")
    p = sub.add_parser("diff", help="두 월드 비교")
    p.add_argument("before")
    p.add_argument("after")
    p = sub.add_parser("menu", help="메뉴")
    p.add_argument("world", nargs="?")
    args = ap.parse_args(argv)
    if args.cmd in (None, "menu"):
        return menu(clean_path(args.world) if getattr(args, "world", None) else None)
    if args.cmd == "setup":
        return 0 if setup(args.preview, args.yes, args.url, args.force) else 1
    if args.cmd == "test":
        return run_test(args.world, args.script, args.seconds, args.area, args.port, args.max_rounds,
                        args.load_wait)
    if args.cmd == "console":
        if not args.world and not args.keep:
            ap.error("월드를 지정하거나 --keep 을 쓰세요")
        return run_console(args.world, args.port, args.keep, not args.no_export)
    if args.cmd == "info":
        return run_info(args.world)
    if args.cmd == "diff":
        return run_diff(args.before, args.after)
    return 0


if __name__ == "__main__":
    sys.exit(main())
