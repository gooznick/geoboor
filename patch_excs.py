import json

with open('data/exceptions.json', encoding='utf-8') as f:
    excs = json.load(f)

if "ענב" not in excs:
    excs["ענב"] = {"name": "ענב", "aliases": ["עינב"]}
else:
    if "עינב" not in excs["ענב"].get("aliases", []):
        excs["ענב"].setdefault("aliases", []).append("עינב")

excs["חברון"] = {
    "name": "חברון",
    "population": 1000,
    "establishment": "1929",
    "itm_east": 160350,
    "itm_north": 104500,
    "aliases": ["יישוב היהודי בחברון"]
}

excs["אביתר"] = {
    "name": "אביתר",
    "population": 53,
    "establishment": "2021",
    "itm_east": 174063,
    "itm_north": 169715,
    "aliases": []
}

if "טירת כרמל" not in excs:
    excs["טירת כרמל"] = {"name": "טירת כרמל", "aliases": ["טירת הכרמל"]}
else:
    if "טירת הכרמל" not in excs["טירת כרמל"].get("aliases", []):
        excs["טירת כרמל"].setdefault("aliases", []).append("טירת הכרמל")


with open('data/exceptions.json', 'w', encoding='utf-8') as f:
    json.dump(excs, f, ensure_ascii=False, indent=4)
