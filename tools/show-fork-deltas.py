#!/usr/bin/env python3
"""逐个列出「fork 改动 vs 上游 v0.2.2」的具体差异片段，供人工判断是否合并。

只读。输出每个文件的 fork 侧新增行（即 fork 在 build190 上做的改动），
并标注该文件在上游 v0.2.2 里是否也被改过（改过的地方可能已含同一修复）。
"""
import difflib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORK = '0d5795c7'
BASE = 'c750348a4d4b18edcb165a93b4ca66403b040b4c'
THEIRS = 'refs/remotes/upstream/v0.2.2'
HEAD = 'HEAD'

TARGETS = [
    'core/UpdateEngine.java',
    'core/WebSessionRecovery.java',
    'core/PluginRepository.java',
    'vscreen/VirtualScreenManager.java',
    'ui/LaunchFragment.java',
    'ui/PluginFragment.java',
    'util/UpdatePolicy.java',
    'core/WebLifecycleController.java',
    'ui/UpdateActivity.java',
    'runtime/StoredWebSession.java',
    'vscreen/VirtualScreenCore.java',
    'backup/NativeDataLocations.java',
    'ui/BrowserOriginRestore.java',
    'util/AppIdentity.java',
    'util/WebProcSel.java',
    'runtime/WebProcessManager.java',
    'util/VirtualScreenBootstrap.java',
    'ui/SettingsFragment.java',
]
PREFIX = 'app/src/main/java/com/deepseekharness/app/'


def show(rev, path):
    try:
        return subprocess.check_output(['git', 'show', '%s:%s' % (rev, path)],
                                       cwd=ROOT, stderr=subprocess.DEVNULL).decode('utf-8', 'replace')
    except subprocess.CalledProcessError:
        return None


def lines(text):
    return [l.rstrip() for l in (text or '').split('\n')]


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for rel in TARGETS:
        if only and only not in rel:
            continue
        path = PREFIX + rel
        fork = show(FORK, path)
        base = show(BASE, path)
        theirs = show(THEIRS, path)
        head = show(HEAD, path)
        if fork is None or head is None:
            print('=== %s  (缺失，跳过)' % rel)
            continue

        # fork 相对 build190 的改动
        f_add = [l[1:].strip() for l in difflib.unified_diff(
            lines(base), lines(fork), lineterm='', n=0)
            if l.startswith('+') and not l.startswith('+++')]
        # 上游 v0.2.2 相对 build190 的改动
        t_add = [l[1:].strip() for l in difflib.unified_diff(
            lines(base), lines(theirs), lineterm='', n=0)
            if l.startswith('+') and not l.startswith('+++')]

        own = [l for l in f_add if l and l not in t_add]
        print('=== %s' % rel)
        print('    fork 新增 %d 行，其中上游 v0.2.2 没有的 %d 行'
              % (len([l for l in f_add if l]), len(own)))
        for line in own[:12]:
            print('      + ' + line[:150])
        if len(own) > 12:
            print('      … 另有 %d 行' % (len(own) - 12))
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
