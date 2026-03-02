import json

with open('data/game_data.json', encoding='utf-8') as f:
    game_data = json.load(f)

existing_names = set(v['name'] for v in game_data.values())
existing_aliases = set(a for v in game_data.values() for a in v.get('aliases', []))

targets = ["בית אריה", "עופרים", "טנא", "עומרים", "אספר", "פני חבר", "קדר", "שערי תקוה", "תלם"]
for t in targets:
    if t in existing_names or t in existing_aliases:
        print(f"EXISTS: {t}")
    else:
        print(f"MISSING: {t}")
