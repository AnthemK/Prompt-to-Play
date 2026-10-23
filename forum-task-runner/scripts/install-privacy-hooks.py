#!/usr/bin/env python3
"""Install repository-local guards without overwriting unrelated hooks."""
import subprocess
from pathlib import Path
root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
custom=subprocess.run(['git','config','--get','core.hooksPath'],capture_output=True,text=True)
if custom.returncode==0:raise SystemExit('已有自定义 hooksPath，请人工合并钩子；不覆盖。')
hooks=Path(subprocess.check_output(['git','rev-parse','--git-path','hooks'],text=True).strip())
marker='# forum-task-runner privacy guard'
for name in ['pre-commit','pre-push']:
    p=hooks/name
    if p.exists() and marker not in p.read_text():raise SystemExit('已有 '+name+'，请合并；不覆盖。')
hooks.mkdir(parents=True,exist_ok=True)
for name,mode in [('pre-commit','--staged'),('pre-push','--history')]:
    p=hooks/name
    p.write_text('#!/bin/sh\n'+marker+'\nset -eu\nroot=$(git rev-parse --show-toplevel)\nexec python3 "$root/forum-task-runner/scripts/privacy-check.py" '+mode+'\n')
    p.chmod(0o755)
print('已安装本机 pre-commit 与 pre-push 隐私检查。')
