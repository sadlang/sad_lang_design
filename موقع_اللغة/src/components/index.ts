// مكوّناتُ الكتابة. تُستورد في ملفّات .mdx:
// import { قسم, شارة, ستتعلم, جرب, خلاصة, قيد_النقاش } from '~/components';
// وحكمُ المترجم يُكتب على كتلة الشفرة نفسها: ```ص حكم=تترجم  أو  ```ص حكم=خطأ
export { default as قسم } from './Section.astro';
export { default as شارة } from './StatusBadge.astro';
export { default as ستتعلم } from './Learn.astro';
export { default as جرب } from './Try.astro';
export { default as خلاصة } from './Summary.astro';
export { default as قيد_النقاش } from './UnderDiscussion.astro';
