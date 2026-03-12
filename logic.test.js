const { chooseAll, stripAndReverse, isHebrewLetter, nameVariants, getVariants, buildDictionaries, readGameData, checkSequence, checkEasterEggs } = require('./logic.js');

describe('מַפָּאוֹת Game Logic', () => {

    test('isHebrewLetter checks', () => {
        expect(isHebrewLetter('א')).toBe(true);
        expect(isHebrewLetter('ם')).toBe(false); // Sofit letters are not in HEBREW_LETTERS set, handled by removeSofit before check
        expect(isHebrewLetter('a')).toBe(false);
        expect(isHebrewLetter('1')).toBe(false);
    });

    test('stripAndReverse normalization', () => {
        // Reversed correctly with English and spaces stripped, sofit changed
        expect(stripAndReverse('תל אביב')).toBe('ביבאלת');
        expect(stripAndReverse('ראשון לציון')).toBe('נויצלנושאר'); // ן becomes נ
        expect(stripAndReverse('מודיעין-מכבים-רעות')).toBe('תוערמיבכמניעידומ');
        expect(stripAndReverse("מצפה לאה")).toBe("האלהפצמ");
        expect(stripAndReverse("מצפהלאה")).toBe("האלהפצמ");
        expect(stripAndReverse("םצפהלאה")).toBe("האלהפצמ");
        expect(stripAndReverse("םץףה לאה")).toBe("האלהפצמ");

    });

    // Shared mock dataset and structures for game state
    let rawData;
    let keyVariantMap;
    let allVariantKeys;
    let baseVariantKeys;
    let outpostKeys;
    let forbidCanon;

    beforeEach(() => {
        rawData = {
            "תל אביב -יפו": {
                "name": "תל אביב",
                "aliases": ["יפו"]
            },
            "אילת": {
                "name": "אילת",
                "aliases": []
            },
            "רביבים": {
                "name": "רביבים",
                "aliases": []
            },
            "גוויאדה": { // Settlement with double vav
                "name": "גוויאדה",
                "aliases": []
            },
            "קרני שומרון": {
                "name": "קרני שומרון",
                "aliases": [],
                "outposts": ["מצפה צבאים"]
            }
        };

        // Simulate game init() using the shared logic function
        const dicts = buildDictionaries(rawData);
        keyVariantMap = dicts.keyVariantMap;
        allVariantKeys = dicts.allVariantKeys;
        baseVariantKeys = dicts.baseVariantKeys;
        outpostKeys = dicts.outpostKeys;
        forbidCanon = new Set();
    });

    test('chooseAll handles empty string with full dataset', () => {
        // Test chooseAll with an empty string, passing baseVariantKeys
        const options = chooseAll('', allVariantKeys, forbidCanon, keyVariantMap, [], baseVariantKeys);

        // We have 4 canon settlements, and 1 alias. So 5 base names.
        // "גוויאדה" yields variants: "גוויאדה" and "גויאדה".
        // Base names reversed (with sofit replacement):
        // תל אביב -> ביבאלת
        // יפו -> ופי
        // אילת -> תליא
        // רביבים -> מיביבר
        // גוויאדה -> הדאיווג
        // גויאדה -> הדאיוג
        // Total variants = 6.
        // Options contain 5 items now because variants are excluded from the empty string proposal.

        expect(options.length).toBe(6);
        expect(options.length).toBeGreaterThan(Object.keys(rawData).length); // More options than raw dictionary keys 

        // 2. Check examples of names and aliases
        const optionKeys = options.map(o => o.key);
        expect(optionKeys).toContain(stripAndReverse("תל אביב"));
        expect(optionKeys).toContain(stripAndReverse("אילת"));
        expect(optionKeys).toContain(stripAndReverse("יפו")); // Alias is included

        // 3. Check that וו replacements are not in the list the computer chooses
        // The new architecture uses baseKeySet to only propose exact original aliases and names!
        expect(optionKeys).toContain(stripAndReverse("גוויאדה"));
        expect(optionKeys).not.toContain(stripAndReverse("גויאדה")); // Variant correctly excluded
    });

    test('chooseAll handles full overlapping matches (e.g. רביבים)', () => {
        // When the user has fully typed "רביבים", the reversed string is "מיביבר".
        // The game should recognize "רביבים" is fully consumed, mark it in `former`, 
        // and propose the next valid components matching the leftover string (which is empty string).

        const current = stripAndReverse("רביבים"); // 'מיביבר'
        const options = chooseAll(current, allVariantKeys, forbidCanon, keyVariantMap, [], baseVariantKeys);

        // Options should now propose all OTHER settlements (since the leftover is empty, 
        // it can transition into any base settlement that isn't רביבים).

        // Explicitly check the exact options returned
        expect(options).toHaveLength(5);

        expect(options).toEqual(expect.arrayContaining([
            { letter: 'ת', key: stripAndReverse("תל אביב"), former: [current] },
            { letter: 'א', key: stripAndReverse("אילת"), former: [current] },
            { letter: 'י', key: stripAndReverse("יפו"), former: [current] },
            { letter: 'ג', key: stripAndReverse("גוויאדה"), former: [current] },
            { letter: 'ק', key: stripAndReverse("קרני שומרון"), former: [current] },
        ]));
    });

    test('chooseAll correctly identifies legal and illegal strings', () => {
        // Helper function to check if a Hebrew string (read left-to-right by user) is legal
        // If chooseAll returns options > 0, the string is a valid prefix/path.
        const isLegal = (hebrewString) => {
            const reversed = stripAndReverse(hebrewString);
            const options = chooseAll(reversed, allVariantKeys, forbidCanon, keyVariantMap, [], baseVariantKeys);
            return options.length > 0;
        };

        // LEGAL strings:
        expect(isLegal("רביב")).toBe(true);
        expect(isLegal("רביבי")).toBe(true);
        expect(isLegal("רביבים")).toBe(true);
        expect(isLegal("רביביםת")).toBe(true); // תל אביב overlapping starting with ת
        expect(isLegal("רביביםיפ")).toBe(true); // יפו overlapping
        expect(isLegal("יפותלאביב")).toBe(true); // יפו overlapping into תל אביב
        expect(isLegal("גוויאדהתל")).toBe(true); // גוויאדה into תל אביב
        expect(isLegal("גויאדה")).toBe(true); // The variant itself is legal to type
        expect(isLegal("גויאדהיפ")).toBe(true); // Variant overlapping into יפו

        // ILLEGAL strings:
        expect(isLegal("רביביםרבי")).toBe(false); // Can't reuse רביבים
        // expect(isLegal("גוויאדהגו")).toBe(false); // TODO: Can't reuse גוויאדה (assuming גויאדה maps to same canon)
        expect(isLegal("ע")).toBe(false); // No settlement starts with ע
        expect(isLegal("יפע")).toBe(false); // יפו ends, no settlement starts with ע
        expect(isLegal("יפוע")).toBe(false);
        expect(isLegal("תלאביביפוס")).toBe(false); // Overlapping chain valid until ס which breaks it
    });

    test('chooseAll prefers base variations when user input matches both base and variant of same settlement', () => {
        // User typed "ג", the computer should propose "גוויאדה" (base) but NOT "גויאדה" (single vav variant).
        const current = stripAndReverse("ג");
        const options = chooseAll(current, allVariantKeys, forbidCanon, keyVariantMap, [], baseVariantKeys);

        const optionKeys = options.map(o => o.key);
        expect(optionKeys).toHaveLength(1);
        expect(optionKeys).toContain(stripAndReverse("גוויאדה"));
        expect(optionKeys).not.toContain(stripAndReverse("גויאדה"));

        // User typed "גוי" which ONLY matches the single-vav variant "גויאדה".
        // The computer MUST propose the variant because the base "גוויאדה" no longer matches.
        const currentVariant = stripAndReverse("גוי");
        const optionsVariant = chooseAll(currentVariant, allVariantKeys, forbidCanon, keyVariantMap, [], baseVariantKeys);

        const optionKeysVariant = optionsVariant.map(o => o.key);
        expect(optionKeysVariant).toHaveLength(1);
        expect(optionKeysVariant).toContain(stripAndReverse("גויאדה"));
        expect(optionKeysVariant).not.toContain(stripAndReverse("גוויאדה"));
    });

    test('checkEasterEggs correctly finds and awards points for easter eggs, handling variants properly', () => {
        const foundEggsSet = new Set();

        // Define a small easter egg DB using reversed keys (just like game.js parsed output)
        const easterEggData = {
            [stripAndReverse("רביבים")]: { msg: "Found Revivim!", points: 100 },
            [stripAndReverse("גוויאדה")]: { msg: "Found Gviada!", points: 50 },
            [stripAndReverse("אילת")]: { msg: "Eilat bonus!", points: 10 }
        };

        // 1. Exact string match ("רביבים" -> RTL "מיביבר")
        const current1 = stripAndReverse("רביבים");
        const found1 = checkEasterEggs(current1, easterEggData, keyVariantMap, foundEggsSet);

        expect(found1).toHaveLength(1);
        expect(found1[0].points).toBe(100);
        expect(found1[0].msg).toBe("Found Revivim!");
        expect(foundEggsSet.has(stripAndReverse("רביבים"))).toBe(true);

        // 2. Typing the EXACT SAME string again shouldn't trigger, because it's recorded in foundEggsSet
        const found2 = checkEasterEggs(current1, easterEggData, keyVariantMap, foundEggsSet);
        expect(found2).toHaveLength(0);

        // 3. Prefixing the same matched string to mimic game progress should NOT re-trigger
        const current2 = stripAndReverse("עיררביבים"); // 'מיביברריע'
        const found3 = checkEasterEggs(current2, easterEggData, keyVariantMap, foundEggsSet);
        expect(found3).toHaveLength(0);

        // 4. Variant matching flexibility! 
        // Our easter egg was explicitly registered for the base variant "גוויאדה" (double-vav).
        // Let's type out the single-vav generic variant "גויאדה"
        const current3 = stripAndReverse("גויאדה"); // RTL 'הדאיוג'
        const found4 = checkEasterEggs(current3, easterEggData, keyVariantMap, foundEggsSet);

        expect(found4).toHaveLength(1); // STILL triggers the egg successfully because their canonical settlements map to the same id!
        expect(found4[0].points).toBe(50);
        expect(foundEggsSet.has(stripAndReverse("גוויאדה"))).toBe(true);
    });

    test('Outposts are ignored by computer default suggestions but accepted if the user overlaps into them', () => {
        // "מצפה צבאים" -> reversed is "םיאבצ הפצמ" -> "מיאבצהפצמ"

        // 1. Ensure the computer won't suggest the outpost on an empty string
        const emptyOptions = chooseAll('', allVariantKeys, forbidCanon, keyVariantMap, [], baseVariantKeys, outpostKeys);
        const emptyOptionKeys = emptyOptions.map(o => o.key);
        expect(emptyOptionKeys).not.toContain(stripAndReverse("מצפה צבאים"));

        // 2. Ensure if the user types part of it (e.g. "מ" which is "מ" in reversed string)
        // Since "מ" could be the start of "מצפה צבאים", we want to ensure the game recognizes it as a valid path.
        // User string building RTL: if user types 'מ' it becomes 'מ'.
        const userTypesM = stripAndReverse("מ"); // just "מ"
        const optionsM = chooseAll(userTypesM, allVariantKeys, forbidCanon, keyVariantMap, [], baseVariantKeys, outpostKeys);

        // Explicit check: letter, key, and former for outposts acting as a first match
        expect(optionsM).toEqual(
            expect.arrayContaining([
                {
                    letter: 'צ',
                    key: stripAndReverse("מצפה צבאים"),
                    former: []
                }
            ])
        );

        // However, if we filter outposts like game.js does for the computer's choice:
        const compOptionsFilteredM = optionsM.filter(opt => !outpostKeys.has(opt.key));
        expect(compOptionsFilteredM.some(o => o.key === stripAndReverse("מצפה צבאים"))).toBe(false);

        // 3. User types an outpost AFTER a regular settlement:
        // Regular settlement is "תל אביב". User types "מ". Combined is "תל אביבמ".
        const userTypesOverlap = stripAndReverse("תל אביבמ");
        const optionsOverlap = chooseAll(userTypesOverlap, allVariantKeys, forbidCanon, keyVariantMap, [], baseVariantKeys, outpostKeys);

        // Explicit check: letter, key, and former showing previous settlement in chain
        expect(optionsOverlap).toEqual(
            expect.arrayContaining([
                {
                    letter: 'צ',
                    key: stripAndReverse("מצפה צבאים"),
                    former: [stripAndReverse("תל אביב")]
                }
            ])
        );

        // 4. User is FORCED into the outpost (e.g. they typed "מצפה צב")
        // User string "מצפה צב" -> "בצהפצמ"
        const userForced = stripAndReverse("מצפה צב");
        const optionsForced = chooseAll(userForced, allVariantKeys, forbidCanon, keyVariantMap, [], baseVariantKeys, outpostKeys);

        expect(optionsForced).toEqual(
            expect.arrayContaining([
                {
                    letter: 'א',
                    key: stripAndReverse("מצפה צבאים"),
                    former: []
                }
            ])
        );

        // The game loop in game.js filters outposts ONLY if non-outposts exist.
        // At "מצפה צב", the only matching base/variant in our test DB is "מצפה צבאים".
        expect(optionsForced.length).toBeGreaterThan(0);

        // We simulate the game.js extraction logic
        const nonOutpostForced = optionsForced.filter(opt => !outpostKeys.has(opt.key));
        expect(nonOutpostForced).toHaveLength(0); // No regular settlements match "מצפה צב"

        const finalCompOptions = nonOutpostForced.length > 0 ? nonOutpostForced : optionsForced;
        expect(finalCompOptions).toHaveLength(1);
        expect(finalCompOptions[0].key).toBe(stripAndReverse("מצפה צבאים"));
    });

    test('Outposts chain terminal state allows final character gracefully', () => {
        // Reproducing bug: "מעוזאסתרמעלהשלמהמצפהלא" + "ה" was rejected because no further continuation
        // exists for "מצפה לאה", and there are no other settlements in the entire universe.
        const mockBugData = {
            "כוכב השחר": {
                "name": "כוכב השחר",
                "aliases": [],
                "outposts": [
                    "מעוז אסתר",
                    "מעלה שלמה",
                    "אעירה שחר",
                    "מצפה לאה"
                ]
            },
        };
        const dicts = buildDictionaries(mockBugData);

        // Scenario 1: User typed "מעוזאסתרמעלהשלמהמצפהלא" (missing the final 'ה' of the 3rd outpost)
        const typedPartial = "מעוזאסתרמעלהשלמהמצפהלא";
        const reversedPartial = stripAndReverse(typedPartial);
        const optionsPartial = chooseAll(reversedPartial, dicts.allVariantKeys, new Set(), dicts.keyVariantMap, [], dicts.baseVariantKeys, dicts.outpostKeys);

        // Exact expectation: The computer should propose 'ה' to finish "מצפה לאה"
        expect(optionsPartial).toEqual([
            {
                letter: 'ה',
                key: stripAndReverse("מצפה לאה"),
                former: [stripAndReverse("מעוז אסתר"), stripAndReverse("מעלה שלמה")]
            }
        ]);

        // With ה: "מעוזאסתרמעלהשלמהמצפהלאה"
        // It forms a completed exact match, but doesn't overlap into any untouched remaining settlement.
        // It SHOULD return an object indicating the path is valid but terminal (letter: undefined/null).
        const typedFull = "מעוזאסתרמעלהשלמהמצפהלאה";
        const reversedFull = stripAndReverse(typedFull);
        const optionsFull = chooseAll(reversedFull, dicts.allVariantKeys, new Set(), dicts.keyVariantMap, [], dicts.baseVariantKeys, dicts.outpostKeys);

        expect(optionsFull).toEqual([
            {
                letter: 'כ',
                key: stripAndReverse("כוכב השחר"),
                former: [stripAndReverse("מעוז אסתר"), stripAndReverse("מעלה שלמה"), stripAndReverse("מצפה לאה")]
            }
        ]);

        // The critical bug check: The sequence should NOT return an empty array (which indicates invalid typing)
        expect(optionsFull.length).toBeGreaterThan(0);


        const typedFull1 = "מצפהלאה";
        const reversedFull1 = stripAndReverse(typedFull1);
        const optionsFull1 = chooseAll(reversedFull1, dicts.allVariantKeys, new Set(), dicts.keyVariantMap, [], dicts.baseVariantKeys, dicts.outpostKeys);

        expect(optionsFull1).toEqual([
            {
                letter: 'כ',
                key: stripAndReverse("כוכב השחר"),
                former: [stripAndReverse("מצפה לאה")]
            }
        ]);

        // The critical bug check: The sequence should NOT return an empty array (which indicates invalid typing)
        expect(optionsFull1.length).toBeGreaterThan(0);
    });

    test('Bug Reproduction: Omitting outpostKeys causes chooseAll to incorrectly forbid parent settlement', () => {
        const mockData = {
            "כוכב השחר": {
                "name": "כוכב השחר",
                "aliases": [],
                "outposts": ["מעוז אסתר",
                    "מעלה שלמה",
                    "אעירה שחר",
                    "מצפה לאה"]
            }
        };
        const dicts = buildDictionaries(mockData);
        const userCurrent = stripAndReverse("מצפהלאה");

        // 1. Without passing outpostKeys (simulates the bug in game.js)
        // Since chooseAll does NOT use globals, falling back to the default `new Set()` 
        // means it treats the outpost like a normal settlement. And since a normal settlement 
        // can't be played twice, it forbids its canonical parent!
        const optionsMissingArg = chooseAll(userCurrent, dicts.allVariantKeys, new Set(), dicts.keyVariantMap, [], dicts.baseVariantKeys);
        expect(optionsMissingArg.length).toBe(0); // Fails exactly like the user's game.js log

        // 2. Passing outpostKeys correctly evaluates it as an outpost and suggests the parent
        const optionsWithArg = chooseAll(userCurrent, dicts.allVariantKeys, new Set(), dicts.keyVariantMap, [], dicts.baseVariantKeys, dicts.outpostKeys);
        expect(optionsWithArg.length).toBeGreaterThan(0);
        expect(optionsWithArg[0].key).toBe(stripAndReverse("כוכב השחר"));
    });

});


describe('readGameData', () => {

    test('reads real game_data.json and builds correct structure', () => {
        const raw = require('./data/game_data.json');
        const { db, canonicalToName } = readGameData(raw);

        // db is a Map with one entry per settlement
        expect(db).toBeInstanceOf(Map);
        expect(db.size).toBe(Object.keys(raw).length);

        // ── Spot-check db entry: "אלון מורה" (two outposts, no aliases) ──
        const alonMora = db.get('אלון מורה');
        expect(alonMora).toBeDefined();
        expect(alonMora.name).toBe('אלון מורה');
        expect(alonMora.aliases).toEqual([]);
        expect(alonMora.outposts).toContain('חוות סקאלי');
        expect(alonMora.outposts).toContain('שכונת הרחיבי');
        expect(alonMora.population).toBe('2170');
        expect(alonMora.establishment).toBe('1979');
        expect(typeof alonMora.x).toBe('number');
        expect(typeof alonMora.y).toBe('number');

        // ── Spot-check canonicalToName for "אלון מורה" ──
        expect(canonicalToName).toBeInstanceOf(Map);
        // key = toCanonical(name), value = [entry.name, originalVariant, tag]
        expect(canonicalToName.get('אלונמורה')).toEqual(['אלון מורה', 'אלון מורה']);
        expect(canonicalToName.get('חוותסקאלי')).toEqual(['אלון מורה', 'חוות סקאלי', 'outpost']);
        expect(canonicalToName.get('שכונתהרחיבי')).toEqual(['אלון מורה', 'שכונת הרחיבי', 'outpost']);

        // ── Spot-check: "איתמר" outpost ──
        const itamar = db.get('איתמר');
        expect(itamar).toBeDefined();
        expect(itamar.outposts).toContain('שיר חדש');
        expect(canonicalToName.get('שירחדש')).toEqual(['איתמר', 'שיר חדש', 'outpost']);
    });

    test('hardcoded data builds correct key-value structure', () => {
        const raw = {
            'אילת': {
                name: 'אילת',
                population: '56004',
                establishment: '1951',
                aliases: [],
                outposts: [],
                x: 98,
                y: 595,
            },
            'תל אביב -יפו': {
                name: 'תל אביב',
                population: '460000',
                establishment: '1909',
                aliases: ['יפו'],
                outposts: [],
                x: 90,
                y: 220,
            },
            'קרני שומרון': {
                name: 'קרני שומרון',
                population: '8000',
                establishment: '1978',
                aliases: [],
                outposts: ['מצפה צבאים'],
                x: 160,
                y: 190,
            },
        };

        const { db, canonicalToName } = readGameData(raw);

        expect(db.size).toBe(3);

        // ── db: plain settlement ──
        const eilat = db.get('אילת');
        expect(eilat.name).toBe('אילת');
        expect(eilat.aliases).toEqual([]);
        expect(eilat.outposts).toEqual([]);
        expect(eilat.population).toBe('56004');
        expect(eilat.establishment).toBe('1951');
        expect(eilat.x).toBe(98);
        expect(eilat.y).toBe(595);

        // ── db: settlement with alias ──
        const tlv = db.get('תל אביב -יפו');
        expect(tlv.name).toBe('תל אביב');
        expect(tlv.aliases).toEqual(['יפו']);
        expect(tlv.outposts).toEqual([]);

        // ── db: settlement with outpost ──
        const karni = db.get('קרני שומרון');
        expect(karni.outposts).toEqual(['מצפה צבאים']);
        expect(karni.aliases).toEqual([]);

        // ── canonicalToName: names (key = toCanonical, value = [entry.name, original]) ──
        expect(canonicalToName.get('אילת')).toEqual(['אילת', 'אילת']);
        expect(canonicalToName.get('תלאביב')).toEqual(['תל אביב', 'תל אביב']);
        expect(canonicalToName.get('קרנישומרונ')).toEqual(['קרני שומרון', 'קרני שומרון']);

        // ── canonicalToName: alias ──
        expect(canonicalToName.get('יפו')).toEqual(['תל אביב', 'יפו']);

        // ── canonicalToName: outpost ──
        expect(canonicalToName.get('מצפהצבאימ')).toEqual(['קרני שומרון', 'מצפה צבאים', 'outpost']);

        // ── canonicalToName total: 3 names + 1 alias + 1 outpost = 5 entries ──
        expect(canonicalToName.size).toBe(5);
    });

});

// ────────────────────────────────────────────────────────────────────────────
// checkSequence tests
// ────────────────────────────────────────────────────────────────────────────
// canonicalToName keys (toCanonical = strip non-Hebrew + normalize sofit):
//   toCanonical("אילת")        = "אילת"
//   toCanonical("תל אביב")     = "תלאביב"
//   toCanonical("יפו")         = "יפו"
//   toCanonical("קרני שומרון") = "קרנישומרון"
//   toCanonical("מצפה צבאים")  = "מצפהצבאים"
//
// Values are [entry.name, originalVariant]:
//   "אילת"       → ["אילת",        "אילת"]
//   "תלאביב"     → ["תל אביב",     "תל אביב"]
//   "יפו"        → ["תל אביב",     "יפו"]      ← alias: entry.name is "תל אביב"
//   "קרנישומרון" → ["קרני שומרון", "קרני שומרון"]
//   "מצפהצבאים"  → ["קרני שומרון", "מצפה צבאים"] ← outpost: entry.name is "קרני שומרון"

describe('checkSequence', () => {

    let canonicalToName;

    beforeEach(() => {
        const raw = {
            'אילת': {
                name: 'אילת', population: '56004', establishment: '1951',
                aliases: [], outposts: [], x: 98, y: 595
            },
            'תל אביב -יפו': {
                name: 'תל אביב', population: '460000', establishment: '1909',
                aliases: ['יפו'], outposts: [], x: 90, y: 220
            },
            'קרני שומרון': {
                name: 'קרני שומרון', population: '8000', establishment: '1978',
                aliases: [], outposts: ['מצפה צבאים'], x: 160, y: 190
            },
        };
        ({ canonicalToName } = readGameData(raw));
    });

    function run(string, forbidden = []) {
        const results = [];
        checkSequence(string, canonicalToName, forbidden, [], results);
        return results;
    }

    test('"ת" is a valid partial for "תל אביב" (canonical "תלאביב" starts with "ת")', () => {
        const results = run('ת');
        expect(results).toHaveLength(1);
        expect(results[0]).toEqual({
            sequence: [],
            forbidden: [],
            lastCanonical: 'תלאביב',
            lastName: 'תל אביב',
        });
    });

    test('"ב" has NO result — no canonical key starts with "ב"', () => {
        const results = run('ב');
        expect(results).toHaveLength(0);
    });

    test('full key consumed, then partial — sequence and forbidden are tracked', () => {
        // "אילת" + "ת" → consume canonical "אילת", remaining "ת" → partial "תלאביב"
        const results = run('אילתת');
        expect(results).toHaveLength(1);
        expect(results[0]).toEqual({
            sequence: ['אילת'],
            forbidden: ['אילת'],
            lastCanonical: 'תלאביב',
            lastName: 'תל אביב',
        });
    });

    test('alias canonical key is consumed as a full key', () => {
        // "יפו" + "א" → consume canonical "יפו" (alias), remaining "א" → partial "אילת"
        const results = run('יפוא');
        expect(results).toHaveLength(1);
        expect(results[0]).toEqual({
            sequence: ['יפו'],
            forbidden: ['תל אביב'],   // entry.name is forbidden, not the alias
            lastCanonical: 'אילת',
            lastName: 'אילת',
        });
    });

    test('outpost canonical key is consumed as a full key', () => {
        // "מצפהצבאים" + "ת" → consume outpost, remaining "ת" → partial "תלאביב"
        const results = run('מצפהצבאימת');
        expect(results).toHaveLength(1);
        expect(results[0]).toEqual({
            sequence: ['מצפהצבאימ'],
            forbidden: ['קרני שומרון'],   // entry.name of the outpost's settlement
            lastCanonical: 'תלאביב',
            lastName: 'תל אביב',
        });
    });

    test('no-repeat: same settlement name cannot appear twice in the sequence', () => {
        // "אילת" + "אילת" = "אילתאילת" (no sofit in אילת)
        const results = run('אילתאילת');
        expect(results).toHaveLength(0);
    });

    test('empty string — all non-forbidden canonical keys are valid continuations', () => {
        const results = run('');
        expect(results).toHaveLength(5);
        const canonicalSet = new Set(results.map(r => r.lastCanonical));
        expect(canonicalSet.has('אילת')).toBe(true);
        expect(canonicalSet.has('תלאביב')).toBe(true);
        expect(canonicalSet.has('יפו')).toBe(true);
        expect(canonicalSet.has('קרנישומרונ')).toBe(true);
        expect(canonicalSet.has('מצפהצבאימ')).toBe(true);
    });

    test('pre-populated forbidden list excludes those names from results', () => {
        const results = run('', ['תל אביב']);
        // "תלאביב" → entry.name="תל אביב" (forbidden) ✗
        // "יפו"    → entry.name="תל אביב" (forbidden) ✗
        expect(results).toHaveLength(3);
        expect(results.every(r => r.lastName !== 'תל אביב')).toBe(true);
    });

});
// ────────────────────────────────────────────────────────────────────────────
// checkSequence — ambiguous prefix tests
// ────────────────────────────────────────────────────────────────────────────
// "תל אביב" (canonical "תלאביב") and "תל מונד" (canonical "תלמונד") share
// the prefix "תל". The function must find ALL matching options.

describe('checkSequence — ambiguous prefix', () => {

    let canonicalToName;

    beforeEach(() => {
        const raw = {
            'תל אביב': {
                name: 'תל אביב', population: '460000', establishment: '1909',
                aliases: [], outposts: [], x: 90, y: 220
            },
            'תל מונד': {
                name: 'תל מונד', population: '5000', establishment: '1953',
                aliases: [], outposts: [], x: 88, y: 225
            },
            'אשדוד': {
                name: 'אשדוד', population: '220000', establishment: '1956',
                aliases: [], outposts: [], x: 100, y: 250
            },
        };
        // canonical keys: "תלאביב", "תלמונד", "אשדוד"
        ({ canonicalToName } = readGameData(raw));
    });

    function run(string, forbidden = []) {
        const results = [];
        checkSequence(string, canonicalToName, forbidden, [], results);
        return results;
    }

    test('partial "תל" matches both "תל אביב" and "תל מונד"', () => {
        const results = run('תל');
        expect(results).toHaveLength(2);
        const canonicals = results.map(r => r.lastCanonical).sort();
        expect(canonicals).toEqual(['תלאביב', 'תלמונד'].sort());
    });

    test('consuming "תל אביב" then partial "תל" only matches "תל מונד"', () => {
        const results = run('תלאביבתל');
        expect(results).toHaveLength(1);
        expect(results[0]).toEqual({
            sequence: ['תלאביב'],
            forbidden: ['תל אביב'],
            lastCanonical: 'תלמונד',
            lastName: 'תל מונד',
        });
    });

    test('full chain: "תל אביב" then "תל מונד" then partial "א" for "אשדוד"', () => {
        const results = run('תלאביבתלמונדא');
        expect(results).toHaveLength(1);
        expect(results[0]).toEqual({
            sequence: ['תלאביב', 'תלמונד'],
            forbidden: ['תל אביב', 'תל מונד'],
            lastCanonical: 'אשדוד',
            lastName: 'אשדוד',
        });
    });

    test('"תל מונד" can be first: partial "תל" then only "תל אביב" remains', () => {
        const results = run('תלמונדתל');
        expect(results).toHaveLength(1);
        expect(results[0]).toEqual({
            sequence: ['תלמונד'],
            forbidden: ['תל מונד'],
            lastCanonical: 'תלאביב',
            lastName: 'תל אביב',
        });
    });

});

// ────────────────────────────────────────────────────────────────────────────
// readGameData — double-letter (יי / וו) canonical variant tests
// ────────────────────────────────────────────────────────────────────────────

describe('readGameData — double-letter canonical variants', () => {

    let canonicalToName;

    beforeEach(() => {
        const raw = {
            'נחלייה': {
                name: 'נחלייה', population: '5000', establishment: '1950',
                aliases: [], outposts: [], x: 50, y: 50
            },
            'חוות נוף': {
                name: 'חוות נוף', population: '3000', establishment: '1990',
                aliases: [], outposts: [], x: 60, y: 60
            },
            'כרמל': {
                name: 'כרמל', population: '40000', establishment: '1920',
                aliases: ['כרמליי'], outposts: [], x: 70, y: 70
            },
            'עמק': {
                name: 'עמק', population: '10000', establishment: '1960',
                aliases: ['מי-יד'], outposts: [], x: 80, y: 80
            },
        };
        ({ canonicalToName } = readGameData(raw));
    });

    test('double יי in name adds single-י variant', () => {
        expect(canonicalToName.get('נחלייה')).toEqual(['נחלייה', 'נחלייה']);
        expect(canonicalToName.get('נחליה')).toEqual(['נחלייה', 'נחלייה', 'short']);
    });

    test('double וו in name adds single-ו variant', () => {
        expect(canonicalToName.get('חוותנופ')).toEqual(['חוות נוף', 'חוות נוף']);
        expect(canonicalToName.get('חותנופ')).toEqual(['חוות נוף', 'חוות נוף', 'short']);
    });

    test('double יי in alias adds single-י variant', () => {
        expect(canonicalToName.get('כרמליי')).toEqual(['כרמל', 'כרמליי']);
        expect(canonicalToName.get('כרמלי')).toEqual(['כרמל', 'כרמליי', 'short']);
    });

    test('hyphenated "מי-יד" does NOT produce a variant (original lacks adjacent יי)', () => {
        expect(canonicalToName.has('מיד')).toBe(false);
        expect(canonicalToName.get('מייד')).toEqual(['עמק', 'מי-יד']);
    });

    test('total size = 4 names + 2 aliases + 3 variants', () => {
        // 6 original entries + 3 variants (נחליה, חותנוף, כרמלי) = 9
        expect(canonicalToName.size).toBe(9);
    });

});
