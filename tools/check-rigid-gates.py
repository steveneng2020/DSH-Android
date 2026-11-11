#!/usr/bin/env python3
"""刚性门禁：把 2026-11-10 ~ 11-11 两天踩过的坑做成机器检查。

## 为什么需要这个脚本

`docs/LESSONS-LEARNED.md` 是**叙述性**台账，写了教训但不会拦住任何人；
`docs/DATA-SOURCES.md` 只登记数字，不判断对错。两天里反复出现同一类问题：

  「检查写了但没跑」「记录与实物不符」「上游内容当自家内容」

它们都不是靠记住就能避免的 —— 必须由脚本在每次提交/发布前强制拦。

## 检查项（每条都对应一次真实事故，编号见 docs/RIGID-GATES.md）

G01 更新记录三面 + updates.json notes 一致（防止「更新日记没有了」）
G02 updates.json 的 sha256/bytes 必须等于本机构建产物（防止发布无法复现的包）
G03 Release 正文结构（防止换行丢失导致 Markdown 塌成一行、字体异常）
G04 工具链里的 check-*.py 必须真被调用（防止「检查存在但从不执行」）
G05 交接文档提到的文件必须存在（防止「保护不存在的 F 类文件」）
G06 上游身份关键词黑名单（防止包名/证书/本机路径混入自家文档）
G07 gpl-binaries.lock.json 与磁盘二进制一致（防止 GPL 溯源失效）
G08 无畸形 git ref（防止 filter-repo 残留）
G09 文档内同一数字不得自相矛盾（防止 278.66 vs 279.77）
G10 版本号三处一致（build.gradle / updates.json / 更新记录首条）

## 跑法

    python3 tools/check-rigid-gates.py            # 全部
    python3 tools/check-rigid-gates.py --list     # 只列 gate 编号与标题
    python3 tools/check-rigid-gates.py --json     # 机器可读

退出码 0 = 全过；非 0 = 有 FAIL。
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WS = ROOT.parent  # 工作区根（含 HANDOFF 等非仓库文件）

# 上游 DSH-APP/DSHA 的身份指纹；出现在自家文档里（且未标注是上游）即视为残留。
UPSTREAM_MARKERS = (
    'dsh.android.client',
    'com.dsh.client',
    'E7E3',
    'code190',
)
# 允许出现这些词的文件夹（历史材料、第三方声明、审计台账）。
UPSTREAM_ALLOWED = (
    'docs/history/',
    'docs/audits/',
    'THIRD_PARTY_NOTICES.md',
    'GPL-SOURCE-OFFER.md',
    'LICENSE',
    'SECURITY.md',
    'AGENTS.md',
    'AGENTS.en.md',
    'BUILD.md',
    'BUILD.en.md',
    'CONTRIBUTING.md',
    'CONTRIBUTING.en.md',
    'UPDATES-HOWTO.md',
)

GATES = []


def gate(code, title):
    def register(fn):
        GATES.append((code, title, fn))
        return fn
    return register


def read(path):
    try:
        return path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return ''


def sh(args, cwd=ROOT):
    try:
        return subprocess.check_output(args, cwd=cwd, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ''


# ---------------------------------------------------------------- G01
@gate('G01', '更新记录三面 + updates.json notes 一致')
def g01():
    script = ROOT / 'tools/check-changelog-sync.py'
    if not script.is_file():
        return ['CHANGELOG_SYNC_SCRIPT_MISSING: tools/check-changelog-sync.py']
    code = subprocess.run([sys.executable, '-B', str(script), '--check'],
                          cwd=ROOT, capture_output=True, text=True)
    if code.returncode != 0:
        return ['CHANGELOG_SYNC_FAILED: ' + (code.stdout or code.stderr).strip()[:400]]
    return []


# ---------------------------------------------------------------- G02
@gate('G02', 'updates.json 的 sha256/bytes 等于本机构建产物')
def g02():
    apk = ROOT / 'app/build/outputs/apk/standard/release/app-standard-release.apk'
    updates = ROOT / 'updates.json'
    if not apk.is_file():
        return ['APK_MISSING: 先构建 assembleStandardRelease（%s）' % apk]
    if not updates.is_file():
        return ['UPDATES_JSON_MISSING']
    artifact = json.loads(read(updates))['releases'][0]['artifacts'][0]
    digest = hashlib.sha256(apk.read_bytes()).hexdigest()
    problems = []
    if artifact['sha256'] != digest:
        problems.append('UPDATES_SHA_MISMATCH: updates.json 登记 %s，实际产物 %s'
                        % (artifact['sha256'], digest))
    if artifact['bytes'] != apk.stat().st_size:
        problems.append('UPDATES_BYTES_MISMATCH: 登记 %s，实际 %s'
                        % (artifact['bytes'], apk.stat().st_size))
    return problems


# ---------------------------------------------------------------- G03
@gate('G03', 'Release 正文 Markdown 结构完整')
def g03():
    """防止「换行丢失 → 表格塌成一行 → 手机上看字体异常大」（2026-11-11 实际事故）。"""
    candidates = [WS / '.release-body.py', ROOT / 'tools/release-body.py']
    script = next((p for p in candidates if p.is_file()), None)
    if script is None:
        return []  # 没有生成器就不判（不制造假红）
    code = subprocess.run([sys.executable, '-B', str(script), '--check'],
                          cwd=script.parent, capture_output=True, text=True)
    if code.returncode != 0:
        return ['RELEASE_BODY_DEGRADED: ' + (code.stdout or code.stderr).strip()[:400]]
    return []


# ---------------------------------------------------------------- G04
@gate('G04', 'tools 下的 check-*.py 必须真被调用')
def g04():
    """2026-11-11 实际事故：check-changelog-sync.py 写好了但没人调用，
    也没提交，等于不存在，v1.1 的更新记录漂了一整个版本。"""
    # 2026-11-11 教训：第一版只查了 CI 与 verify-stability，漏掉 app/build.gradle，
    # 于是把两个真正由构建期调用的门禁误报成「从未执行」。
    callers = [
        ROOT / 'tools/verify-stability.py',
        ROOT / '.github/workflows/ci-fast.yml',
        ROOT / '.github/workflows/ci-package.yml',
        ROOT / '.github/workflows/release.yml',
        ROOT / 'build.sh',
        ROOT / 'app/build.gradle',
        ROOT / 'build.gradle',
    ]
    haystack = '\n'.join(read(p) for p in callers)
    problems = []
    for script in sorted((ROOT / 'tools').glob('check-*.py')):
        name = script.name
        # 本脚本自身与其被 G01 直接调用的情况不算遗漏
        if name == 'check-rigid-gates.py':
            continue
        if name in haystack:
            continue
        problems.append('CHECK_NEVER_CALLED: tools/%s 没有被 ci-fast / verify-stability / build.sh 调用'
                        % name)
    return problems


# ---------------------------------------------------------------- G05
@gate('G05', '交接文档提到的源文件必须存在')
def g05():
    """2026-11-11 实际事故：HANDOFF/MEMORY 写「F 类 = WebLifecycleController.java 等」，
    这三个文件根本不存在，后来者可能据此去「保护」或「回滚」。"""
    docs = [WS / 'docs/HANDOFF-新会话.md', WS / 'MEMORY.md', ROOT / 'docs/交接规程.md']
    problems = []
    pattern = re.compile(r'`([A-Za-z0-9_./-]+\.(?:java|py|mjs|cjs|json|md))`')
    for doc in docs:
        if not doc.is_file():
            continue
        for lineno, line in enumerate(read(doc).split('\n'), 1):
            # 只查「明确说这些文件在某个分类下」的段落，避免误报普通提及
            if not re.search(r'(F 类|G 类|改动|源码改动)', line):
                continue
            for name in pattern.findall(line):
                if name.startswith(('http', 'docs/', 'tools/', 'app/src/main/res')):
                    continue
                if (ROOT / name).exists():
                    continue
                problems.append('HANDOFF_PHANTOM_FILE: %s:%d 提到 `%s`，但仓库里不存在'
                                % (doc.name, lineno, name))
    return problems


# ---------------------------------------------------------------- G06
@gate('G06', '上游身份指纹不得混入自家文档')
def g06():
    """只查「面向用户的现行文档」。

    2026-11-11 教训：第一版扫全仓 *.md，报出 322 条 —— 绝大部分是 docs/releases/
    与 bug/ 下的上游历史记录，那些本来就该保留上游痕迹。门禁范围划错会
    制造大量假红，反而让人忽略真正的泄漏。
    """
    targeted = [
        'README.md', 'README.en.md',
        'AGENTS.md', 'AGENTS.en.md',
        'BUILD.md', 'BUILD.en.md',
        'CONTRIBUTING.md', 'CONTRIBUTING.en.md',
        'UPDATES-HOWTO.md', 'CHANGELOG.md',
        'GPL-SOURCE-OFFER.md',
        'docs/update.md', 'docs/en/update.md',
        'docs/接手指南.md',
        'docs/documentation-index.md',
        'docs/en/index.md',
    ]
    problems = []
    for rel in targeted:
        path = ROOT / rel
        if not path.is_file():
            continue
        if rel in UPSTREAM_ALLOWED:
            continue
        text = read(path)
        for marker in UPSTREAM_MARKERS:
            for lineno, line in enumerate(text.split('\n'), 1):
                if marker not in line:
                    continue
                # 该行若明确把标记归给上游，属于正确的对照说明，放行
                if '上游' in line or 'upstream' in line.lower():
                    continue
                problems.append('UPSTREAM_MARKER_LEAK: %s:%d 出现 `%s`，且未标注属上游'
                                % (rel, lineno, marker))
    return problems


# ---------------------------------------------------------------- G07
@gate('G07', 'GPL 二进制溯源锁与磁盘一致')
def g07():
    script = ROOT / 'tools/check-proot-provenance.py'
    if not script.is_file():
        return ['PROVENANCE_SCRIPT_MISSING']
    code = subprocess.run([sys.executable, '-B', str(script)],
                          cwd=ROOT, capture_output=True, text=True)
    if code.returncode != 0:
        return ['PROVENANCE_FAILED: ' + (code.stdout or code.stderr).strip()[:400]]
    return []


# ---------------------------------------------------------------- G08
@gate('G08', 'git ref 无畸形名与孤立 recovered/remotes')
def g08():
    """2026-11-11 实际事故：filter-repo 后残留 refs/recovered/*、refs/remotes/*，
    还把 refs/recovered/tags/* 变成了 28 个畸形 tag（refs/tags/refs/recovered/tags/*）。"""
    problems = []
    refs = sh(['git', 'for-each-ref', '--format=%(refname)']).split('\n')
    for ref in filter(None, refs):
        if ref.startswith('refs/tags/refs/'):
            problems.append('MALFORMED_TAG_REF: %s（tag 名里嵌了 refs/ 路径）' % ref)
        elif ref.startswith('refs/recovered/') or ref.startswith('refs/backup/'):
            problems.append('STALE_LOCAL_REF: %s（filter-repo 残留，会藏住已清理的历史）' % ref)
        # `refs/remotes/<remote>/*` 要区分两类：
        #   - `refs/remotes/origin/*`：本仓库已没有 origin，出现即为历史残留
        #   - `refs/remotes/upstream/*`：正常的上游跟踪引用，合并/对比都要用它
        # 2026-11-11 教训：第一版一刀切把所有 refs/remotes/ 判为残留，
        # fetch 上游后立刻误报 —— 门禁范围划错比没有门禁更糟。
        elif ref.startswith('refs/remotes/origin/'):
            problems.append('STALE_LOCAL_REF: %s（本仓库无 origin，属历史残留）' % ref)
    return problems


# ---------------------------------------------------------------- G09
@gate('G09', '文档内同一事实的数字不得自相矛盾')
def g09():
    """2026-11-11 实际事故：README 下载段写 279.77 MiB，已知限制段写 278.66 MiB。"""
    problems = []
    size = re.compile(r'(\d{2,3}\.\d{2})\s*MiB')
    for name in ('README.md', 'README.en.md'):
        path = ROOT / name
        if not path.is_file():
            continue
        found = {}
        for lineno, line in enumerate(read(path).split('\n'), 1):
            for value in size.findall(line):
                found.setdefault(value, []).append(lineno)
        if len(found) > 1:
            detail = '；'.join('%s MiB @行%s' % (k, ','.join(map(str, v)))
                              for k, v in sorted(found.items()))
            problems.append('CONTRADICTORY_SIZE: %s 出现多个包体数字（%s）' % (name, detail))
    return problems


# ---------------------------------------------------------------- G10
@gate('G10', '版本号三处一致')
def g10():
    problems = []
    gradle = read(ROOT / 'app/build.gradle')
    name = re.search(r'versionName\s+"([^"]+)"', gradle)
    code = re.search(r'versionCode\s+(\d+)', gradle)
    if not name or not code:
        return ['GRADLE_VERSION_MISSING']
    version, version_code = name.group(1), int(code.group(1))

    updates = json.loads(read(ROOT / 'updates.json') or '{}')
    release = (updates.get('releases') or [{}])[0]
    if release.get('version') != version:
        problems.append('VERSION_MISMATCH: build.gradle `%s` vs updates.json `%s`'
                        % (version, release.get('version')))
    if release.get('versionCode') != version_code:
        problems.append('VERSION_CODE_MISMATCH: build.gradle %s vs updates.json %s'
                        % (version_code, release.get('versionCode')))

    recent = json.loads(read(ROOT / 'app/src/main/res/raw/changelog_recent.json') or '{}')
    entries = recent.get('entries') or []
    if entries and entries[0].get('version') != version:
        problems.append('CHANGELOG_VERSION_MISMATCH: 首条 `%s` vs build.gradle `%s`'
                        % (entries[0].get('version'), version))

    # 版本名里的构建日期与今天是否离谱（只警告不拦，构建日期允许是过去某天）
    return problems


# ---------------------------------------------------------------- G11
@gate('G11', '正式包必须已输出到 builds/ 目录')
def g11():
    """用户在 2026-11-11 明确要求：以后构建的正式版都必须输出到
    /storage/emulated/0/Download/Eta/DSHA开发/builds。

    产物原先只躺在 app/build/outputs/（会被 gradle clean 清掉，也在
    .gitignore 里），交付时要手工 cp，容易忘；builds/ 历史上还混进过
    -PROBE1~-PROBE16 这类一次性探针包。
    """
    builds = ROOT.parent / 'builds'
    apk = ROOT / 'app/build/outputs/apk/standard/release/app-standard-release.apk'
    if not apk.is_file():
        return []  # 没构建过就不判（避免在纯文档改动时制造假红）
    if not builds.is_dir():
        return ['BUILDS_DIR_MISSING: %s 不存在' % builds]

    digest = hashlib.sha256(apk.read_bytes()).hexdigest()
    size = apk.stat().st_size
    # 找出 builds/ 下与当前产物字节完全一致的文件
    matching = []
    for candidate in sorted(builds.glob('*.apk')):
        try:
            if candidate.stat().st_size != size:
                continue
            if hashlib.sha256(candidate.read_bytes()).hexdigest() == digest:
                matching.append(candidate)
        except OSError:
            continue
    if not matching:
        return ['RELEASE_NOT_EXPORTED: 当前产物（%s…，%s B）没有出现在 %s\n'
                '        跑 python3 tools/export-release-apk.py'
                % (digest[:12], size, builds)]
    # 每个输出都必须有配套 .sha256，且内容正确
    problems = []
    for path in matching:
        side = path.with_suffix('.apk.sha256')
        if not side.is_file():
            problems.append('EXPORTED_SHA256_MISSING: %s 缺配套 .sha256' % path.name)
            continue
        recorded = side.read_text(encoding='ascii', errors='replace').split()
        if not recorded or recorded[0] != digest:
            problems.append('EXPORTED_SHA256_WRONG: %s 记录的摘要与产物不符' % side.name)
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)

    if args.list:
        for code, title, _ in GATES:
            print('%s  %s' % (code, title))
        return 0

    results = []
    failed = 0
    for code, title, fn in GATES:
        try:
            problems = fn() or []
        except Exception as error:  # 门禁自身坏掉也要报，不能静默通过
            problems = ['GATE_CRASHED: %s: %s' % (type(error).__name__, error)]
        results.append({'gate': code, 'title': title,
                        'status': 'fail' if problems else 'pass',
                        'problems': problems})
        if problems:
            failed += 1

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for row in results:
            print('[%s] %s  %s' % ('FAIL' if row['problems'] else ' OK ',
                                   row['gate'], row['title']))
            for problem in row['problems']:
                print('        ' + problem)
        total = len(results)
        print('\n%s  (%d/%d gates passed)' %
              ('RIGID GATES PASS' if not failed else 'RIGID GATES FAILED',
               total - failed, total))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
