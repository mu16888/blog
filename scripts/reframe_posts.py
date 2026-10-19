# -*- coding: utf-8 -*-
import re, os

BLOG = r"E:/workbuddy工作台/四季发财公司/12_运营工程区/沐风博客/content/posts"

# 每篇：统一的 CTA 外层样式 + 帖子专属引导句 + 统一系统卖点
STYLE = ('<div style="margin:24px 0;padding:16px 18px;border-left:4px solid #1b2a4d;'
         'background:#f8f9fc;border-radius:0 8px 8px 0;font-size:14px;color:#444;">')

SYS_PITCH = ("给 AI 一句话，它就吐出一份标准（国标）红头文件——把国标格式、文种规则、语言规范、"
             "审稿自检整合成一套可反复调用的公文写作系统，装进任意 AI 工具即用，红头、标题、正文、落款一次到位。"
             "42 个红头 DOCX 随系统赠送。不代写、不编造，重要文书仍须人工复核。")

SERIES_LINE = "> 📚 本文是《公文写作系统》系列之一。\n"

# (文件名, 引导句)  —— 引导句保持各篇自然口吻，卖点统一为系统
LEADS = {
    "gww-format-pitfalls.md":   "📚 想让公文写作少返工？",
    "gww-qingshi-report.md":    "📚 文种总拿不准？",
    "gww-title-traps.md":       "📚 标题和文种总拿不准？",
    "gww-redhead-checklist.md": "📚 想一键套国标版式？",
    "gww-banned-words.md":      "📚 语病和禁词想一次查干净？",
    "ai-office-basics.md":      "🛠️ 想把手里的重复活自动化？",
    "ai-weekly-report.md":      "🛠️ 周报月报只是开始",
    "free-office-tools.md":     "🛠️ 公文类重复活，我做了个专门系统",
}

CTA_RE = re.compile(
    r'<div style="margin:24px 0;padding:16px 18px;border-left:4px solid #1b2a4d;.*?</div>\s*',
    re.DOTALL)

def new_cta(lead):
    return (STYLE + "\n"
            '<strong style="color:#1b2a4d;">' + lead + '</strong><br>\n'
            '试试 <a href="/products/gongwensecpro/" style="color:#1b2a4d;font-weight:700;">公文秒成Pro</a>：'
            + SYS_PITCH + '\n</div>\n')

for fn, lead in LEADS.items():
    path = os.path.join(BLOG, fn)
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()

    # 1) 系列标识：插到 front matter 闭合 (draft: false\n---\n) 之后
    if "《公文写作系统》系列之一" not in txt:
        txt = re.sub(r'(draft: false\n---\n)', r'\1\n' + SERIES_LINE + r'\n', txt, count=1)

    # 2) 替换 CTA 盒子
    txt, n = CTA_RE.subn(lambda m: new_cta(lead), txt, count=1)
    if n != 1:
        print(f"[WARN] {fn}: CTA 替换数={n}")

    # 3) tags 追加「公文写作系统」
    if "公文写作系统" not in txt:
        def tag_repl(m):
            line = m.group(0)
            if line.rstrip().endswith("]"):
                return line[:-1].rstrip() + ', "公文写作系统"]'
            return line
        txt, tn = re.subn(r'^tags: \[.*?\]\s*$', tag_repl, txt, count=1, flags=re.MULTILINE)
        if tn != 1:
            print(f"[WARN] {fn}: tags 替换数={tn}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"[OK] {fn} 处理完成")
