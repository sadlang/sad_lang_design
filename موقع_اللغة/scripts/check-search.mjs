// البحثُ يوحّد الهمزاتِ والتشكيل. يُشغَّل بعد البناء (npm run build)، ووحده: npm run check:search
//
// لا إعدادَ لذلك: Pagefind يكتشف العربيّةَ من <html lang="ar">، فيمرّر الكلماتِ على جذّاع Snowball العربيّ
// في الفهرس وفي السؤال معًا. وهو يحذف التشكيلَ والتطويل، ويجعل «أ إ آ» ألفًا، و«ؤ» واوًا، و«ئ ى» ياءً،
// و«ة» هاءً. وهذا الفحصُ يحرس ذلك: إن تغيّرت لغةُ الصفحات أو سلوكُ Pagefind عند ترقيته فشل البناء.
//
// لكلّ زوجٍ: صورةٌ كما في الموقع، وصورةٌ يكتبها الباحث. ويجب أن تُرجعا الصفحاتِ نفسَها، ولا تكونا فارغتين.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const PAIRS = [
	// الهمزة على الألف (ك‑١: «أ إ آ» و«ا» حرفٌ واحدٌ في المعرِّفات)
	['الأنواع', 'الانواع'],
	['إعادة', 'اعادة'],
	['إلى', 'الى'],
	['آخر', 'اخر'],
	['خطأ', 'خطا'],
	// الهمزاتُ الأخرى
	['مؤقت', 'موقت'],
	['قارئ', 'قاري'],
	// التشكيلُ والشدّة
	['المتغيّر', 'المتغير'],
	['المتغيّر', 'المُتَغَيِّر'],
	['تُهيَّأ', 'تهيا'],
	['أُسَر', 'اسر'],
	['القيمةُ', 'القيمة'],
	// التطويل
	['المتغيّر', 'المتـغير'],
];

const dist = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'dist');
const bundle = path.join(dist, 'pagefind', 'pagefind.js');
if (!fs.existsSync(bundle)) {
	console.error('فحصُ البحث: لا فهرس. ابنِ الموقع أوّلًا (npm run build).');
	process.exit(1);
}

// pagefind.js مكتوبٌ للمتصفّح: يجلب ملفّاتِ الفهرس بـfetch. فيُقرأ هنا من dist/ مباشرةً.
const ORIGIN = 'http://sad.local';
globalThis.fetch = async (url) => new Response(fs.readFileSync(path.join(dist, decodeURI(new URL(url, ORIGIN).pathname))));
globalThis.window ??= globalThis;
globalThis.location ??= new URL(`${ORIGIN}/`);

const pagefind = await import(pathToFileURL(bundle).href);
await pagefind.options({ basePath: `${ORIGIN}/pagefind/` });

/** @param {string} q */
const urls = async (q) => {
	const r = await pagefind.search(q);
	return (await Promise.all(r.results.map(async (x) => (await x.data()).url))).sort();
};

const errors = [];
for (const [site, typed] of PAIRS) {
	const [a, b] = await Promise.all([urls(site), urls(typed)]);
	if (!a.length) errors.push(`«${site}» لا يجد شيئًا. أحُذفت الكلمةُ من الموقع؟ فاختر زوجًا غيره`);
	else if (a.join('\n') !== b.join('\n')) errors.push(`«${typed}» يجد ${b.length} صفحة، و«${site}» يجد ${a.length}`);
}
await pagefind.destroy?.();

if (errors.length) {
	console.error(`فحصُ البحث: ${errors.length} خطأ\n- ${errors.join('\n- ')}`);
	process.exit(1);
}
console.log(`فحصُ البحث: ${PAIRS.length} زوجًا، كلُّ صورتين تجدان الصفحاتِ نفسَها.`);
