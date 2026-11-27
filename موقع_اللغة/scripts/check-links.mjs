// الروابطُ الداخليّة تصل. يُشغَّل بعد البناء (npm run build)، ووحده: npm run check:links
//
// الموقعُ منشورٌ تحت اسم المستودع (BASE في src/lib/site.mjs، وقرارات الموقع، القرار ٢٤)، فرابطٌ يبدأ بـ/
// يخرج منه فيعطي ٤٠٤. فيُفحص كلُّ href وsrc بين علامتي تنصيص مزدوجتين في صفحات dist/ (وهكذا يكتبها Astro):
// يُحَلّ من عنوان صفحته، ويجب أن يقع تحت BASE وأن يصل إلى ملفّ، أو إلى مجلّدٍ فيه index.html.
// **وصفحةُ ٤٠٤ تُعرض في أيّ مسار،** فلا يُقبل فيها رابطٌ نسبيّ: رابطُها مطلقٌ ومعه BASE.
// ولا تُفحص: الروابطُ إلى خادمٍ آخر، وما بعد # أو ?، وsrcset، والروابطُ داخل CSS وJS.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { BASE as SITE_BASE } from '../src/lib/site.mjs';
import { count } from './count.mjs';

const BASE = SITE_BASE + '/';
const ORIGIN = 'http://sad.local';
const LINK = /** @type {const} */ (['رابطٌ', 'رابطان', 'روابط', 'رابطًا', 'رابط']);
const dist = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'dist');
if (!fs.existsSync(dist)) {
	console.error('فحصُ الروابط: لا مجلّدَ dist/. ابنِ الموقع أوّلًا (npm run build).');
	process.exit(1);
}

/** @param {string} dir @returns {string[]} */
const pages = (dir) =>
	fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
		const p = path.join(dir, e.name);
		return e.isDirectory() ? pages(p) : e.name.endsWith('.html') ? [p] : [];
	});

/** يصل المسارُ إلى ملفٍّ في dist/؟ وترميزٌ غيرُ صالح (`%` بلا رقمين) رابطٌ لا يصل. @param {string} pathname */
const exists = (pathname) => {
	let rel;
	try {
		rel = decodeURIComponent(pathname.slice(BASE.length));
	} catch {
		return false;
	}
	const file = path.join(dist, rel);
	return (fs.existsSync(file) && fs.statSync(file).isFile()) || fs.existsSync(path.join(file, 'index.html'));
};

// GitHub Pages لا يعرض صفحةَ ٤٠٤ الخاصّة إلّا من 404.html في الجذر، لا من 404/index.html.
if (!fs.existsSync(path.join(dist, '404.html'))) {
	console.error('فحصُ الروابط: لا 404.html في جذر dist/، فلا يعرض GitHub Pages صفحةَ «غير موجودة».');
	process.exit(1);
}

const files = pages(dist);
if (!files.length) {
	console.error('فحصُ الروابط: لا صفحةَ HTML في dist/. ابنِ الموقع أوّلًا (npm run build).');
	process.exit(1);
}
const bad = [];
let checked = 0;
for (const file of files) {
	const rel = path.relative(dist, file).replaceAll('\\', '/');
	const pageUrl = ORIGIN + BASE + (rel.endsWith('index.html') ? rel.slice(0, -'index.html'.length) : rel);
	for (const m of fs.readFileSync(file, 'utf8').matchAll(/\s(?:href|src)="([^"#?]*)/g)) {
		const raw = m[1];
		if (raw === '' || /^[a-z][a-z0-9+.-]*:|^\/\//i.test(raw)) continue;
		checked++;
		if (rel === '404.html' && !raw.startsWith(BASE)) {
			bad.push(`${rel}: ${raw} (صفحةُ ٤٠٤ تُعرض في أيّ مسار، فرابطُها مطلقٌ يبدأ بـ${BASE})`);
			continue;
		}
		const url = new URL(raw, pageUrl);
		if (url.origin !== ORIGIN || !url.pathname.startsWith(BASE) || !exists(url.pathname)) {
			bad.push(`${rel}: ${raw}`);
		}
	}
}

if (bad.length) {
	console.error(`فحصُ الروابط: ${count(bad.length, LINK)} لا يصل، أو يخرج من ${BASE}:`);
	for (const b of bad) console.error(`  ${b}`);
	process.exit(1);
}
console.log(`فحصُ الروابط: ${count(checked, LINK)} داخليًّا، كلُّها تحت ${BASE} وتصل.`);
