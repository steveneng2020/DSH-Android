// 聊天主界面顶栏「图标垂直对齐 + 水平不重叠」（DSHA_HEADER_ALIGN_V1）的不变量。
//
// 为什么需要这个文件：tools/apply-mobile-client-patches.mjs:122 的注释写着
// 「门禁：tools/test-mobile-header-align.mjs 逐项断言垂直极差/墨迹极差/水平间隙」，
// 但该文件**从未存在**（git log --all 为空，BACKLOG §7 的 B2/R-9 记录过同一处遗漏）。
// 于是这套顶栏 CSS 同样长期裸奔。
//
// 断言对象是产物字节（app/src/main/assets/.../client.js），同时验证
// 「补丁被应用」与「应用后的形状符合设计」。
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source = readFileSync(
  'app/src/main/assets/builtin-plugins/dsh-web-mobile/lib/client.js',
  'utf8',
);

const START = 'DSHA_HEADER_ALIGN_V1';
const start = source.indexOf(START);
assert.notEqual(start, -1, '产物缺少 DSHA_HEADER_ALIGN_V1');

// 块边界：从本块注释起点，到该模板字符串结尾（反引号 + 分号 + 下一个 __modules）
const blockStart = source.lastIndexOf('/* ---', start);
assert.notEqual(blockStart, -1, '找不到 headerAlign 块注释起点');
const blockEnd = source.indexOf('`;\n};', start);
assert.notEqual(blockEnd, -1, '找不到 headerAlign 模板结尾');
const block = source.slice(blockStart, blockEnd);
assert.ok(block.length > 2000, `headerAlign 块过短（${block.length}）`);

test('补丁限定在手机档（不污染桌面/平板）', () => {
  assert.match(block, /@media \(max-width: 1023px\) and \(pointer: coarse\)/);
});

test('第一行统一 28dp 盒高（任何一项更高都会把整行顶高 2~3dp）', () => {
  // 谱系 chip 的 28px 约束
  const chip = block.match(/\[class\*="ZKlsPq_root"\][^{]*\{[^}]*\}/s);
  assert.ok(chip, '缺少谱系 chip 规则');
  assert.match(chip[0], /height: 28px !important/);
  assert.match(chip[0], /min-height: 28px !important/);
  assert.match(chip[0], /max-height: 28px !important/);
  // 动作行每一项
  const actions = block.match(/\[class\*="_headerActions"\] > \*\s*\{[^}]*\}/s);
  assert.ok(actions, '缺少 _headerActions > * 规则');
  assert.match(actions[0], /max-height: 28px !important/);
});

test('谱系 chip 从标签行搬回标题行内联（position 归零）', () => {
  // 改造前是 position:absolute + bottom:0，落点在标签行，比标题行低 28dp
  const chip = block.match(/\[class\*="ZKlsPq_root"\]:not\(\[class\*="_switcherRoot"\]\)\s*\{[^}]*\}/s);
  assert.ok(chip, '缺少谱系 chip 的内联规则');
  assert.match(chip[0], /position: static !important/);
  assert.match(chip[0], /bottom: auto !important/);
  assert.match(chip[0], /left: auto !important/);
  assert.match(chip[0], /right: auto !important/);
});

test('标题 crumb 单行省略，不换行', () => {
  const crumb = block.match(/\[class\*="_crumbCurrent"\]\s*\{[^}]*\}/s);
  assert.ok(crumb, '缺少 _crumbCurrent 规则');
  assert.match(crumb[0], /text-overflow: ellipsis !important/);
  assert.match(crumb[0], /white-space: nowrap !important/);
  assert.match(crumb[0], /overflow: hidden !important/);
});

test('标题簇让出右上角 34px 文件按钮座位', () => {
  // 实测 en/360/全 chip：团队 chip 右缘 347.8 > 按钮左缘 326
  const cluster = block.match(/\[class\*="_titleCluster"\]\s*\{[^}]*margin-right[^}]*\}/s);
  assert.ok(cluster, '缺少 _titleCluster 的 margin-right 规则');
  assert.match(cluster[0], /margin-right: 34px !important/);
});

test('动作行有明确水平间距（2026-11-10 补，原先只统一行高、没约束间距）', () => {
  const row = block.match(/\[class\*="_headerActions"\]\s*\{[^}]*column-gap[^}]*\}/s);
  assert.ok(row, '缺少 _headerActions 的 column-gap 规则');
  assert.match(row[0], /column-gap: 8px !important/);
  assert.match(row[0], /display: flex !important/);
  assert.match(row[0], /align-items: center !important/);
});

test('动作项不收缩、不吃额外 margin（间距只由 gap 决定，避免双重计算）', () => {
  const items = block.match(/\[class\*="_headerActions"\] > \*\s*\{[^}]*margin-left[^}]*\}/s);
  assert.ok(items, '缺少 _headerActions > * 的 margin 归零规则');
  assert.match(items[0], /flex: 0 0 auto !important/);
  assert.match(items[0], /margin-left: 0 !important/);
  assert.match(items[0], /margin-right: 0 !important/);
});

test('标题簇内部也有 gap，最后一项不贴到动作行', () => {
  const clusterGap = block.match(/\[class\*="_titleCluster"\]\s*\{[^}]*column-gap[^}]*\}/s);
  assert.ok(clusterGap, '缺少 _titleCluster 的 column-gap 规则');
  assert.match(clusterGap[0], /column-gap: 6px !important/);
});
