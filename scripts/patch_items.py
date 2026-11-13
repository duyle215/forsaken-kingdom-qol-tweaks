"""Re-level the randomly droppable equipment in units/itemdata.slk.

The drop code in the maps cannot be changed: the game ignores war3map.luac
placed in the local-files folder, and refuses rebuilt .w3xd files. The game
does read units/itemdata.slk from local files, so this changes WHAT drops,
not HOW OFTEN.

Every random drop calls ChooseRandomItemExWithFilterBJ(level, EQUIPMENT, ANY,
DROPPABLE): one item of that Level with tag "Droppable". The tier rolls pick
level 1-2 (Common roll), 3-4 (Uncommon), 5-6 (Rare), 7 (Epic), 8 (Legendary).
So:
  - Common and Uncommon droppable items move to JUNK_LEVEL, which nothing
    rolls, so they stop dropping at random.
  - Rare, Epic and Legendary droppable items are spread over levels 1-8 as in
    LAYOUT. Rarity colour comes from the item name, not from Level.
Other tags (Boss Drop, Shop, World, Quest Reward, Secret) are left alone.
"pickRandom" is 0 for all of them in 3.0.1 and drops still happen, so the
filter ignores it.

Usage: python -I patch_items.py <itemdata.slk in> <itemdata.slk out> <itemstrings.txt>
"""
import re
import sys

JUNK_LEVEL = 9
# level: (Legendary, Epic, Rare). None = all items of that rarity still left.
# Level 1 is also what farm camp leaders always drop.
# Levels 1-5 are rolled most often and hold only Epic and Legendary (late game
# only uses those). Rares go to the rarer rolls 6-8.
LAYOUT = {
    1: (2, 2, 0),
    2: (2, 5, 0),
    3: (1, 8, 0),
    4: (1, 8, 0),
    5: (0, 8, 0),
    6: (0, 0, 24),
    7: (0, 0, None),
    8: (0, 0, 1),
}
# SkipScarletCrusadeItems() in every map re-rolls these at the same level.
# They stay at level 7, which also holds other items so the re-roll ends.
SCARLET = {"epmm", "ehtc", "ehtf", "ehtj", "ehtm", "ehtv"}
EXPECTED = {"Common": 47, "Uncommon": 55, "Rare": 49, "Epic": 36, "Legendary": 6}
# Non-droppable items that also become random drops:
# id -> (rarity, level, original tag). Level 1 is what farm camp leaders drop.
# Rewards that are hard to earn for casual players:
#   eeh3 Master Engineering Goggles: 1st place in Silverpine Sprint
#        (undeadre01 OQ_03_Rally_Reward); the race code cannot be changed.
#   eeh2 Greater Engineering Goggles: 2nd-3rd place in the same race.
#   ergp Gift of Pride, ergw Gift of Wrath, ergs Gift of Sloth: killing the
#        Pride (30:00), Wrath (22:30) and Sloth (15:00) bosses in Forsaken
#        Survival (undeadre02_01).
EXTRA_DROPS = {
    "eeh3": ("Epic", 1, "Quest Reward"),
    "ergp": ("Epic", 1, "Boss Drop"),
    "eeh2": ("Rare", 1, "Quest Reward"),
    "ergw": ("Rare", 1, "Boss Drop"),
    "ergs": ("Rare", 1, "Boss Drop"),
}


def rarities(path):
    out, cur = {}, None
    for ln in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"\[(\w{4})\]", ln)
        if m:
            cur = m.group(1)
        elif ln.startswith("Ubertip=") and cur:
            r = re.search(r"\|c\w{8}(Common|Uncommon|Rare|Epic|Legendary) ", ln)
            if r:
                out[cur] = r.group(1)
    return out


def main(src, dst, strings):
    rar = rarities(strings)
    lines = open(src, "rb").read().split(b"\n")
    cells = {}  # (y, x) -> line index
    vals = {}
    y = x = 0
    for i, ln in enumerate(lines):
        if not ln.startswith(b"C;"):
            continue
        body = ln.rstrip(b"\r")
        for p in body.split(b";")[1:]:
            if p[:1] == b"X":
                x = int(p[1:])
            elif p[:1] == b"Y":
                y = int(p[1:])
        m = re.search(rb";K(.*)$", body)
        if m:
            cells[(y, x)] = i
            vals[(y, x)] = m.group(1).strip(b'"').decode()
    hdr = {v: xx for (yy, xx), v in vals.items() if yy == 1}
    col = {k: hdr[k] for k in ("itemID", "class", "Level", "oldLevel", "tag")}

    pools = {t: [] for t in EXPECTED}
    for (yy, xx), v in sorted(vals.items()):
        if xx != col["itemID"] or yy == 1:
            continue
        g = lambda k: vals.get((yy, col[k]))
        if g("class") != "Equipment" or g("tag") != "Droppable":
            continue
        t = rar.get(v)
        assert t in EXPECTED, (v, t)
        assert g("Level") == g("oldLevel"), v
        pools[t].append((int(g("Level")), v, yy))
    got = {t: len(p) for t, p in pools.items()}
    assert got == EXPECTED, ("itemdata.slk changed, re-check the layout", got)

    new_level = {}
    for t in ("Common", "Uncommon"):
        for _, v, yy in pools[t]:
            new_level[yy] = (v, t, JUNK_LEVEL)
    for i, t in enumerate(("Legendary", "Epic", "Rare")):
        items = sorted(p for p in pools[t] if p[1] not in SCARLET)
        for _, v, yy in (p for p in pools[t] if p[1] in SCARLET):
            new_level[yy] = (v, t, 7)
        for lv in sorted(LAYOUT, key=lambda k: LAYOUT[k][i] is None):
            n = LAYOUT[lv][i]
            take, items = (items, []) if n is None else (items[:n], items[n:])
            for _, v, yy in take:
                new_level[yy] = (v, t, lv)
        assert not items, (t, "left over", items)

    rows = {v: yy for (yy, xx), v in vals.items() if xx == col["itemID"] and yy != 1}
    for v, (t, lv, tag) in EXTRA_DROPS.items():
        yy = rows[v]
        assert rar.get(v) == t and vals.get((yy, col["class"])) == "Equipment", v
        assert vals.get((yy, col["tag"])) == tag, (v, vals.get((yy, col["tag"])))
        new_level[yy] = (v, t, lv)
        i = cells[(yy, col["tag"])]
        cr = lines[i].endswith(b"\r")
        body = lines[i].rstrip(b"\r")
        m = re.search(rb';K"' + re.escape(tag.encode()) + rb'"$', body)
        assert m, body
        lines[i] = body[:m.start()] + b';K"Droppable"' + (b"\r" if cr else b"")

    for yy, (v, t, lv) in new_level.items():
        for k in ("Level", "oldLevel"):
            i = cells[(yy, col[k])]
            ln = lines[i]
            cr = ln.endswith(b"\r")
            body = ln.rstrip(b"\r")
            m = re.search(rb";K(\d+)$", body)
            assert m, body
            lines[i] = body[:m.start(1)] + str(lv).encode() + (b"\r" if cr else b"")
    open(dst, "wb").write(b"\n".join(lines))

    # report per level
    for lv in range(1, JUNK_LEVEL + 1):
        row = [(t, v) for v, t, l in new_level.values() if l == lv]
        if row:
            print("Level %d:" % lv, ", ".join("%s(%s)" % (v, t[0]) for t, v in sorted(row)))


if __name__ == "__main__":
    main(*sys.argv[1:4])
