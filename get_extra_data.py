import urllib.request
import re
import json

urls = {
    "היישוב היהודי בחברון": "https://he.wikipedia.org/wiki/%D7%94%D7%99%D7%99%D7%A9%D7%95%D7%91_%D7%94%D7%99%D7%94%D7%95%D7%93%D7%99_%D7%91%D7%97%D7%91%D7%A8%D7%95%D7%9F",
    "אביתר": "https://he.wikipedia.org/wiki/%D7%90%D7%91%D7%99%D7%AA%D7%A8_(%D7%9E%D7%90%D7%97%D7%96)"
}

results = {}
for name, url in urls.items():
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
        itm = re.search(r'(\d{6})\s*/\s*(\d{6})', html)
        pop = re.search(r'אוכלוסייה.*?(\d+,\d+|\d+)', html, re.DOTALL)
        est = re.search(r'הוקם ב.*?(1\d{3}|20\d{2})', html)
        if itm:
            results[name] = {
                "itm_east": int(itm.group(1)),
                "itm_north": int(itm.group(2)),
                "population": int(pop.group(1).replace(',', '')) if pop else 1000,
                "establishment": est.group(1) if est else ""
            }
        else:
             results[name] = "NO ITM"
    except Exception as e:
        results[name] = f"Error: {e}"

# Get categories
def get_category_members(cat_name):
    url = f"https://he.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:{urllib.parse.quote(cat_name)}&cmlimit=500&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req).read().decode('utf-8')
    data = json.loads(res)
    return [m["title"] for m in data["query"]["categorymembers"] if not m["title"].startswith("קטגוריה:")]

import urllib.parse
try:
    bik = get_category_members("בקעת_הירדן:_יישובים")
    golan = get_category_members("רמת_הגולן:_יישובים")
    results["bik"] = bik
    results["golan"] = golan
except Exception as e:
    results["cat_error"] = str(e)

print(json.dumps(results, ensure_ascii=False, indent=2))
