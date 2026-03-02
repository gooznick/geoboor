import urllib.request
import urllib.parse
import json

query = """
SELECT ?item ?itemLabel ?coord
WHERE {
  ?item wdt:P31 wd:Q1334237.
  OPTIONAL { ?item wdt:P625 ?coord. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "he,en". }
}
"""

url = "https://query.wikidata.org/sparql?query=" + urllib.parse.quote(query) + "&format=json"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 Geoboor/1.0'})
try:
    response = urllib.request.urlopen(req).read()
    data = json.loads(response)
    names = []
    for binding in data['results']['bindings']:
        label = binding.get('itemLabel', {}).get('value', '')
        if label and any("\u0590" <= c <= "\u05ea" for c in label):
            names.append(label)
    print(f"Found {len(names)} total from Wikidata.")
    
    with open('data/game_data.json', encoding='utf-8') as f:
        game_data = json.load(f)
    existing_names = set(v['name'] for v in game_data.values())
    existing_aliases = set(a for v in game_data.values() for a in v.get('aliases', []))
    
    missing = []
    for name in names:
        n = name.strip()
        if n not in existing_names and n not in existing_aliases and " " in n and "מאחז" not in n:
            missing.append(n)
            
    print("Some missing from Wikidata (likely outliers/outposts):")
    for m in sorted(list(set(missing)))[:40]:
        print(m)
        
except Exception as e:
    print(f"Error: {e}")
