// الموقع لا يحمّل شيئًا من خادم آخر (قرارات الموقع، القرار ٢٠). يُشغَّل بعد البناء، ووحده: npm run check:external
//
// يفحص ما يحمّله المتصفّح وحده، في ملفّات HTML وSVG وCSS من dist/:
// - href في <link> إلّا ما لا يُحمَّل (canonical وalternate وsitemap وأمثالها، وحدها بلا قيمة تُحمِّل)،
//   وimagesrcset فيه؛ وhref وxlink:href في كلّ وسم غيره إلّا <a> و<area> (فهما روابط)، ومنه <base> و<image> و<use> من SVG.
// - src وsrcset وposter وbackground في أيّ وسم، وdata في <object>، وما في srcdoc من <iframe>.
// - كتل <style>، وسمة style، وسمات SVG التي تأخذ url() (fill وstroke وfilter وmask وclip-path وmarker-* وcursor)،
//   و@import وurl() وimage-set() في CSS. وتُهمَل @namespace لأنّ عنوانها اسم لا يُحمَّل.
// والوسوم تُقرأ كما يقرؤها المتصفّح: القيمة بعلامتي تنصيص أو بلا علامة، وتُفكّ كياناتها (&#x2F; و&quot; وأمثالهما)
// وتهريبات CSS (\2f)، وتُترك التعليقات ومتون <script>. والعنوان من خادم آخر إن بدأ بشرطتين (/ أو \)
// أو بمخطّط غير data: وblob: وabout:، بعد حذف ما يحذفه المتصفّح من فراغ وتحكّم.
//
// ولا يفحص: الروابطَ التي ينقر عليها القارئ (<a href>) فليست تحميلًا، ولا ملفّات JS (ما تجلبه بـfetch أو import
// وقتَ التشغيل لا يُعرف بقراءة نصّها؛ وسكربتات الموقع من Astro وStarlight وPagefind، وتحميلُها نفسُه مفحوص).
// ولا <script type="importmap"> (من باب JS)، ولا <meta http-equiv="refresh"> ولا <a ping> (انتقالٌ أو نقرٌ لا تحميل).
// وهذه الحدود حسمها المالك (٢٠٢٦-١١-٢٦)، والفحصُ كافٍ كما هو.
//
// رمز الخروج: ٠ إن لم يوجد مورد من خادم آخر، و١ إن وُجد أو لم يوجد dist/ أو لم يكن فيه ملفّ يُفحص.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const DIST = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'dist');

/** المتصفّح يحذف الفراغ ومحارف التحكّم من طرفي العنوان، والجدولة والسطر الجديد من داخله. @param {string} u */
const clean = (u) => u.replace(/^[\x00-\x20]+|[\x00-\x20]+$/g, '').replace(/[\t\n\r]/g, '');
const EXTERNAL = /^(?:[\\/]{2}|(?!(?:data|blob|about):)[a-z][a-z0-9+.-]*:)/i;

// --- CSS ---
const STR = String.raw`"((?:[^"\\\n]|\\[\s\S])*)|'((?:[^'\\\n]|\\[\s\S])*)`;
// يكفي أوّل العنوان لمعرفة خادمه، فلا يُشترط إغلاق القوس ولا علامة التنصيص.
const URL_FN = new RegExp(String.raw`url\(\s*(?:${STR}|((?:[^\s"'()\\]|\\[\s\S])*))`, 'gi');
const IMPORT = new RegExp(String.raw`@import\s*(?:${STR})`, 'gi');
const STRING = new RegExp(`(?:${STR})`, 'g');
/** @param {string} s */
const unescapeCss = (s) =>
	s.replace(/\\(?:([0-9a-f]{1,6})[ \t\n\r\f]?|\n|([\s\S]))/gi, (_, hex, ch) =>
		hex ? String.fromCodePoint(Math.min(parseInt(hex, 16), 0x10ffff) || 0xfffd) : (ch ?? ''),
	);
/** النصوص في image-set(...) إلى قوسها المغلق، ولو تداخلت الأقواس. ولا يُعاد مسح ما مُسح، فالزمن خطّيّ.
 *  @param {string} css @returns {string[]} */
const imageSetStrings = (css) => {
	const out = [];
	let end = 0;
	for (const m of css.matchAll(/image-set\(/gi)) {
		if (m.index < end) continue;
		let depth = 1;
		let i = m.index + m[0].length;
		for (; i < css.length && depth > 0; i++) {
			const c = css[i];
			if (c === '(') depth++;
			else if (c === ')') depth--;
			else if (c === '"' || c === "'") {
				STRING.lastIndex = i;
				const s = STRING.exec(css);
				if (s && s.index === i) {
					out.push(s[1] ?? s[2] ?? '');
					i += s[0].length; // s[0] بلا علامة الإغلاق، فيتخطّاها i++
				}
			}
		}
		end = i;
	}
	return out;
};
/** @param {string} css @returns {string[]} */
const cssUrls = (css) => {
	if (!/url\(|@import|image-set\(/i.test(css)) return [];
	const text = css.replace(/@namespace\b[^;{}]*;?/gi, '');
	return [
		...[...text.matchAll(URL_FN)].map((m) => m[1] ?? m[2] ?? m[3] ?? ''),
		...[...text.matchAll(IMPORT)].map((m) => m[1] ?? m[2] ?? ''),
		...imageSetStrings(text),
	].map(unescapeCss);
};

// --- HTML وSVG ---
const NAMED = { quot: '"', apos: "'", amp: '&', lt: '<', gt: '>', sol: '/', bsol: '\\', colon: ':', period: '.', Tab: '\t', NewLine: '\n', lpar: '(', rpar: ')', nbsp: ' ' };
/** @param {string} s */
const decode = (s) =>
	s.replace(/&(?:#x([0-9a-f]+);?|#(\d+);?|([a-z]+);)/gi, (e, hex, dec, name) => {
		if (name) return Object.hasOwn(NAMED, name) ? NAMED[/** @type {keyof typeof NAMED} */ (name)] : e;
		const cp = parseInt(hex ?? dec, hex ? 16 : 10);
		return cp > 0 && cp <= 0x10ffff ? String.fromCodePoint(cp) : '�';
	});
const WS = /[\t\n\f\r ]/;
const TAG_NAME = /<([a-z][^\t\n\f\r />]*)/iy;
const COMMENT_END = /--!?>/g;
const RAW = new Set(['script', 'style', 'textarea', 'title']);
const FOREIGN = new Set(['svg', 'math']);
const FOREIGN_END = /<\/(?:svg|math)[\t\n\f\r />]/iy;

/**
 * الوسوم الافتتاحيّة كما يقسمها المتصفّح، بسماتها مفكوكةً، وأوّلُ السمة المكرّرة هو المعتبر.
 * و«/>» يُغلق الوسم في ملفّ SVG وفي <svg> و<math> داخل HTML وحدها؛ أمّا «<script/>» في HTML فما بعده متنٌ له.
 * @param {string} s @param {boolean} xml ملفّ SVG، فكلّه محتوًى أجنبيّ @returns {Generator<{ name: string, attrs: Map<string, string>, body: string }>}
 */
function* tags(s, xml) {
	const n = s.length;
	let i = 0;
	let foreign = 0; // عمق <svg> و<math> في HTML
	while ((i = s.indexOf('<', i)) !== -1) {
		FOREIGN_END.lastIndex = i;
		if (foreign && FOREIGN_END.test(s)) foreign--;
		if (s.startsWith('<!--', i)) {
			COMMENT_END.lastIndex = i + 2; // «<!-->» و«<!--->» تعليقان فارغان
			i = COMMENT_END.exec(s) ? COMMENT_END.lastIndex : n;
			continue;
		}
		TAG_NAME.lastIndex = i;
		const m = TAG_NAME.exec(s);
		if (!m) {
			i++;
			continue;
		}
		const name = m[1].toLowerCase();
		const attrs = new Map();
		let j = TAG_NAME.lastIndex;
		let selfClosing = false; // «/» قبل «>» مباشرةً، لا آخرُ قيمةٍ بلا علامة تنصيص
		for (;;) {
			selfClosing = false;
			while (j < n && (WS.test(s[j]) || s[j] === '/')) selfClosing = s[j++] === '/';
			if (j >= n || s[j] === '>') break;
			let k = j + 1; // أوّل محرف في الاسم قد يكون «=»
			while (k < n && !WS.test(s[k]) && !'/>='.includes(s[k])) k++;
			const attr = s.slice(j, k).toLowerCase();
			j = k;
			while (j < n && WS.test(s[j])) j++;
			let value = '';
			if (s[j] === '=') {
				j++;
				while (j < n && WS.test(s[j])) j++;
				if (s[j] === '"' || s[j] === "'") {
					const end = s.indexOf(s[j], j + 1);
					value = s.slice(j + 1, end === -1 ? n : end);
					j = end === -1 ? n : end + 1;
				} else {
					k = j;
					while (k < n && !WS.test(s[k]) && s[k] !== '>') k++;
					value = s.slice(j, k);
					j = k;
				}
			}
			if (!attrs.has(attr)) attrs.set(attr, decode(value));
		}
		i = j + 1;
		let body = '';
		const closed = selfClosing && (xml || foreign > 0 || FOREIGN.has(name));
		if (FOREIGN.has(name) && !xml && !closed) foreign++;
		if (RAW.has(name) && !closed) {
			const close = new RegExp(String.raw`</${name}[\t\n\f\r />]`, 'gi');
			close.lastIndex = i;
			const e = close.exec(s);
			body = s.slice(i, e ? e.index : n);
			i = e ? e.index : n;
		}
		yield { name, attrs, body };
	}
}

// <link> لا يُحمَّل إلّا إن كان في rel ما يُحمِّل. وهذه قيمُ rel التي لا يحمّل المتصفّح بها شيئًا.
const NOT_LOADED = new Set(['canonical', 'alternate', 'sitemap', 'author', 'license', 'help', 'me', 'bookmark']);
const LINKS = new Set(['a', 'area']);
const CSS_ATTRS = ['style', 'fill', 'stroke', 'filter', 'mask', 'clip-path', 'marker-start', 'marker-mid', 'marker-end', 'cursor'];
/** srcset: عناوين يفصلها فاصلة، ولكلٍّ وصفٌ اختياريّ. @param {string} s */
const srcsetUrls = (s) => s.split(',').map((c) => c.trim().split(/[\t\n\f\r ]+/)[0]).filter(Boolean);

/** @param {string} markup @param {boolean} [xml] @returns {string[]} */
const markupUrls = (markup, xml = false) => {
	const out = [];
	for (const { name, attrs, body } of tags(markup, xml)) {
		const push = (/** @type {string | undefined} */ v) => v !== undefined && out.push(v);
		if (name === 'link') {
			const rels = (attrs.get('rel') ?? '').toLowerCase().split(/[\t\n\f\r ]+/).filter(Boolean);
			if (!rels.length || rels.some((r) => !NOT_LOADED.has(r))) {
				push(attrs.get('href'));
				out.push(...srcsetUrls(attrs.get('imagesrcset') ?? ''));
			}
		} else if (!LINKS.has(name)) {
			push(attrs.get('href'));
			push(attrs.get('xlink:href'));
		}
		for (const k of ['src', 'poster', 'background']) push(attrs.get(k));
		if (name === 'object') push(attrs.get('data'));
		out.push(...srcsetUrls(attrs.get('srcset') ?? ''));
		if (name === 'iframe') out.push(...markupUrls(attrs.get('srcdoc') ?? ''));
		for (const k of CSS_ATTRS) out.push(...cssUrls(attrs.get(k) ?? ''));
		if (name === 'style') out.push(...cssUrls(body));
	}
	return out;
};

/** @param {string} dir @returns {string[]} */
const walk = (dir) =>
	fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
		const p = path.join(dir, e.name);
		return e.isDirectory() ? walk(p) : [p];
	});

/** عدد ومعدوده بالعربيّة. @param {number} n @param {readonly [string, string, string, string, string]} f
 *  الصيغ: المفرد، والمثنّى، والجمع (٣–١٠)، والمفرد المنصوب (١١–٩٩)، والمفرد المجرور (١٠٠ وما بعده).
 *  وما بعد المئات يحكمه آخرُه: ١٠٣ موارد، و١١١ موردًا، و١٠٠ مورد؛ و١٠١ و١٠٢ كالمئة على الشائع في الأرقام. */
const count = (n, [one, two, plural, acc, gen]) => {
	if (n === 1) return `${one} واحد`;
	if (n === 2) return two;
	const r = n % 100;
	if (r >= 3 && r <= 10) return `${n} ${plural}`;
	if (r >= 11) return `${n} ${acc}`;
	return `${n} ${gen}`;
};
const RESOURCE = /** @type {const} */ (['موردٌ', 'موردان', 'موارد', 'موردًا', 'مورد']);
const FILE = /** @type {const} */ (['ملفٌّ', 'ملفّان', 'ملفّات', 'ملفًّا', 'ملفّ']);

if (!fs.existsSync(DIST)) {
	console.error('فحصُ الموارد الخارجيّة: لا مجلّدَ dist/. ابنِ الموقع أوّلًا (npm run build).');
	process.exit(1);
}
const problems = new Set();
let files = 0;
for (const file of walk(DIST)) {
	const ext = path.extname(file).toLowerCase();
	if (ext !== '.html' && ext !== '.css' && ext !== '.svg') continue;
	files++;
	const text = fs.readFileSync(file, 'utf8');
	const urls = ext === '.css' ? cssUrls(text) : markupUrls(text, ext === '.svg');
	for (const u of urls.map(clean)) if (EXTERNAL.test(u)) problems.add(`${path.relative(DIST, file)}: ${u}`);
}
if (!files) {
	console.error('فحصُ الموارد الخارجيّة: لا ملفَّ HTML ولا CSS ولا SVG في dist/. ابنِ الموقع أوّلًا (npm run build).');
	process.exit(1);
}
if (problems.size) {
	console.error(`فحصُ الموارد الخارجيّة: ${count(problems.size, RESOURCE)} من خادم آخر (قرارات الموقع، القرار ٢٠):`);
	for (const p of problems) console.error(`  ${p}`);
	process.exit(1);
}
console.log(`فحصُ الموارد الخارجيّة: ${count(files, FILE)}، ولا موردَ من خادم آخر.`);
