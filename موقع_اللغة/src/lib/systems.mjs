// المصدرُ الوحيد لأقسام الموقع: القائمةُ الجانبيّة، وبطاقاتُ الصفحة الرئيسيّة، وأين تظهر شاراتُ الحالة.
// المحورُ الأوّل القارئ (تعلّم · مرجع · مفاهيم · مكتبة · مترجم)، والمحورُ الثاني الموضوع.
// لإضافة قسم: أضِفه هنا، ثمّ أنشئ مجلّده في src/content/docs وفيه index.mdx.
//   dir:       مجلّدُ القسم في src/content/docs.
//   reader:    لمن القسم، ويظهر في بطاقته.
//   statusful: صفحاتُه تملك قراراتٍ فتحمل <قسم حالة="…"> وشاراتِ الحالة.
//              true للقسم كلّه، أو مسارٌ فرعيٌّ فيه وحده (في المترجم: reference).
//   groups:    إن وُجدت قُسّم القسمُ مجموعاتٍ، كلٌّ منها مجلّدٌ فرعيّ. وللمجموعة groups أيضًا.
//              وإن غابت وُلِّد القسمُ (أو المجموعة) كلُّه من مجلّده.
export const SECTIONS = [
	{ dir: 'learn', label: 'تعلّم ص', reader: 'للمتعلّم', statusful: false },
	{
		dir: 'reference',
		label: 'مرجع اللغة',
		reader: 'للمبرمج',
		statusful: true,
		groups: [
			{ dir: 'lexical', label: 'المعجم والمعرّفات' },
			{ dir: 'declarations', label: 'التعريفات' },
			{ dir: 'statements', label: 'الجمل والتحكّم' },
			{ dir: 'expressions', label: 'التعبيرات' },
			{ dir: 'functions', label: 'الدوالّ والمغلقات' },
			{ dir: 'failure', label: 'الفشل والخلل' },
			{ dir: 'types', label: 'الأنواع المدمجة' },
			{ dir: 'modules', label: 'الوحدات والحزم' },
			// لكلّ عائلة أخطاءٍ تبويبٌ ومجلّدٌ باسم ملفّها في data/errors/ من مستودع المترجم (قرارُ المالك ٢٠٢٦-١١-٢٧).
			{
				dir: 'errors',
				label: 'رسائل الأخطاء',
				groups: [
					{ dir: 'files', label: 'ملفات' },
					{ dir: 'compiler', label: 'مترجم' },
				],
			},
		],
	},
	{
		dir: 'concepts',
		label: 'المفاهيم',
		reader: 'للمبرمج',
		statusful: true,
		groups: [
			{ dir: 'ownership', label: 'الملكية' },
			{ dir: 'types', label: 'الأنواع' },
		],
	},
	{ dir: 'library', label: 'المكتبة', reader: 'للمبرمج', statusful: true },
	{
		dir: 'compiler',
		label: 'المترجم',
		reader: 'للمساهم',
		statusful: 'reference',
		groups: [
			{ dir: 'guide', label: 'الدليل' },
			{
				dir: 'reference',
				label: 'المرجع',
				groups: [
					{ dir: 'decisions', label: 'قرارات التطوير' },
					{ dir: 'internals', label: 'الأنظمة الداخلية' },
					{ dir: 'standards', label: 'معايير الشفرة والجودة' },
				],
			},
		],
	},
];

/** القسمُ من معرّف الصفحة: reference/declarations/variable ← reference. @param {string} id */
export const sectionOf = (id) => id.split('/')[0];

/** هل تملك الصفحةُ قراراتٍ فتحمل شاراتِ الحالة؟ @param {string} id */
export const isStatusful = (id) => {
	const s = SECTIONS.find((x) => x.dir === sectionOf(id));
	if (!s) return false;
	if (typeof s.statusful === 'string') return id === `${s.dir}/${s.statusful}` || id.startsWith(`${s.dir}/${s.statusful}/`);
	return s.statusful;
};
