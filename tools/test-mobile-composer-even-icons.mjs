// 输入框底部图标等距排布（DSHA_COMPOSER_EVEN_ICONS_V1）的不变量。
//
// 为什么需要这个文件：tools/apply-mobile-client-patches.mjs:335 的注释写着
// 「门禁：tools/test-mobile-composer-even-icons.mjs 逐项断言这些不变量」，
// 但该文件**从未存在**（BACKLOG §7 的 B2/R-5 记录过同一处遗漏）。
// 于是这套 CSS 长期没有自动化保护：改错了产物也照样出包。
//
// 断言对象是**产物字节**（app/src/main/assets/.../client.js），不是补丁源码，
// 因此它同时验证「补丁确实被应用」和「应用后的形状符合设计」。
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const DEPLOYED = 'app/src/main/assets/builtin-plugins/dsh-web-mobile/lib/client.js';
const source = readFileSync(DEPLOYED, 'utf8');

// 锚点说明：composerEvenIcons 在产物里的位置（实测 237334）**晚于**「DSHA 保留手机搜索」
// （203689），所以不能拿后者当结束锚点 —— 会得到空片段、断言恒假。
// 用「下一个 /* --- 块注释」作为边界（实测 243786，块长 6452）。
const start = source.indexOf('DSHA_COMPOSER_EVEN_ICONS_V1');
assert.notEqual(start, -1, '产物缺少 DSHA_COMPOSER_EVEN_ICONS_V1');
// 回退到该块的注释起点
const blockStart = source.lastIndexOf('/* ---', start);
assert.notEqual(blockStart, -1, '找不到 composerEvenIcons 的块注释起点');
// 结束锚点不能用「下一个 /* --- 」，因为 PUA 那段补丁注释本身就以它开头，
// 会把 PUA 规则切成块外（实测过：8 项过、PUA 项误报失败）。
// 用模板字符串的真正结尾「反引号 + 分号 + 换行」定位。
const blockEnd = source.indexOf('`;\n};\n__modules[', start);
assert.notEqual(blockEnd, -1, '找不到 composerEvenIcons 模板的结尾');
const block = source.slice(blockStart, blockEnd);
assert.ok(block.length > 3000, `composerEvenIcons 块过短（${block.length}），锚点可能错位`);

test('补丁标记存在且媒体查询限定在手机档（不污染桌面）', () => {
  assert.ok(source.includes('DSHA_COMPOSER_EVEN_ICONS_V1'), '缺少补丁标记');
  // 媒体条件必须是 max-width:1023px + pointer:coarse
  assert.match(
    block,
    /@media \(max-width: 1023px\) and \(pointer: coarse\)/,
    '媒体查询不是手机档条件',
  );
});

test('行容器改为等宽网格：grid + 等宽列 + 统一 column-gap/padding', () => {
  // 设计要求：两条车道与 modes/standardControls 摊平到同一行直接网格项
  assert.match(block, /display: grid !important/, '未改为 grid');
  assert.match(block, /grid-auto-flow: column/, '不是单行网格');
  assert.match(
    block,
    /grid-auto-columns: minmax\(0, 1fr\)/,
    '列宽不是等宽 minmax(0,1fr)',
  );
  // 列间距与左右 padding 取同一个值，才能保证「首尾留白 == 列间距」
  const gap = block.match(/column-gap: (\d+)px !important/);
  const padL = block.match(/padding-left: (\d+)px !important/);
  const padR = block.match(/padding-right: (\d+)px !important/);
  assert.ok(gap && padL && padR, '缺少 column-gap / padding-left / padding-right');
  assert.equal(gap[1], padL[1], 'column-gap 与 padding-left 不相等');
  assert.equal(gap[1], padR[1], 'column-gap 与 padding-right 不相等');
  assert.equal(gap[1], '8', '间距应为 8px（设计稿定值）');
});

test('两条车道与 modes/standardControls 都要 display:contents（真正摊平）', () => {
  // 只要漏掉任一选择器，对应车道就会退回「按内容宽度分配」，等距立刻失效
  for (const cls of ['_tools', '_trailing', '_modes', '_standardControls']) {
    const re = new RegExp(
      `\\[class\\*="${cls}"\\][^{]*\\{[^}]*display: contents !important`,
      's',
    );
    assert.match(block, re, `${cls} 未设为 display:contents`);
  }
});

test('网格项必须 min-width:0 + overflow:hidden（否则长文案撑破等宽）', () => {
  assert.match(block, /min-width: 0 !important/, '缺 min-width:0');
  assert.match(block, /max-width: none !important/, '缺 max-width:none');
  assert.match(block, /overflow: hidden/, '缺 overflow:hidden');
  assert.match(block, /box-sizing: border-box/, '缺 box-sizing:border-box');
});

test('文字标签收成图标：triggerLabel / triggerEffort 必须隐藏', () => {
  // 这是「宽度不再随文案/语言变化」的关键
  for (const cls of ['_triggerLabel', '_triggerEffort']) {
    const re = new RegExp(
      `\\[class\\*="${cls}"\\][^{]*\\{[^}]*display: none !important`,
      's',
    );
    assert.match(block, re, `${cls} 未隐藏`);
  }
  assert.match(
    block,
    /--dsh-composer-model-text-display: none/,
    '模型文字未关闭',
  );
  assert.match(
    block,
    /--dsh-composer-model-icon-display: block/,
    '模型图标未打开',
  );
});

test('触发键占满整列且高度固定 34px（保证与发送键同一基线）', () => {
  const trigger = block.match(/\[class\*="_trigger"\]\s*\{[^}]*\}/s);
  assert.ok(trigger, '缺少 _trigger 规则');
  assert.match(trigger[0], /width: 100% !important/);
  assert.match(trigger[0], /height: 34px !important/);
  assert.match(trigger[0], /justify-content: center !important/);
  assert.match(trigger[0], /gap: 0 !important/);
});

test('发送键容器高度也是 34px（否则行高被最高的那个撑起）', () => {
  const primary = block.match(/\[class\*="_primary"\]\s*\{[^}]*\}/s);
  assert.ok(primary, '缺少 _primary 规则');
  assert.match(primary[0], /height: 34px !important/);
});

test('空的活动位必须折叠，不能占掉一列', () => {
  // 否则 _activity 为空时仍占一格，把 7 个控件挤成 8 列
  assert.match(
    block,
    /\[class\*="_activity"\]:empty/,
    '缺少 _activity:empty 折叠规则',
  );
  assert.match(block, /\[hidden\]\s*\{\s*display: none !important/, '缺少 [hidden] 折叠');
});

test('PUA 第三方药丸也被纳入网格（2026-11-10 补，方案 A）', () => {
  // @michengai/dsh-pua 在 composer 里注入 .pua-composer/.pua-trigger，
  // 它们是文字药丸（~130px），且不受宿主类名选择器覆盖 —— 若不单独约束，
  // 等距网格里会单独撑宽一列。此处断言补丁显式纳入它。
  assert.match(block, /\.pua-composer/, '未纳入 .pua-composer 容器');
  assert.match(block, /\.pua-trigger/, '未纳入 .pua-trigger 药丸');
  // 药丸必须与宿主控件同高（34px），否则整行基线被拉偏
  // 注意：注释里也提到 ".pua-trigger 按钮"，所以必须匹配「选择器行末尾紧跟 {」的那个，
  // 而不是注释中的任意提及。用行首（两个空格缩进）+ 选择器 + 空白 + { 定位。
  const puaTrigger = block.match(/^  \[[^\n]*\.pua-trigger \{[^}]*\}/m);
  assert.ok(puaTrigger, '缺少 .pua-trigger 规则');
  assert.match(puaTrigger[0], /height: 34px !important/, 'PUA 药丸高度不是 34px');
  assert.match(puaTrigger[0], /width: 100% !important/, 'PUA 药丸未占满整列');
});
