import json

new_settlements = {
    "שערי תקוה": {
        "name": "שערי תקוה",
        "population": 6000,
        "establishment": "1982",
        "itm_east": 198516,
        "itm_north": 670155
    },
    "עץ אפרים": {
        "name": "עץ אפרים",
        "population": 2500,
        "establishment": "1985",
        "itm_east": 198299,
        "itm_north": 671239
    },
    "עשהאל": {
        "name": "עשהאל",
        "population": 800,
        "establishment": "2001",
        "itm_east": 158226,
        "itm_north": 582156
    },
    "לשם": {
         "name": "לשם",
         "population": 3000,
         "establishment": "2013",
         "itm_east": 204558,
         "itm_north": 662580
    },
    "מגרון": {
        "name": "מגרון",
        "population": 300,
        "establishment": "2012",
        "itm_east": 223508,
        "itm_north": 643260
    },
    "אש קודש": {
        "name": "אש קודש",
        "population": 250,
        "establishment": "2000",
        "itm_east": 234193,
        "itm_north": 661002
    },
    "קידה": {
        "name": "קידה",
        "population": 300,
        "establishment": "2003",
        "itm_east": 233777,
        "itm_north": 661445
    },
    "סוסיא": {
        "name": "סוסיא",
        "population": 1500,
        "establishment": "1983",
        "itm_east": 210156,
        "itm_north": 583595
    },
    "אביגיל": {
        "name": "אביגיל",
        "population": 300,
        "establishment": "2001",
        "itm_east": 210878,
        "itm_north": 585958
    }
}

with open('data/exceptions.json', encoding='utf-8') as f:
    exceptions = json.load(f)

for k, v in new_settlements.items():
    if k not in exceptions:
        exceptions[k] = v

with open('data/exceptions.json', 'w', encoding='utf-8') as f:
    json.dump(exceptions, f, ensure_ascii=False, indent=4)
