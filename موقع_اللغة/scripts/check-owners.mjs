// لكلّ قرارٍ صفحةٌ مالكةٌ واحدة. يُشغَّل قبل البناء (npm run build)، ووحده: npm run check:owners
// يقرأ «يملك: [...]» من رأس كلّ صفحةٍ في src/content/docs، ويقارنه بـsrc/lib/decisions.mjs.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { DECISIONS } from '../src/lib/decisions.mjs';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'src', 'content', 'docs');

/** @param {string} dir @returns {string[]} */
const walk = (dir) =>
	fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
		const p = path.join(dir, e.name);
		return e.isDirectory() ? walk(p) : /\.mdx?$/.test(e.name) ? [p] : [];
	});

/** @type {Map<string, string[]>} */
const owners = new Map();
const errors = [];

for (const file of walk(root)) {
	const rel = path.relative(root, file).replaceAll('\\', '/');
	const fm = fs.readFileSync(file, 'utf8').replace(/\r\n/g, '\n').match(/^---\n([\s\S]*?)\n---/);
	const line = fm?.[1].match(/^يملك:\s*\[(.*)\]\s*$/m);
	if (!line) continue;
	for (const raw of line[1].split(',')) {
		const id = raw.trim().replace(/^["']|["']$/g, '');
		if (!id) continue;
		if (!(id in DECISIONS)) errors.push(`${rel}: يملك «${id}»، وليس في src/lib/decisions.mjs`);
		owners.set(id, [...(owners.get(id) ?? []), rel]);
	}
}

for (const [id, pages] of owners) if (pages.length > 1) errors.push(`«${id}» تملكه ${pages.length} صفحات: ${pages.join('، ')}`);
for (const id of Object.keys(DECISIONS)) if (!owners.has(id)) errors.push(`«${id}» (${DECISIONS[id]}) بلا صفحةٍ مالكة`);

if (errors.length) {
	console.error(`فحصُ الصفحات المالكة: ${errors.length} خطأ\n- ${errors.join('\n- ')}`);
	process.exit(1);
}
console.log(`فحصُ الصفحات المالكة: ${owners.size} قرارًا، لكلٍّ صفحةٌ واحدة.`);
