"""Copy unitbalance.slk and set movement speed (spd) for the player heroes."""
import sys, re
src, dst = sys.argv[1], sys.argv[2]
FACTOR = 1.2
HEROES = ["Ugrk", "Ugr2", "Ugr3", "Uany", "Hleo", "Uctl", "Ujsm"]  # Uctl Landen, Ujsm Ilastar (Act 1)
data = open(src, "rb").read()
lines = data.split(b"\n")
# pass 1: find header column for spd and row for each hero
y = x = 0; spd_col = None; rows = {}
pos = []
for i, ln in enumerate(lines):
    if ln.startswith(b"C;"):
        for p in ln.rstrip(b"\r").split(b";")[1:]:
            if p[:1] == b"X": x = int(p[1:])
            elif p[:1] == b"Y": y = int(p[1:])
        m = re.search(rb";K(.*)$", ln.rstrip(b"\r"))
        val = m.group(1).strip(b'"') if m else None
        pos.append((i, y, x))
        if y == 1 and val == b"spd": spd_col = x
        if x == 1 and val and val.decode() in HEROES: rows[y] = val.decode()
assert spd_col and len(rows) == len(HEROES), (spd_col, rows)
changed = 0
for i, yy, xx in pos:
    if xx == spd_col and yy in rows:
        ln = lines[i]; cr = ln.endswith(b"\r"); body = ln.rstrip(b"\r")
        m = re.search(rb";K(\d+)$", body); assert m, body
        old = int(m.group(1)); new = round(old * FACTOR)
        lines[i] = body[:m.start(1)] + str(new).encode() + (b"\r" if cr else b"")
        print(rows[yy], old, "->", new); changed += 1
assert changed == len(HEROES)
open(dst, "wb").write(b"\n".join(lines))
