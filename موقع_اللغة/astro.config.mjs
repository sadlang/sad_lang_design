// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { SECTIONS } from './src/lib/systems.mjs';
import { BASE, SITE } from './src/lib/site.mjs';

// كلُّ قسمٍ مدخلٌ ثمّ مجموعاتُه، أو يُولَّد كلُّه من مجلّده. والأقسامُ في src/lib/systems.mjs.
/** @typedef {{ label: string, dir: string, groups?: Group[] }} Group */
/** @param {string} base @param {Group} g @returns {any} */
const group = (base, g) => {
	const dir = `${base}/${g.dir}`;
	return {
		label: g.label,
		items: g.groups
			? [{ label: 'مدخل', link: `/${dir}/` }, ...g.groups.map((x) => group(dir, x))]
			: [{ autogenerate: { directory: dir } }],
	};
};
/** @param {Group} s */
const section = (s) => ({
	label: s.label,
	collapsed: true,
	items: s.groups
		? [{ label: 'مدخل', link: `/${s.dir}/` }, ...s.groups.map((g) => group(s.dir, g))]
		: [{ autogenerate: { directory: s.dir } }],
});

// الخطوطُ مستضافةٌ مع الموقع (@fontsource)، لا من Google Fonts (قرارات الموقع، القرار ٢٠).
/** @param {string} pkg @param {number[]} weights */
const font = (pkg, weights) => weights.map((w) => `@fontsource/${pkg}/${w}.css`);
const FONTS = [
	...font('ibm-plex-sans-arabic', [400, 500, 600, 700]),
	...font('noto-naskh-arabic', [400, 600, 700]),
	...font('ibm-plex-mono', [400, 500]),
];

// يُنشر على GitHub Pages تحت اسم المستودع، فكلُّ رابطٍ داخليٍّ في المحتوى نسبيّ لا يبدأ بـ/ (قرارات الموقع، القرار ٢٤).
export default defineConfig({
	site: SITE,
	base: BASE,
	integrations: [
		starlight({
			title: 'لغة ص',
			description: 'توثيق لغة ص',
			logo: { src: './src/assets/logo.svg' },
			favicon: '/favicon.svg',
			// صفحةُ ٤٠٤ من src/content/docs/404.md، فلا حاجةَ لمسار Starlight الافتراضيّ.
			disable404Route: true,
			defaultLocale: 'root',
			locales: { root: { label: 'العربية', lang: 'ar', dir: 'rtl' } },
			customCss: [...FONTS, './src/styles/theme.css'],
			components: { PageTitle: './src/components/PageTitle.astro' },
			routeMiddleware: './src/routeData.ts',
			tableOfContents: { minHeadingLevel: 2, maxHeadingLevel: 3 },
			sidebar: SECTIONS.map(section),
		}),
	],
});
