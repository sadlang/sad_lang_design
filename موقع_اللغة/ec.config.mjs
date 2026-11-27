// @ts-check
// إعدادُ كتل الشفرة (Expressive Code). مستقلٌّ عن astro.config.mjs لأنّ فيه إضافات.
import { defineEcConfig } from '@astrojs/starlight/expressive-code';
import { pluginLineNumbers } from '@expressive-code/plugin-line-numbers';
import { pluginVerdict } from './src/lib/ec-verdict.mjs';

export default defineEcConfig({
	themes: ['github-dark', 'github-light'],
	// لا قواعدَ تلوينٍ لـص بعد؛ تُكتب الشفرةُ ```ص وتُعرض نصًّا إلى أن تُولَّد من ملفّ الكلمات (قرارات الموقع، القرار ٢١).
	// و```خرج نصٌّ عربيٌّ من اليمين بلا تلوين، كخرج المترجم في الطرفيّة.
	shiki: { langAlias: { 'ص': 'txt', 'خرج': 'txt', 'ebnf': 'txt' } },
	plugins: [pluginLineNumbers(), pluginVerdict()],
	// أرقامُ الأسطر لشفرة ص وحدها، ويُطفئها ```ص showLineNumbers=false
	defaultProps: { showLineNumbers: false, overridesByLang: { 'ص': { showLineNumbers: true } } },
	styleOverrides: { codeFontFamily: "'IBM Plex Mono', 'IBM Plex Sans Arabic', monospace", borderRadius: '10px' },
});
