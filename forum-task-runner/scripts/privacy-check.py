#!/usr/bin/env python3
"""Inspect Git objects, never print credential contents. Scope: forum-task-runner."""
import re
import subprocess
import sys
from pathlib import PurePosixPath

PREFIX = 'forum-task-runner/'
PRIVATE_DIRS = {'.data', '.private', '.test-output', 'backups', 'exports', 'profiles',
                'test-results', 'playwright-report', 'node_modules', '.browsers'}
PRIVATE_SUFFIX = re.compile(r'\.(key|pem|p12|pfx|sqlite(?:3)?(?:-\w+)?|db(?:-\w+)?|log|har|zip|tar|gz|webm|mp4)$', re.I)
SECRETS = [
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    re.compile(rb'127\.0\.0\.1:8924/#[a-f0-9]{32,}', re.I),
    re.compile(rb'\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}'),
    re.compile(rb'\bAKIA[A-Z0-9]{16}\b'),
    re.compile(rb'Bearer\s+[A-Za-z0-9_.-]{24,}'),
    re.compile(rb'"(?:password|passwd|access_token|refresh_token|client_secret)"\s*:\s*"[^"\s]{8,}"', re.I),
    re.compile(rb'"cookies"\s*:\s*\[\s*\{'),
]

def git(*args):
    return subprocess.check_output(['git', *args], stderr=subprocess.DEVNULL)

def reason(path, content):
    parts=PurePosixPath(path).parts
    name=parts[-1]
    if any(p in PRIVATE_DIRS or p.startswith('browser-profile') for p in parts[1:]): return '私有目录'
    if name=='.env' or name.startswith('.env.') or PRIVATE_SUFFIX.search(name): return '敏感文件类型'
    if re.search(r'(cookies|storage.?state|credentials|secrets).*\.json$|\.local\.(json|ya?ml)$',name,re.I):return '本地凭据配置'
    if any(p.search(content) for p in SECRETS): return '疑似凭据内容'
    return None

def scan(mode):
    if mode=='--history':
        refs=git('rev-list','--all','--',PREFIX).decode().splitlines()
    else: refs=['HEAD'] if mode=='--head' else [None]
    failures=set();seen=set()
    for ref in refs:
        if ref:
            entries=git('ls-tree','-r','-z',ref,'--',PREFIX).split(b'\0')
            objects=[]
            for entry in entries:
                if not entry:continue
                meta,path=entry.split(b'\t',1);objects.append((path.decode(),meta.split()[2].decode()))
        else:
            paths=git('diff','--cached','--name-only','--diff-filter=ACMR','-z','--',PREFIX).split(b'\0')
            objects=[(p.decode(),':'+p.decode()) for p in paths if p]
        for path,obj in objects:
            if (path,obj) in seen:continue
            seen.add((path,obj))
            why=reason(path,git('show',obj))
            if why:failures.add((path,why))
    for path,why in sorted(failures):print(f'BLOCKED {path}: {why}',file=sys.stderr)
    if failures:
        print('隐私检查未通过。请清理暂存区/历史，不要绕过检查。',file=sys.stderr)
        return 1
    print('隐私检查通过：'+('本项目全部本地引用历史' if mode=='--history' else '本项目暂存内容' if mode=='--staged' else '本项目 HEAD'))
    return 0

if __name__=='__main__':
    try: sys.exit(scan(sys.argv[1] if len(sys.argv)>1 else '--staged'))
    except (subprocess.CalledProcessError,UnicodeError,IndexError):
        print('隐私检查无法完成，拒绝继续。',file=sys.stderr);sys.exit(2)
