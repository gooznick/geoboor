import urllib.request
import re
import json

targets = [
    "שערי תקווה", "עץ אפרים", "לשם", "סוסיא", "אביגיל", "אש קודש", 
    "חוות יאיר", "חרשה", "מגרון", "מיצד", "מעלה רחבעם", "מצפה דני", 
    "מצפה כרמים", "נופי פרת", "עדי עד", "עשהאל", "קידה", "שדה בר"
]

results = {}
for name in targets:
    url = "https://he.wikipedia.org/wiki/" + urllib.parse.quote(name)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 Geoboor/1.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
        
        # Look for ITM coordinates, usually around "רשת ישראל החדשה" or similar
        itm_matches = re.findall(r'(\d{6})\s*/\s*(\d{6})', html)
        itm = None
        for match in itm_matches:
            east = int(match[0])
            north = int(match[1])
            # Valid ITM Easting is usually 100000 - 300000
            # Valid ITM Northing is usually 300000 - 800000
            if 100000 <= east <= 300000 and 300000 <= north <= 800000:
                itm = (east, north)
                break
                
        pop = re.search(r'אוכלוסייה.*?(\d+,\d+|\d+)', html, re.DOTALL)
        pop_val = 1000
        if pop: 
            pstr = pop.group(1).replace(',', '')
            if pstr.isdigit():
                pop_val = int(pstr)
                
        est = re.search(r'הוקם ב.*?(\d{4})', html)
        if itm:
            results[name.replace("תקווה", "תקוה")] = {
                "name": name.replace("תקווה", "תקוה"),
                "itm_east": itm[0],
                "itm_north": itm[1],
                "population": pop_val,
                "establishment": est.group(1) if est else ""
            }
            print(f"Got {name}: {itm[0]}/{itm[1]} Pop: {pop_val}")
        else:
            print(f"Missing coords for {name}")
    except Exception as e:
        print(f"Error on {name}: {e}")

with open('data/exceptions.json', encoding='utf-8') as f:
    exceptions = json.load(f)

for k, v in results.items():
    if k not in exceptions:
        exceptions[k] = v

with open('data/exceptions.json', 'w', encoding='utf-8') as f:
    json.dump(exceptions, f, ensure_ascii=False, indent=4)
