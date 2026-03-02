import urllib.request
import json
import re

url = "https://he.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:%D7%94%D7%AA%D7%A0%D7%97%D7%9C%D7%95%D7%99%D7%95%D7%AA_%D7%91%D7%99%D7%94%D7%95%D7%93%D7%94_%D7%95%D7%A9%D7%95%D7%9E%D7%A8%D7%95%D7%9F&cmlimit=500&format=json"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 Geoboor/1.0'})
try:
    response = urllib.request.urlopen(req).read().decode('utf-8')
    data = json.loads(response)
    names = [member['title'] for member in data['query']['categorymembers'] if member['ns'] == 0]
    
    with open('data/game_data.json', encoding='utf-8') as f:
        game_data = json.load(f)
    existing_names = set(v['name'] for v in game_data.values())
    existing_aliases = set(a for v in game_data.values() for a in v.get('aliases', []))
    
    missing = []
    for name in names:
        # Clean wikipedia extra parens
        clean_name = re.sub(r'\s*\(.*?\)', '', name).strip()
        if clean_name not in existing_names and clean_name not in existing_aliases:
            if "יהודה ושומרון" not in clean_name and "מועצה" not in clean_name and "גוש" not in clean_name:
                missing.append(clean_name)
            
    print("Missing settlements from Wikipedia 'Settlements in Judea and Samaria':")
    for m in sorted(list(set(missing))):
        print(m)
        
except Exception as e:
    print(f"Error: {e}")
