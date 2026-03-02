"""
process_settlements.py
----------------------
Reads bycode2024.xlsx from CBS, applies naming exceptions,
and produces data/game_data.json (same format as boor/data.json
but updated for 2024, with an extra "aliases" field).

Run with:  .venv/bin/python3 data/process_settlements.py
"""
import openpyxl, json, os, re
import numpy as np

HERE     = os.path.dirname(__file__)
XLSX     = os.path.join(HERE, "bycode2024.xlsx")
EXC_FILE = os.path.join(HERE, "exceptions.json")
CAL_FILE = os.path.join(HERE, "israel.png.csv")
OUT_FILE = os.path.join(HERE, "game_data.json")
LOG_FILE = os.path.join(HERE, "data.md")

# ---------------------------------------------------------------------------
# Column indices (0-based) in the xlsx
# ---------------------------------------------------------------------------
COL_NAME      = 0
COL_TOTAL_POP = 12
COL_JEWS      = 14
COL_YEAR      = 17
COL_COORDS    = 20

# ---------------------------------------------------------------------------
# Parenthetical content that should just be deleted (not become an alias)
# ---------------------------------------------------------------------------
DELETE_PARENS = {
    "מושב", "מושבה", "קיבוץ", "קבוצה",
    "ישיבה", "קהילת חינוך", "מוסד", "כפר נוער", "כפר עבודה",
}

SOFIT_MAP = str.maketrans("םןץףך", "מנצפכ")


def remove_sofit(s):
    return s.translate(SOFIT_MAP)


def to_game_key(name):
    """Convert a display name to the game key (reversed, only Hebrew letters)."""
    name = name.strip()
    name = remove_sofit(name)
    name = ''.join(ch for ch in name if ch.isalpha() and '\u05d0' <= ch <= '\u05ea')
    return name[::-1]


def parse_coords(coord_str):
    """ITM: 12-char string → (east_6_digits, north_6_digits)."""
    if not coord_str:
        return None, None
    s = str(coord_str).strip().replace(" ", "")
    if len(s) == 12:
        try:
            return int(s[:6]), int(s[6:])
        except ValueError:
            pass
    return None, None


def clean_name(raw, exceptions):
    """
    Apply naming rules to produce (display_name, [alias_display_names]).
    Priority: explicit exceptions > general rules.
    """
    raw = raw.strip()

    # 1. Explicit exception
    if raw in exceptions:
        e = exceptions[raw]
        return e["name"], e.get("aliases", [])

    # 2. Strip trailing geresh (') after a Hebrew letter, e.g. "דגניה א'"
    name = re.sub(r"'\s*$", "", raw).strip()

    # 3. Handle parentheses
    paren_match = re.search(r'\(([^)]+)\)', name)
    if paren_match:
        content = paren_match.group(1).strip()
        base    = re.sub(r'\s*\([^)]+\)\s*', ' ', name).strip()
        if content in DELETE_PARENS:
            return base, []
        else:
            # content becomes an alias: e.g. "גבעת חיים (איחוד)" → alias "גבעת חיים איחוד"
            alias = base + " " + content
            return base, [alias]

    # 4. Handle hyphen: second part is alias  (handles "אל -רום" spacing too)
    if "-" in name:
        parts = [p.strip() for p in name.split("-", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            return parts[0], [parts[1]]

    return name, []


# ---------------------------------------------------------------------------
# Coordinate conversion (affine, same approach as original prepare.py)
# ---------------------------------------------------------------------------
def load_calibration(cal_file, settlements_itm):
    """
    Read 3 calibration points (name → pixel x,y) and look up their ITM
    coordinates from the processed settlements dict.
    Returns an affine transform function (itm → pixel).
    """
    cal_points = []
    with open(cal_file, encoding="utf-8") as f:
        f.read(1)  # BOM
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 3:
                continue
            cal_name = parts[0].strip()
            px, py = int(parts[1]), int(parts[2])
            cal_points.append((cal_name, px, py))

    if len(cal_points) < 3:
        raise ValueError("Need at least 3 calibration points")

    # Find ITM for each calibration settlement
    itm_pts, pix_pts = [], []
    for cal_name, px, py in cal_points:
        key = to_game_key(cal_name)
        if key not in settlements_itm:
            raise ValueError(f"Calibration settlement '{cal_name}' (key '{key}') not found in data")
        itm_pts.append(settlements_itm[key])
        pix_pts.append((px, py))
        print(f"  Calibration: {cal_name} → ITM {settlements_itm[key]} → pixel ({px},{py})")

    # Solve affine transform
    (e1,n1),(e2,n2),(e3,n3) = itm_pts
    (x1,y1),(x2,y2),(x3,y3) = pix_pts
    X = np.array([[e1,n1,1],[e2,n2,1],[e3,n3,1]], dtype=float)
    Yx = np.array([x1,x2,x3], dtype=float)
    Yy = np.array([y1,y2,y3], dtype=float)
    ax = np.linalg.solve(X, Yx)
    ay = np.linalg.solve(X, Yy)

    def transform(east, north):
        px = ax[0]*east + ax[1]*north + ax[2]
        py = ay[0]*east + ay[1]*north + ay[2]
        return int(round(px)), int(round(py))

    return transform


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Load exceptions
    with open(EXC_FILE, encoding="utf-8") as f:
        exceptions = {k: v for k, v in json.load(f).items() if not k.startswith("_")}

    print(f"Loaded {len(exceptions)} explicit exceptions")

    # Read xlsx
    print("Reading xlsx…")
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb.active

    raw_rows = []
    first = True
    for row in ws.iter_rows(values_only=True):
        if first:
            first = False
            continue
        name      = row[COL_NAME]
        total_pop = row[COL_TOTAL_POP]
        jews      = row[COL_JEWS]
        year      = row[COL_YEAR]
        coords    = row[COL_COORDS]
        if not name:
            continue
        raw_rows.append((name, total_pop, jews, year, coords))

    wb.close()
    print(f"  {len(raw_rows)} rows read")

    # Build settlements dict: game_key → data
    # Phase 1: collect data per game_key (merge duplicates)
    settlements = {}   # key → dict
    key_to_itm  = {}   # key → (east, north)
    skipped_pop = 0
    skipped_jew = 0

    for raw_name, total_pop, jews, year, coords in raw_rows:
        raw_name_str = str(raw_name).strip()
        is_exception = raw_name_str in exceptions

        # Filter
        if not is_exception:
            if not total_pop or total_pop == 0:
                skipped_pop += 1
                continue
            pct = (jews or 0) / total_pop
            if pct <= 0.20:
                skipped_jew += 1
                continue

        display_name, alias_names = clean_name(str(raw_name), exceptions)

        east, north = parse_coords(coords)
        year_str = ""
        if year:
            y = str(year).strip()
            year_str = y if y.lstrip('-').isdigit() else y

        pop_str = str(int(total_pop)) if total_pop else ""

        # Main entry
        key = to_game_key(display_name)
        alias_keys = [to_game_key(a) for a in alias_names if a.strip()]

        entry = {
            "name":          display_name,
            "population":    pop_str,
            "establishment": year_str,
            "aliases":       alias_names,
            "itm_east":      east,
            "itm_north":     north,
            "x": 0,
            "y": 0,
        }

        # Override missing/empty fields if it's an exception with hardcoded values
        if is_exception:
            exc = exceptions[raw_name_str]
            if "population" in exc: entry["population"] = str(exc["population"])
            if "establishment" in exc: entry["establishment"] = str(exc["establishment"])
            if "itm_east" in exc: entry["itm_east"] = int(exc["itm_east"])
            if "itm_north" in exc: entry["itm_north"] = int(exc["itm_north"])
            # Update local variables for key_to_itm collection later
            if "itm_east" in exc and "itm_north" in exc:
                east, north = int(exc["itm_east"]), int(exc["itm_north"])

        if key not in settlements:
            settlements[key] = entry
        else:
            # Merge aliases if same key appears again (e.g. two דגניה entries)
            existing = settlements[key]
            for a in alias_names:
                if a not in existing["aliases"]:
                    existing["aliases"].append(a)

        if east and north:
            key_to_itm[key] = (east, north)

    # Phase 1.5: inject purely synthetic entries from exceptions that were not in raw_rows
    added_from_excel = set(str(r[0]).strip() for r in raw_rows if r[0])
    for exc_key, exc in exceptions.items():
        if exc_key not in added_from_excel:
            # Only add if it provides at least population and coordinates
            if "itm_east" in exc and "itm_north" in exc:
                display_name = exc["name"]
                key = to_game_key(display_name)
                alias_names = exc.get("aliases", [])
                east, north = int(exc["itm_east"]), int(exc["itm_north"])
                entry = {
                    "name":          display_name,
                    "population":    str(exc.get("population", "1000")),
                    "establishment": str(exc.get("establishment", "")),
                    "aliases":       alias_names,
                    "itm_east":      east,
                    "itm_north":     north,
                    "x": 0,
                    "y": 0,
                }
                settlements[key] = entry
                key_to_itm[key] = (east, north)

    print(f"  Settlements (>20% Jewish): {len(settlements)}")
    print(f"  Skipped (no pop data):     {skipped_pop}")
    print(f"  Skipped (≤20% Jewish):     {skipped_jew}")

    # Phase 2: coordinate conversion
    print("Computing coordinates…")
    try:
        transform = load_calibration(CAL_FILE, key_to_itm)
        for key, entry in settlements.items():
            if key in key_to_itm:
                east, north = key_to_itm[key]
                entry["itm_east"]  = east
                entry["itm_north"] = north
                entry["x"], entry["y"] = transform(east, north)
    except Exception as e:
        print(f"  WARNING: coordinate conversion failed: {e}")
        print("  x,y will be 0,0 for all entries")

    # Phase 3: write output JSON (same structure as boor/data.json)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(settlements, f, ensure_ascii=False, indent=4)
    print(f"Wrote {OUT_FILE}  ({len(settlements)} entries)")

    # Phase 4: update data.md log
    _write_log(settlements, skipped_pop, skipped_jew, exceptions)
    print(f"Updated {LOG_FILE}")


def _write_log(settlements, skipped_pop, skipped_jew, exceptions):
    with_aliases = sum(1 for v in settlements.values() if v["aliases"])
    lines = [
        "# Settlement Data Processing Log",
        "",
        "## Source",
        "- File: `bycode2024.xlsx` — [CBS 2024](https://www.cbs.gov.il/he/publications/DocLib/2019/ishuvim/bycode2024.xlsx)",
        "",
        "## Filter",
        "- **(יהודים ואחרים / סך הכל אוכלוסייה) > 20%**",
        "",
        "## Naming Rules",
        "1. Explicit overrides loaded from `exceptions.json`",
        "2. Parenthetical content in DELETE list → stripped: " +
            ", ".join(f"`{w}`" for w in sorted(["מושב","מושבה","קיבוץ","קבוצה","ישיבה","קהילת חינוך","מוסד","כפר נוער"])),
        "3. Other parenthetical content → becomes an alias",
        "4. Hyphenated name → first part is primary, second part is alias",
        "5. Trailing geresh `'` → stripped",
        "",
        "## Results",
        f"| | Count |",
        f"|---|---|",
        f"| Qualifying settlements | **{len(settlements)}** |",
        f"| With aliases | {with_aliases} |",
        f"| Skipped (no pop data) | {skipped_pop} |",
        f"| Skipped (≤20% Jewish) | {skipped_jew} |",
        "",
        "## Explicit Exceptions",
        "",
        "| Raw name (xlsx) | Game name | Aliases |",
        "|-----------------|-----------|---------|",
    ]
    for raw, exc in sorted(exceptions.items()):
        aliases = ", ".join(exc.get("aliases", [])) or "—"
        lines.append(f"| {raw} | {exc['name']} | {aliases} |")

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
