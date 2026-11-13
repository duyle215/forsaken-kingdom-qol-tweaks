# Forsaken Kingdom Quality-of-Life Tweaks

A single-player data mod for the **Forsaken Kingdom** campaign in **Warcraft III Reforged**. It is for casual players who play for the story and for collecting gear.

- **Better loot:** random drops are Rare, Epic or Legendary only. Rewards locked behind the Silverpine Sprint race and the Forsaken Survival bosses can also drop from monsters.
- **Faster heroes:** +20% movement speed for Garek, Anya, Leonid, Landen and Ilastar.

Built for game version **3.0.1.24371**. Download it from [Releases](../../releases/latest).

## Downloads

| File | What it changes |
|---|---|
| [`itemdata.slk`](../../releases/latest/download/itemdata.slk) | Item drops |
| [`unitbalance.slk`](../../releases/latest/download/unitbalance.slk) | Hero movement speed |
| [`enable-local-files.reg`](../../releases/latest/download/enable-local-files.reg) | Turns on "Allow Local Files" so the game reads the two files |

Use one or both `.slk` files. Each one works on its own.

## Install (Windows)

1. Run `enable-local-files.reg` and accept. It sets the DWORD `Allow Local Files` = 1 under `HKEY_CURRENT_USER\Software\Blizzard Entertainment\Warcraft III`.
2. Put the `.slk` file(s) in `<Warcraft III folder>\_retail_\units\`. Create the `units` folder if it does not exist. Example: `C:\Program Files (x86)\Warcraft III\_retail_\units\itemdata.slk`.
3. Restart the game. Existing saves work.

**Uninstall:** delete the `.slk` file(s) from `_retail_\units\`.

> **Remove the mod after every game update.** The files are full copies of the game's data tables. After a patch, the old copies would override the new data and can break items or stats. Wait for a rebuilt release, or rebuild it yourself (see below).

Single-player only. Remove it before playing online.

## What it changes

### Loot (`itemdata.slk`)

- Common and Uncommon items no longer drop at random.
- **Drop frequency is unchanged**, about 4% per kill. Only the quality changes.
- Farm camp leaders, which always drop an item, now always drop a Rare, Epic or Legendary.
- These rewards can also drop at random:
  - Master Engineering Goggles (Epic), from 1st place in Silverpine Sprint
  - Greater Engineering Goggles (Rare), from 2nd-3rd place
  - Gift of Pride (Epic), Gift of Wrath and Gift of Sloth (Rare), from the Forsaken Survival bosses
- The item table is shared data, so the Forsaken Kingdom human campaign is affected too.

### Speed (`unitbalance.slk`)

| Hero | Before | After |
|---|---|---|
| Garek (all forms), Anya, Leonid | 300 | 360 |
| Landen, Ilastar (Act 1) | 270 | 324 |

Some map scripts set a speed directly, for example when Anya joins the party. The mod cannot change that.

## What it cannot do

The campaign maps (`.w3xd`) are encrypted and signed. The game refuses a repacked map, and it ignores a modified `war3map.luac` placed in the local files folder. So nothing inside the maps can be changed: the drop rate formula, Silverpine Sprint AI and car health, Forsaken Survival perks and starting HP. Only global data tables that the game reads from `_retail_\` can be replaced.

## How it works

The drop code is inside each campaign map, so it cannot be edited. The game reads the item table, though, and that is enough to change *what* drops.

1. When a monster dies, the map's `RollItem` rolls the rarity tiers from Legendary down to Common. The chance depends on the monster level and adds up to about 4% per kill.
2. The winning tier picks an item level: Common 1-2, Uncommon 3-4, Rare 5-6, Epic 7, Legendary 8.
3. `ChooseRandomItemExWithFilterBJ(level, ITEM_TYPE_EQUIPMENT, EQUIPMENT_TYPE_ANY, ITEMTAG_TYPE_DROPPABLE)` picks a random equipment item whose `Level` column is that level and whose `tag` column is `Droppable`.

The rarity colour shown in game comes from the item name and tooltip, not from `Level`. So `patch_items.py` only moves items between levels:

- Droppable Common and Uncommon items go to level 9, which nothing rolls.
- Epic and Legendary items fill levels 1-5, the most frequent rolls. Rare items go to levels 6-8.
- Selected reward items get the `Droppable` tag and level 1. Farm camp leaders always drop a level 1 item.
- The six Scarlet Crusade items stay at level 7. `SkipScarletCrusadeItems` re-rolls them at the same level, so that level must also hold other items.

`patch_speed.py` multiplies the `spd` column of the hero rows in `unitbalance.slk` by 1.2.

## Rebuild after a game update

You need Python 3 and the original files from your own game. Extract them from the game's CASC storage with a tool such as [CASCExplorer](https://github.com/WoW-Tools/CASCExplorer) or CASC Viewer:

- `war3.w3mod/units/itemdata.slk`
- `war3.w3mod/units/unitbalance.slk`
- `war3.w3mod/_locales/enus.w3mod/units/itemstrings.txt`

Then run:

```
python -I scripts/patch_items.py itemdata.slk out/itemdata.slk itemstrings.txt
python -I scripts/patch_speed.py unitbalance.slk out/unitbalance.slk
```

`patch_items.py` stops if the number of droppable items per rarity is no longer 47/55/49/36/6 (Common/Uncommon/Rare/Epic/Legendary). In that case the patch changed the item table, and the `LAYOUT` table must be reviewed before you use the output.

## License

The scripts are under the MIT License. Warcraft III and Forsaken Kingdom are by Blizzard Entertainment. The released `.slk` files are modified copies of Blizzard's game data, and this project is not affiliated with Blizzard.
