import json
with open('data/game_data.json', encoding='utf-8') as f:
    game_data = json.load(f)
exists = any("סוסיא" in v["name"] for v in game_data.values())
print("סוסיא EXISTS:", exists)
exists = any("לשם" in v["name"] for v in game_data.values())
print("לשם EXISTS:", exists)
