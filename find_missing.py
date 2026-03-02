import urllib.request
import re
import openpyxl

url = "https://he.wikipedia.org/wiki/%D7%94%D7%94%D7%AA%D7%A0%D7%97%D7%9C%D7%95%D7%99%D7%95%D7%AA" # wiki page for Israeli settlements
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
except Exception as e:
    print(f"Failed to fetch wiki: {e}")
    html = ""

# try to parse some settlement names from tables or lists
# We'll just extract all Hebrew words that look like links
links = re.findall(r'<a href="/wiki/[^"]*" title="([^"]+)">', html)
names = set()
for link in links:
    link = link.split(' (')[0] # remove parens
    if any("\u0590" <= c <= "\u05ea" for c in link):
        names.add(link)

wb = openpyxl.load_workbook("data/bycode2024.xlsx", read_only=True, data_only=True)
ws = wb.active
excel_names = set()
for row in ws.iter_rows(values_only=True):
    name = row[0]
    if name and isinstance(name, str):
        excel_names.add(name.strip().split(' (')[0].strip())
        
missing = names - excel_names
print("Some possibly missing settlements:")
for m in sorted(list(missing)):
    if len(m) > 3 and " " in m:
        print(m)
