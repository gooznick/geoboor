"""
process_settlements.py
----------------------
Reads bycode2024.xlsx from CBS, applies naming exceptions,
and produces data/game_data.json.

Run with:  .venv/bin/python3 data/process_settlements.py
"""
import openpyxl, json, os, re
import numpy as np

HERE     = os.path.dirname(__file__)
XLSX     = os.path.join(HERE, "bycode2024.xlsx")
EXC_FILE = os.path.join(HERE, "exceptions.json")
CAL_FILE = os.path.join(HERE, "israel.png.csv")
OUT_FILE = os.path.join(HERE, "game_data.json")

# ---------------------------------------------------------------------------
# Column indices (0-based) in the xlsx
# ---------------------------------------------------------------------------
COL_NAME      = 0
COL_TOTAL_POP = 12
COL_JEWS      = 14
COL_YEAR      = 17
COL_COORDS    = 20




def parse_coords(coord_str):
    """ITM: 12-char string → (east_6_digits, north_6_digits)."""
    s = str(coord_str or "").replace(" ", "")
    return (int(s[:6]), int(s[6:])) if len(s) == 12 and s.isdigit() else (None, None)


def clean_name(raw, exceptions):
    """
    Apply naming rules to produce display_name.
    Priority: explicit exceptions > general rules.
    """
    raw = raw.strip()

    # 1. Explicit exception
    if raw in exceptions:
        return exceptions[raw]["name"]

    name = raw

    # 2. Handle parentheses
    if "(" in name:
        print(f"ommitting () for the settlements {raw[::-1]}")
        name = re.sub(r'\s*\([^)]*\)\s*', ' ', name).strip()

    # 3. Handle hyphen
    if "-" in name:
        print(f"omitting - for the settlements {raw[::-1]}")
        name = name.split("-")[0].strip()

    # 4. Remove quotes
    name = name.replace('"', '').replace("'", "").strip()
    
    # Clean up any weird double spaces
    name = re.sub(r'\s+', ' ', name)

    return name


# ---------------------------------------------------------------------------
# Coordinate conversion (affine)
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
        key = cal_name
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
    rows = list(wb.active.iter_rows(values_only=True))[1:]
    wb.close()

    settlements = {}
    key_to_itm = {}
    skipped_pop = skipped_jew = 0
    added_from_excel = set()

    for row in rows:
        raw_name = row[COL_NAME]
        if not raw_name: continue
        
        raw_name_str = str(raw_name).strip()
        added_from_excel.add(raw_name_str)
        is_exception = raw_name_str in exceptions

        population, jews = row[COL_TOTAL_POP], row[COL_JEWS]
        if not is_exception:
            if not population:
                skipped_pop += 1
                continue
            if (jews or 0) / population <= 0.20:
                skipped_jew += 1
                continue

        east, north = parse_coords(row[COL_COORDS])
        alias_names = exceptions[raw_name_str].get("aliases", []) if is_exception else []
        outposts = exceptions[raw_name_str].get("outposts", []) if is_exception else []

        entry = {
            "name":          clean_name(raw_name_str, exceptions),
            "population":    str(population or "").strip(),
            "establishment": str(row[COL_YEAR] or "").strip(),
            "aliases":       alias_names,
            "outposts":      outposts,
            "itm_east":      east,
            "itm_north":     north,
            "x": 0, "y": 0,
        }

        # Override with explicit exception data
        if is_exception:
            exc = exceptions[raw_name_str]
            for prop in ["population", "establishment", "itm_east", "itm_north"]:
                if prop in exc: entry[prop] = exc[prop]
            east, north = entry.get("itm_east"), entry.get("itm_north")

        # Merge aliases if we've seen this raw name before
        if raw_name_str in settlements:
            for a in alias_names:
                if a not in settlements[raw_name_str]["aliases"]:
                    settlements[raw_name_str]["aliases"].append(a)
        else:
            settlements[raw_name_str] = entry

        if east and north:
            key_to_itm[raw_name_str] = (east, north)

    # Inject missing synthetic exceptions
    for exc_key, exc in exceptions.items():
        if exc_key not in added_from_excel and "itm_east" in exc and "itm_north" in exc:
            east, north = int(exc["itm_east"]), int(exc["itm_north"])
            settlements[exc_key] = {
                "name":          exc["name"],
                "population":    str(exc.get("population", "1000")),
                "establishment": str(exc.get("establishment", "")),
                "aliases":       exc.get("aliases", []),
                "outposts":      exc.get("outposts", []),
                "itm_east":      east,
                "itm_north":     north,
                "x": 0, "y": 0,
            }
            key_to_itm[exc_key] = (east, north)

    print(f"  Settlements (>20% Jewish): {len(settlements)}")
    print(f"  Skipped (no pop data):     {skipped_pop}")
    print(f"  Skipped (≤20% Jewish):     {skipped_jew}")

    print("Computing coordinates…")
    try:
        transform = load_calibration(CAL_FILE, key_to_itm)
        for key, entry in settlements.items():
            if key in key_to_itm:
                entry["x"], entry["y"] = transform(entry["itm_east"], entry["itm_north"])
    except Exception as e:
        print(f"  WARNING: coordinate conversion failed: {e}")
        print("  x,y will be 0,0 for all entries")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(settlements, f, ensure_ascii=False, indent=4)
    print(f"Wrote {OUT_FILE}  ({len(settlements)} entries)")


if __name__ == "__main__":
    main()
