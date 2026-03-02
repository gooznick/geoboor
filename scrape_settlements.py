import urllib.request
import re
import json

url = "https://he.wikipedia.org/wiki/%D7%9E%D7%95%D7%A2%D7%A6%D7%94_%D7%90%D7%96%D7%95%D7%A8%D7%99%D7%AA_%D7%A9%D7%95%D7%9E%D7%A8%D7%95%D7%9F" # Shomron Regional Council
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    links = re.findall(r'<a href="/wiki/[^"]*" title="([^"]+)">', html)
    print("Found names in Shomron:")
    for l in links[:20]:
        print(l)
except Exception as e:
    print(f"Error: {e}")

