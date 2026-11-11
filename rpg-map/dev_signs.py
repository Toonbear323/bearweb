import sys, time, re
sys.path.insert(0, '.')
import build
build.T0 = time.time()
w, n, T = build.build()
def width(line):
    bold = '§l' in line
    line = re.sub('§.', '', line)
    return sum((9 if ord(c) > 0x2E80 else 4 if c == ' ' else 3 if c in '.,:·!()' else 6) + (1 if bold and c != ' ' else 0) for c in line)
bad = 0
for wd in (w, n):
    for pos, d in wd.be.items():
        if d['id'] in ('Sign', 'HangingSign'):
            t = d['FrontText']['Text']
            lines = t.split('\n')
            mx = max(width(l) for l in lines)
            lim = 88 if d['id'] == 'Sign' else 52
            if len(lines) > 4 or mx > lim:
                bad += 1
                print(pos, d['id'], len(lines), mx, repr(t))
print('bad signs', bad)
