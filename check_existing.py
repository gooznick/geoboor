import json

with open('data/game_data.json', encoding='utf-8') as f:
    game_data = json.load(f)

existing_names = set(v['name'] for v in game_data.values())

targets = ["אריאל", "מעלה אדומים", "ביתר עילית", "מודיעין עילית", "שערי תקוה", "עץ אפרים", "מעלה עירון", "רהט", "טייבה", "אום אל-פחם", "כפר קאסם", "קלנסווה", "סח'נין", "עראבה", "שורשים", "מצפה רמון", "קצרין"]
for t in targets:
    if t in existing_names:
        print(f"EXISTS: {t}")
    else:
        print(f"MISSING: {t}")
