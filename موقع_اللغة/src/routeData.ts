// يضع شارةَ حالة الصفحة (أضعفَ حالةٍ في أقسامها) بجانب كلّ صفحةٍ تملك قراراتٍ في القائمة الجانبيّة.
import { defineRouteMiddleware, type StarlightRouteData } from '@astrojs/starlight/route-data';
import { getCollection } from 'astro:content';
import { STATUSES, isStatusful, pageStatus } from './lib/status';

const base = import.meta.env.BASE_URL.replace(/\/+$/, '');
const norm = (p: string) =>
	decodeURI(p.startsWith(base + '/') ? p.slice(base.length) : p)
		.replace(/^\/+|\/+$/g, '')
		.replace(/(^|\/)index$/, '');

// تُحسب الحالاتُ مرّةً واحدةً في البناء، وفي كلّ طلبٍ أثناء التطوير ليظهر التعديلُ فورًا.
const load = async () => {
	const m = new Map<string, ReturnType<typeof pageStatus>>();
	for (const e of await getCollection('docs')) {
		if (isStatusful(e.id)) m.set(norm(e.id), pageStatus(e.body ?? '', e.filePath ?? e.id));
	}
	return m;
};
let cache: ReturnType<typeof load> | undefined;
const statuses = () => (import.meta.env.DEV ? load() : (cache ??= load()));

export const onRequest = defineRouteMiddleware(async (context) => {
	const byId = await statuses();
	const walk = (entries: StarlightRouteData['sidebar']) => {
		for (const e of entries) {
			if (e.type === 'group') walk(e.entries);
			else {
				const st = byId.get(norm(e.href));
				if (st) {
					const s = STATUSES[st];
					e.badge = { text: s.sym, variant: s.variant, class: `sad-badge sad-${s.key}` };
					e.attrs = { ...e.attrs, title: `حالة الصفحة: ${s.label}`, 'aria-label': `${e.label}، حالة الصفحة: ${s.label}` };
				}
			}
		}
	};
	walk(context.locals.starlightRoute.sidebar);
});
