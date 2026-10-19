# -*- coding: utf-8 -*-
import re, os

BLOG = r"E:/workbuddy工作台/四季发财公司/12_运营工程区/沐风博客/content/posts"
FILES = [
    "gww-format-pitfalls.md", "gww-qingshi-report.md", "gww-title-traps.md",
    "gww-redhead-checklist.md", "gww-banned-words.md", "ai-office-basics.md",
    "ai-weekly-report.md", "free-office-tools.md",
]

def tag_repl(m):
    line = m.group(0)
    if "公文写作系统" in line:
        return line  # 已含，跳过
    if line.rstrip().endswith("]"):
        return line[:-1].rstrip() + ', "公文写作系统"]'
    return line

for fn in FILES:
    path = os.path.join(BLOG, fn)
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    txt, n = re.subn(r'^tags: \[.*?\]\s*$', tag_repl, txt, count=1, flags=re.MULTILINE)
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"[{'OK' if n==1 else 'WARN n='+str(n)}] {fn} -> {txt.splitlines()[5]}")
