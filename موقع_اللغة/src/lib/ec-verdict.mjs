// إضافةٌ لـExpressive Code: رأسٌ لكلّ كتلة شفرة ص فيه «شفرة ص»، وحكمُ المترجم إن كُتب:
//   ```ص حكم=تترجم      ← ✓ تُترجَم
//   ```ص حكم=خطأ        ← ✗ خطأُ ترجمة
//   ```ص حكم=خطأ:200014 ← ✗ خطأُ ترجمة 200014 (رمزُ الخطأ، ق‑٦: ستُّ خاناتٍ لاتينيّة، والعربيّةُ تُقبل وتُحوَّل)
import { definePlugin } from '@expressive-code/core';
import { h, select } from '@expressive-code/core/hast';

const VERDICTS = {
	'تترجم': { cls: 'sad-ok', text: '✓ تُترجَم' },
	'خطأ': { cls: 'sad-err', text: '✗ خطأُ ترجمة' },
};

export function pluginVerdict() {
	const verdicts = new WeakMap();
	return definePlugin({
		name: 'sad-verdict',
		hooks: {
			preprocessMetadata: ({ codeBlock }) => {
				if (codeBlock.language !== 'ص') return;
				if (!codeBlock.props.title) codeBlock.props.title = 'شفرة ص';
				const raw = codeBlock.metaOptions.getString('حكم');
				if (raw === undefined) return;
				const [v, code] = raw.split(':');
				if (!VERDICTS[v]) throw new Error(`حكمٌ غير معروف: «${raw}». المسموح: ${Object.keys(VERDICTS).join('، ')}`);
				if (code === undefined) return void verdicts.set(codeBlock, VERDICTS[v]);
				const latin = code.replace(/[٠-٩]/g, (d) => String(d.charCodeAt(0) - 0x0660));
				if (v !== 'خطأ' || !/^[1-9][0-9]{5}$/.test(latin))
					throw new Error(`رمزُ خطأٍ غير صالح: «${raw}». الصيغة: حكم=خطأ:200014 (ستُّ خانات، والعائلةُ من 100)`);
				verdicts.set(codeBlock, { ...VERDICTS[v], text: `${VERDICTS[v].text} ${latin}` });
			},
			postprocessRenderedBlock: ({ codeBlock, renderData }) => {
				const v = verdicts.get(codeBlock);
				if (!v) return;
				const header = select('figcaption.header', renderData.blockAst);
				if (!header) return;
				header.children.push(h('span', { className: ['sad-verdict', v.cls], 'data-pagefind-ignore': '' }, v.text));
			},
		},
	});
}
