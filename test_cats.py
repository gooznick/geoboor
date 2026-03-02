import urllib.request, json, urllib.parse

def get_cat(cat_name):
    url = f"https://he.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:{urllib.parse.quote(cat_name)}&cmlimit=500&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req).read().decode('utf-8')
    data = json.loads(res)
    return [m["title"] for m in data["query"]["categorymembers"] if not m["title"].startswith("קטגוריה:")]

print("GOLAN:", get_cat("מועצה_אזורית_גולן:_יישובים"))
print("BIKA:", get_cat("מועצה_אזורית_בקעת_הירדן:_יישובים"))
