const SOFIT_MAP = { 'ם': 'מ', 'ן': 'נ', 'ץ': 'צ', 'ף': 'פ', 'ך': 'כ' };
function stripAndReverse(name) {
    return Array.from(name.replace(/[^\u05D0-\u05EA]/g, ''))
        .reverse()
        .map(c => SOFIT_MAP[c] ?? c)
        .join('');
}
let current = '';
let word = "פסגות"; // pe, samekh, gimel, vav, tav
console.log("word is", word, "key is", stripAndReverse(word));
let letters = word.split('');
for (let ch of letters) {
    current = ch + current;
    console.log("typed", ch, "current is", current);
}
