# -*- coding: utf-8 -*-
import os, re, glob
from PIL import Image

BLOG = r"E:/workbuddy工作台/四季发财公司/12_运营工程区/沐风博客"
IMG = os.path.join(BLOG, "static", "img", "gw-templates")

# 1) PNG -> JPEG（白底文档样张，q85）
for png in glob.glob(os.path.join(IMG, "gw-*.png")):
    jpg = png[:-4] + ".jpg"
    im = Image.open(png)
    if im.mode != "RGB":
        im = im.convert("RGB")
    im.save(jpg, "JPEG", quality=85, optimize=True)
    kb_png = os.path.getsize(png) // 1024
    os.remove(png)
    kb_jpg = os.path.getsize(jpg) // 1024
    print(f"{os.path.basename(png)}({kb_png}KB 删) -> {os.path.basename(jpg)}({kb_jpg}KB)")

# 2) 5 篇文章引用 .png -> .jpg（仅 /img/gw-templates/）
POSTS = ["gww-format-pitfalls", "gww-redhead-checklist", "gww-qingshi-report",
         "gww-title-traps", "gww-banned-words"]
pat = re.compile(r'(/img/gw-templates/gw-[a-z]+)\.png')
for p in POSTS:
    f = os.path.join(BLOG, "content", "posts", p + ".md")
    with open(f, encoding="utf-8") as fh:
        t = fh.read()
    t2, n = pat.subn(r'\1.jpg', t)
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(t2)
    print(f"{p}: 替换 {n} 处")
