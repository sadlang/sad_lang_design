// حالاتُ القرارات. الترتيبُ من الأضعف إلى الأقوى، وحالةُ الصفحة أضعفُ حالةٍ فيها.
import { isStatusful } from './systems.mjs';

export const STATUSES = {
	'لم_يعالج': { key: 'none', sym: '○', label: 'لم يُعالَج', variant: 'default', rank: 0 },
	'مفتوح': { key: 'open', sym: '؟', label: 'مفتوح', variant: 'caution', rank: 1 },
	'مؤجل': { key: 'hold', sym: '‖', label: 'مؤجَّل', variant: 'tip', rank: 2 },
	'مقترح': { key: 'prop', sym: '◇', label: 'مقترح', variant: 'note', rank: 3 },
	'معتمد': { key: 'ok', sym: '✓', label: 'معتمد', variant: 'success', rank: 4 },
} as const;

export type Status = keyof typeof STATUSES;

/** where: مسارُ الملفّ، ليُذكر في رسالة الخطأ. */
export function statusOf(name: string | undefined, where = '') {
	const s = STATUSES[name as Status];
	if (!s) throw new Error(`${where ? where + ': ' : ''}حالةٌ غير معروفة: «${name ?? '(بلا حالة)'}». المسموح: ${Object.keys(STATUSES).join('، ')}`);
	return s;
}

/** يحذف ما لا يُعرض قسمًا: كتلَ الشفرة المسوّرة، والشفرةَ داخل السطر، وتعليقاتِ MDX وHTML. */
const stripNonContent = (s: string) =>
	s
		.replace(/^[ \t]*(`{3,}|~{3,})[^\n]*\n[\s\S]*?^[ \t]*\1[ \t]*$/gm, '')
		.replace(/\{\/\*[\s\S]*?\*\/\}/g, '')
		.replace(/<!--[\s\S]*?-->/g, '')
		.replace(/`[^`\n]*`/g, '');

// <قسم حالة="…"> بأيّ تنصيص: "…" أو '…' أو {"…"}، ولو امتدّت خصائصُه على أسطر.
// \b لا يصلح هنا: لا يعدّ الحروفَ العربيّة حروفَ كلمة.
const SECTION = /<قسم(?=[\s>\/])(?:[^>"'{]|"[^"]*"|'[^']*'|\{[^}]*\})*?حالة\s*=\s*(?:"([^"]*)"|'([^']*)'|\{\s*["']([^"']*)["']\s*\})/g;

/** حالاتُ أقسام الصفحة كما كُتبت في <قسم حالة="…">. */
export function sectionStatuses(body: string, where = ''): Status[] {
	return [...stripNonContent(body).matchAll(SECTION)].map((m) => {
		const v = m[1] ?? m[2] ?? m[3];
		statusOf(v, where);
		return v as Status;
	});
}

/** أضعفُ حالةٍ في الصفحة، أو لا شيء إن لم يكن فيها قسمٌ ذو حالة. */
export function pageStatus(body: string, where = ''): Status | undefined {
	const all = sectionStatuses(body, where);
	if (!all.length) return undefined;
	return all.reduce((a, b) => (STATUSES[b].rank < STATUSES[a].rank ? b : a));
}

/** هل تملك الصفحةُ قراراتٍ فتحمل شاراتِ الحالة؟ (المرجع، والمفاهيم، والمكتبة، ومرجعُ المترجم) */
export { isStatusful };
