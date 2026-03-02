import openpyxl

wb = openpyxl.load_workbook('data/bycode2024.xlsx', read_only=True, data_only=True)
ws = wb.active
golan = []
bika = []
for row in ws.iter_rows(min_row=2, values_only=True):
    name = row[0]
    c_name = str(row[28])
    if "גולן" in c_name:
         golan.append(name.strip())
    elif "בקעת הירדן" in c_name or "ערבות הירדן" in c_name or "מגילות" in c_name:
         bika.append(name.strip())

print("GOLAN:", golan)
print("BIKA:", bika)
