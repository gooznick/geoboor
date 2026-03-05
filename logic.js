// GeoBoor Logic

const HEBREW_LETTERS = new Set('אבגדהוזחטיכלמנסעפצקרשת');
const SOFIT_MAP = { 'ם': 'מ', 'ן': 'נ', 'ץ': 'צ', 'ף': 'פ', 'ך': 'כ' };

function removeSofit(ch) {
    return SOFIT_MAP[ch] ?? ch;
}

function isHebrewLetter(ch) {
    return HEBREW_LETTERS.has(ch);
}

// Two consecutive yod (י\u05D9) → single yod, two vav (ו\u05D5) → single vav
const RE_DOUBLE_YOD = /\u05D9\u05D9/g;   // יי
const RE_DOUBLE_VAV = /\u05D5\u05D5/g;   // וו

/**
 * Generate the set of name-string variants by applying יי→י / וו→ו
 * BEFORE stripping spaces, so word boundaries block cross-word substitutions.
 * e.g. "תלמי יחיאל" keeps both יי (they're in separate words); "איייל" collapses to "איל".
 */
function nameVariants(name) {
    const v1 = name.replace(RE_DOUBLE_YOD, '\u05D9');
    const v2 = name.replace(RE_DOUBLE_VAV, '\u05D5');
    const v3 = v1.replace(RE_DOUBLE_VAV, '\u05D5');
    return new Set([name, v1, v2, v3]);
}

/** Strip non-Hebrew chars, reverse, and normalize sofit letters in one step. */
function stripAndReverse(name) {
    return Array.from(name.replace(/[^\u05D0-\u05EA]/g, ''))
        .reverse()
        .map(c => SOFIT_MAP[c] ?? c)
        .join('');
}

function getVariants(entry) {
    const rawNames = [entry.name, ...(entry.aliases || [])];
    const baseKeys = new Set();
    const variantKeys = new Set();

    for (const n of rawNames) {
        if (!n) continue;

        // The first variant returned by nameVariants is ALWAYS the original string
        const variantsArr = Array.from(nameVariants(n));

        // The original string is a base key
        baseKeys.add(stripAndReverse(variantsArr[0]));

        // Any subsequent strings from nameVariants are modified variants
        for (let i = 1; i < variantsArr.length; i++) {
            variantKeys.add(stripAndReverse(variantsArr[i]));
        }
    }
    return {
        baseKeys: [...baseKeys],
        variantKeys: [...variantKeys]
    };
}

/**
 * Returns all possibilities for what can follow the current accumulated string.
 * Returns array of { letter, key, former } where:
 *   - letter: next letter the computer would add (to the left)
 *   - key: variant key of the chosen settlement
 *   - former: variant keys of settlements already consumed in this path
 *
 * `forbidCanon`: canonical keys of permanently forbidden settlements (set on mistake only).
 */
function chooseAll(current, keySet, forbidCanon, keyVariantMap, former, baseKeySet = null, outpostKeys = new Set()) {

    former = former || [];
    if (!current) {
        // Collect canonical keys that are forbidden OR have already been used in this path
        const excludeCanon = new Set(forbidCanon);
        for (const f of former) {
            if (!outpostKeys.has(f)) {
                excludeCanon.add(keyVariantMap[f]);
            }
        }

        const baseOptions = [];

        // If empty string, we want to look at ALL possible valid starts.
        // If a baseKeySet is provided, we ONLY use the base keys for proposals.
        // Otherwise fallback to keySet for backward compatibility.
        const searchSet = baseKeySet || keySet;

        for (const k of searchSet) {
            const canon = keyVariantMap[k];
            if (!excludeCanon.has(canon) && !former.includes(k)) {
                baseOptions.push({ letter: k[k.length - 1], key: k, former: former });
            }
        }
        return baseOptions;
    }

    const results = [];

    // Find variant keys that END WITH current (settlement whose name starts with current read RTL)
    for (const k of keySet) {
        if (k.endsWith(current) && k !== current &&
            !former.includes(k) && !forbidCanon.has(keyVariantMap[k])) {
            results.push({ letter: k[k.length - 1 - current.length], key: k, former });
        }
    }

    // Check if current ENDS WITH a full settlement key (it was consumed)
    for (const k of keySet) {
        if (current.endsWith(k) && !former.includes(k) && !forbidCanon.has(keyVariantMap[k])) {
            const newFormer = [...former, k];
            const newCurrent = current.slice(0, current.length - k.length);
            results.push(...chooseAll(newCurrent, keySet, forbidCanon, keyVariantMap, newFormer, baseKeySet, outpostKeys));
        }
    }

    if (baseKeySet && results.length > 0) {
        // Filter out variant keys if there's a base key that also represents the same canonical settlement
        // for the same partial path.
        const groupsWithBase = new Set();
        for (const r of results) {
            if (baseKeySet.has(r.key)) {
                // Generate a group ID using canonical key + former array 
                const groupId = keyVariantMap[r.key] + '|' + (r.former || []).join(',');
                groupsWithBase.add(groupId);
            }
        }
        return results.filter(r => {
            if (baseKeySet.has(r.key)) return true;
            const groupId = keyVariantMap[r.key] + '|' + (r.former || []).join(',');
            return !groupsWithBase.has(groupId);
        });
    }
    return results;
}

/**
 * Returns the set of variant keys that appear in ALL options (guaranteed consumed).
 */
function findAllFormer(options) {
    if (!options.length) return new Set();
    let common = new Set(options[0].former);
    for (const opt of options) {
        const s = new Set(opt.former);
        common = new Set([...common].filter(x => s.has(x)));
    }
    return common;
}

/**
 * Parses raw JSON settlement data to build the dictionaries for the game.
 * Returns an object containing: { keyVariantMap, variantDisplayName, allVariantKeys, baseVariantKeys }
 * Returns an object containing: { keyVariantMap, variantDisplayName, allVariantKeys, baseVariantKeys, outpostKeys }
 */
function buildDictionaries(raw) {
    const keyVariantMap = {};         // variantKey → canonical key
    const variantDisplayName = {};    // variantKey → display name
    const allVariantKeys = new Set(); // all valid variant reversed-name strings
    const baseVariantKeys = new Set(); // strictly the unmodified names and aliases keys
    const outpostKeys = new Set(); // reversed keys corresponding strictly to outposts

    for (const [canonKey, entry] of Object.entries(raw)) {
        // Collect normal names and aliases
        const rawNames = [entry.name, ...(entry.aliases || [])].filter(Boolean);
        for (const n of rawNames) {
            const variantsArr = Array.from(nameVariants(n));

            // The first variant is always the base
            const baseKey = stripAndReverse(variantsArr[0]);
            allVariantKeys.add(baseKey);
            baseVariantKeys.add(baseKey);
            keyVariantMap[baseKey] = canonKey;
            if (!variantDisplayName[baseKey]) variantDisplayName[baseKey] = n;

            // Rest are variations (double-vav adjustments etc)
            for (let i = 1; i < variantsArr.length; i++) {
                const variantKey = stripAndReverse(variantsArr[i]);
                allVariantKeys.add(variantKey);
                keyVariantMap[variantKey] = canonKey;
                if (!variantDisplayName[variantKey]) variantDisplayName[variantKey] = n;
            }
        }

        // Collect outposts
        const rawOutposts = (entry['outposts'] || []).filter(Boolean);
        for (const op of rawOutposts) {
            const variantsArr = Array.from(nameVariants(op));

            const baseKey = stripAndReverse(variantsArr[0]);
            allVariantKeys.add(baseKey);
            // Outposts are NOT added to baseVariantKeys so the computer won't naturally propose them on empty strings
            // But we do track them in outpostKeys
            outpostKeys.add(baseKey);
            keyVariantMap[baseKey] = canonKey;
            if (!variantDisplayName[baseKey]) variantDisplayName[baseKey] = op;

            for (let i = 1; i < variantsArr.length; i++) {
                const variantKey = stripAndReverse(variantsArr[i]);
                allVariantKeys.add(variantKey);
                outpostKeys.add(variantKey);
                keyVariantMap[variantKey] = canonKey;
                if (!variantDisplayName[variantKey]) variantDisplayName[variantKey] = op;
            }
        }

        // canonical key always maps to itself
        keyVariantMap[canonKey] = canonKey;
        if (!variantDisplayName[canonKey]) variantDisplayName[canonKey] = entry.name;
    }

    return { keyVariantMap, variantDisplayName, allVariantKeys, baseVariantKeys, outpostKeys };
}

/**
 * Checks if the current string triggers any new easter eggs.
 * Mutates `foundEggsSet` by adding newly found keys.
 * Returns an array of triggered egg objects: [{ msg, points }, ...]
 */
function checkEasterEggs(currentStr, easterEggData, keyVariantMap, foundEggsSet) {
    const newlyFound = [];
    for (const [key, egg] of Object.entries(easterEggData)) {
        if (!foundEggsSet.has(key)) {
            // Find the canonical key for this easter egg
            const canonKey = keyVariantMap[key];
            if (canonKey) {
                // Find all variants for this canonical key
                const variants = Object.keys(keyVariantMap).filter(k => keyVariantMap[k] === canonKey);
                // Check if current string starts with any of these variants
                if (variants.some(v => currentStr.startsWith(v))) {
                    foundEggsSet.add(key);
                    newlyFound.push(egg);
                }
            }
        }
    }
    return newlyFound;
}

// Export for Node.js environments (like Jest)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        HEBREW_LETTERS,
        SOFIT_MAP,
        removeSofit,
        isHebrewLetter,
        nameVariants,
        stripAndReverse,
        getVariants,
        buildDictionaries,
        chooseAll,
        findAllFormer,
        checkEasterEggs
    };
}
