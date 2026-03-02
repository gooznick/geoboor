const fs = require('fs');

const raw = fs.readFileSync('data/easter_eggs.json', 'utf8');
const eggsRaw = JSON.parse(raw);
let count = 0;
for (const [key, val] of Object.entries(eggsRaw)) {
    count++;
}
print(count, "eggs loaded");
