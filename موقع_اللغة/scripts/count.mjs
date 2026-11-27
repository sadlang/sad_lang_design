// عددٌ ومعدودُه بالعربيّة، تشترك فيه سكربتات الفحص.
/** عدد ومعدوده بالعربيّة. @param {number} n @param {readonly [string, string, string, string, string]} f
 *  الصيغ: المفرد، والمثنّى، والجمع (٣–١٠)، والمفرد المنصوب (١١–٩٩)، والمفرد المجرور (١٠٠ وما بعده).
 *  وما بعد المئات يحكمه آخرُه: ١٠٣ موارد، و١١١ موردًا، و١٠٠ مورد؛ و١٠١ و١٠٢ كالمئة على الشائع في الأرقام. */
export const count = (n, [one, two, plural, acc, gen]) => {
	if (n === 1) return `${one} واحد`;
	if (n === 2) return two;
	const r = n % 100;
	if (r >= 3 && r <= 10) return `${n} ${plural}`;
	if (r >= 11) return `${n} ${acc}`;
	return `${n} ${gen}`;
};
