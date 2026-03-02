import json

with open('data/game_data.json', 'r', encoding='utf-8') as f:
    data = json.loads(f.read())

special_map = {
    # The 4 hearts (50 pts)
    "שדה יעקב": {"msg": "❤️", "points": 50},
    "קדומים": {"msg": "❤️", "points": 50},
    "כרמיאל": {"msg": "❤️", "points": 50},
    "פדיה": {"msg": "❤️", "points": 50},
    
    # Classics (50-70 pts)
    "ירושלים": {"msg": "של זהב", "points": 70},
    "דגניה א'": {"msg": "אם הקבוצות", "points": 50},
    "זכרון יעקב": {"msg": "מושבת הברון", "points": 50},
    "צפת": {"msg": "עיר המקובלים", "points": 50},
    "תל אביב - יפו": {"msg": "העיר העברית הראשונה", "points": 40},
    "חיפה": {"msg": "בירת הצפון", "points": 50},
    "מטולה": {"msg": "המושבה הצפונית ביותר", "points": 50},
    "אילת": {"msg": "העיר הדרומית ביותר", "points": 50},
    "בית שאן": {"msg": "בירת עמק המעיינות", "points": 40},
}

# 1. חומה ומגדל (Tower and Stockade) -> 40 pts
homa_umigdal = [
    "ניר דוד (תל עמל)", "ניר דוד", "חניתה", "טירת צבי", "שאר ישוב", "דן",
    "דפנה", "מחניים", "עין גב", "שער הגולן", "מעוז חיים", "מסדה", 
    "בית יוסף", "בני יהודה", "כפר רופין", "נווה איתן", "אילון", 
    "חורשים", "אשדות יעקב", "תל עמל", "עברון", "גשר", "חפציבה",
    "כפר המכבי", "משמר זבולון", "יזרעאל", "תל יצחק", "מולדת"
]

# 2. 11 הנקודות בנגב (11 Points in the Negev) -> 40 pts
negev_11 = [
    "חצרים", "נבטים", "נירים", "משמר הנגב", "אורים", "בארי", 
    "גל און", "שובל", "תקומה", "כפר דרום", "קדמה"
]

# 3. עוטף עזה (Gaza envelope) -> 40 pts (User requested 40 pts now)
gaza_env = [
    "כיסופים", "ניר עוז", "זיקים", "יד מרדכי", "כפר עזה", 
    "בארי", "נחל עוז", "חולית", "כרם שלום", "מגן", 
    "ניר יצחק", "סופה", "עין השלושה", "רעים", "סעד", 
    "עלומים", "ניר עם", "ארז", "מפלסים", "כפר מימון",
    "שדרות", "נתיב העשרה", "פרי גן", "תלמי יוסף", "יבול",
    "יתד", "שלומית", "נווה", "בני נצרים", "אוהד", "גבולות", "כרמיה"
]

# 4. גבול הצפון (Northern Border) -> 30 pts
northern_border = [
    "שלומי", "ראש הנקרה", "חניתה", "אדמית", "יערה", "ערב אל עראמשה",
    "זרעית", "שתולה", "נטועה", "אבן מנחם", "מרגליות", "משגב עם",
    "מנרה", "יפתח", "מלכיה", "יראון", "אביבים", "ברעם", "סאסא",
    "צבעון", "מתת", "פסוטה", "דוב\"ב", "חורפיש", "אלקוש"
]

# 5. הנגב (The Negev) -> 30 pts
the_negev = [
    "מצפה רמון", "ירוחם", "דימונה", "ערד", "שדה בוקר", 
    "רביבים", "משאבי שדה", "צאלים", "רתמים", "טללים", "אשלים",
    "כמהין", "שבטה", "ניצנה", "עזוז", "קדש ברנע"
]

# 6. רמת הגולן -> 20 pts
golan_env = [
    "אבני איתן", "אודם", "אורטל", "אל רום", "אלוני הבשן", "אלי עד", "אניעם", 
    "אפיק", "בני יהודה", "גבעת יואב", "גשור", "חדנס", "חספין", "יונתן", "כנף", 
    "כפר חרוב", "מבוא חמה", "מיצר", "מעלה גמלא", "מרום גולן", "נאות גולן", "נוב", 
    "נווה אטי\"ב", "נטור", "נמרוד", "עין זיוון", "קדמת צבי", "קלע", "קשת", "רמות", 
    "רמת הנשיא טראמפ", "רמת מגשימים", "שעל"
]

# 7. יישובי הבקעה -> 20 pts
bika_env = [
    "אבנת", "אלמוג", "ארגמן", "בית הערבה", "בית חוגלה", "בקעות", "גיתית", 
    "גלגל", "ורד יריחו", "חמדת", "חמרה", "ייט\"ב", "יפית", "מבואות יריחו", 
    "מחולה", "מכורה", "מצפה שלם", "משואה", "משכיות", "נעמ\"ה", "נערן", 
    "נתיב הגדוד", "פצאל", "קליה", "רועי", "רותם", "שדמות מחולה", "שלומציון", "תומר"
]

easter_eggs = {}

valid_names = {d['name'] for d in data.values()}

# Process groups sequentially based on priority
for name, val in special_map.items():
    if name in valid_names:
        easter_eggs[name] = val

for name in homa_umigdal:
    if name in valid_names and name not in easter_eggs:
        easter_eggs[name] = {"msg": "חומה ומגדל", "points": 40}

for name in negev_11:
    if name in valid_names and name not in easter_eggs:
        easter_eggs[name] = {"msg": "11 הנקודות בנגב", "points": 40}

for name in gaza_env:
    if name in valid_names and name not in easter_eggs:
        easter_eggs[name] = {"msg": "עוטף עזה", "points": 40}

for name in northern_border:
    if name in valid_names and name not in easter_eggs:
        easter_eggs[name] = {"msg": "יישובי הצפון", "points": 30}
        
for name in the_negev:
    if name in valid_names and name not in easter_eggs:
        easter_eggs[name] = {"msg": "הנגב", "points": 30}

for name in golan_env:
    if name in valid_names and name not in easter_eggs:
        easter_eggs[name] = {"msg": "יישובי רמת הגולן", "points": 20}

for name in bika_env:
    if name in valid_names and name not in easter_eggs:
        easter_eggs[name] = {"msg": "יישובי הבקעה", "points": 20}

print(f"Total Easter Eggs mapped: {len(easter_eggs)}")

with open('data/easter_eggs.json', 'w', encoding='utf-8') as f:
    json.dump(easter_eggs, f, ensure_ascii=False, indent=4)
