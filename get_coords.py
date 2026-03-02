import urllib.request
import re
import json

urls = {
    "שערי תקוה": "https://he.wikipedia.org/wiki/%D7%A9%D7%A2%D7%A8%D7%99_%D7%AA%D7%A7%D7%95%D7%95%D7%94",
    "עץ אפרים": "https://he.wikipedia.org/wiki/%D7%A2%D7%A5_%D7%90%D7%A4%D7%A8%D7%99%D7%9D"
}

results = {}
for name, url in urls.items():
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
        # try to find ITM coordinates. In hebrew wiki, there is usually `data-mw="interface">198516/670155<` or similar
        itm = re.search(r'(\d{6})\s*/\s*(\d{6})', html)
        pop = re.search(r'אוכלוסייה.*?(\d+,\d+|\d+)', html, re.DOTALL)
        est = re.search(r'הוקם ב.*?(\d{4})', html)
        if itm:
            results[name] = {
                "itm_east": int(itm.group(1)),
                "itm_north": int(itm.group(2)),
                "population": int(pop.group(1).replace(',', '')) if pop else 1000,
                "establishment": est.group(1) if est else ""
            }
    except Exception as e:
        print(f"Error on {name}: {e}")

print(json.dumps(results, ensure_ascii=False, indent=2))
