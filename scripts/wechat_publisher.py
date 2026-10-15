#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
公众号发布工具 —— 把博客 Markdown 一键转成公众号图文（官方草稿箱/发布接口，不碰登录态）

用法（在仓库根目录跑）:
  python scripts/wechat_publisher.py list                 # 列出可发文章（draft:false）
  python scripts/wechat_publisher.py build <slug>         # 只生成微信 HTML 预览，不调接口
  python scripts/wechat_publisher.py draft <slug>         # 传封面 + 建草稿（安全，默认动作）
  python scripts/wechat_publisher.py publish <slug>       # 建草稿 + 立即发布（freepublish）

凭据在 config/wechat_config.json（已被 .gitignore 挡住，不入 GitHub）。
依赖: markdown requests（managed venv 已装）
"""
import json
import re
import sys
import time
from pathlib import Path

import markdown
import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "wechat_config.json"
TOKEN_FILE = ROOT / "config" / ".wechat_token.json"
DRAFT_LOG = ROOT / "config" / ".wechat_drafts.json"
POSTS_DIR = ROOT / "content" / "posts"
PREVIEW_DIR = ROOT / "_wechat_preview"
API = "https://api.weixin.qq.com"

CFG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
SITE = CFG["site_base"].rstrip("/")


# ---------------------------------------------------------------- token
def get_token(force=False):
    if TOKEN_FILE.exists() and not force:
        d = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
        if d.get("expire", 0) > time.time() + 120:
            return d["access_token"]
    r = requests.get(
        f"{API}/cgi-bin/token",
        params={"grant_type": "client_credential", "appid": CFG["appid"], "secret": CFG["secret"]},
        timeout=15,
    ).json()
    if "access_token" not in r:
        hint = ""
        if r.get("errcode") == 40164:
            hint = "  → 本机公网IP不在白名单：微信开发者平台 → 公众号 → 基础信息 → 开发密钥 → 设置名单"
        elif r.get("errcode") in (40001, 40125):
            hint = "  → AppSecret 不对，去开发者平台重新生成"
        elif r.get("errcode") == 40013:
            hint = "  → AppID 不对，核对 config/wechat_config.json"
        sys.exit(f"[token失败] {r}{hint}")
    TOKEN_FILE.write_text(
        json.dumps({"access_token": r["access_token"], "expire": time.time() + r["expires_in"]}, ensure_ascii=False),
        encoding="utf-8",
    )
    return r["access_token"]


# ---------------------------------------------------------------- 文章解析
def load_post(slug):
    path = POSTS_DIR / f"{slug}.md"
    if not path.exists():
        sys.exit(f"[找不到文章] {path}")
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        sys.exit(f"[frontmatter异常] {path}")
    fm = {}
    for line in parts[1].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line.strip())
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm, parts[2].strip()


def clean(v):
    return v.strip().strip('"').strip("'") if v else ""


def fit_bytes(s, limit):
    """微信限制按 UTF-8 字节算（中文1字=3字节）。超限从尾部裁到 limit 内。"""
    while s and len(s.encode("utf-8")) > limit:
        s = s[:-1]
    return s


# ---------------------------------------------------------------- Markdown → 微信HTML
S = {  # 内联样式（微信编辑器会剥 <style> 块，必须内联）
    "h2": 'font-size:17px;font-weight:bold;color:#1b2a4d;border-left:4px solid #1b2a4d;padding-left:10px;margin:28px 0 14px;',
    "h3": 'font-size:16px;font-weight:bold;color:#1b2a4d;margin:22px 0 12px;',
    "p": 'font-size:15px;color:#333;line-height:1.9;letter-spacing:0.3px;margin:0 0 16px;text-align:justify;',
    "strong": 'color:#1b2a4d;',
    "table": 'width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;',
    "th": 'background:#1b2a4d;color:#ffffff;border:1px solid #dfe3ea;padding:8px 10px;text-align:left;',
    "td": 'border:1px solid #dfe3ea;padding:8px 10px;color:#333;',
    "ul": 'margin:0 0 16px;padding-left:22px;',
    "ol": 'margin:0 0 16px;padding-left:22px;',
    "li": 'font-size:15px;color:#333;line-height:1.9;margin-bottom:6px;',
    "blockquote": 'border-left:4px solid #c9a86a;background:#faf7f2;padding:10px 14px;margin:0 0 16px;',
    "hr": 'border:none;border-top:1px dashed #cccccc;margin:24px 0;',
    "img": 'max-width:100%;display:block;margin:0 auto;',
}


def md_to_wechat_html(body):
    html = markdown.markdown(body, extensions=["tables"])
    # 相对路径图片转绝对（博客域名直链）
    html = re.sub(r'src="/', f'src="{SITE}/', html)
    # 逐类注入内联样式
    for tag, style in S.items():
        if tag in ("strong",):
            html = re.sub(rf"<{tag}>(?!<span)", f'<{tag} style="{style}">', html)
        elif tag == "img":
            html = re.sub(r"<img ", f'<img style="{style}" ', html)
        elif tag == "hr":
            html = html.replace("<hr />", f'<hr style="{style}"/>').replace("<hr>", f'<hr style="{style}"/>')
        elif tag in ("ul", "ol", "table", "blockquote"):
            html = re.sub(rf"<{tag}>", f'<{tag} style="{style}">', html)
        else:
            html = re.sub(rf"<{tag}>(.*?)</{tag}>", rf'<{tag} style="{style}">\1</{tag}>', html, flags=re.S)
    # th/td 逐个上样式
    html = re.sub(r"<th>(.*?)</th>", rf'<th style="{S["th"]}">\1</th>', html, flags=re.S)
    html = re.sub(r"<td>(.*?)</td>", rf'<td style="{S["td"]}">\1</td>', html, flags=re.S)
    return html.strip()


# ---------------------------------------------------------------- 微信接口
def api_post(path, payload, timeout=30):
    """POST JSON，显式 UTF-8 提交 + 显式 utf-8 解码响应。

    两个坑都在这里：
    1) 提交用 requests 的 json= 会走 ensure_ascii=True，中文被转成 \\uXXXX 而微信
       未解码 → 后台正文显示乱码。必须 ensure_ascii=False + UTF-8 字节。
    2) 微信响应没有 charset，requests 的 .json() 会猜成 ISO-8859-1，把 UTF-8 中文
       解成 mojibake（ä½ å¥½）。必须 content.decode("utf-8") 再 json.loads。
    """
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    r = requests.post(
        f"{API}{path}",
        params={"access_token": get_token()},
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=timeout,
    )
    return json.loads(r.content.decode("utf-8"))


def upload_cover(token, local_path: Path):
    if not local_path.exists():
        sys.exit(f"[封面对不上] 本地找不到 {local_path}")
    r = requests.post(
        f"{API}/cgi-bin/material/add_material",
        params={"access_token": token, "type": "image"},
        files={"media": (local_path.name, local_path.read_bytes(), "image/jpeg")},
        timeout=60,
    ).json()
    if "media_id" not in r:
        sys.exit(f"[封面上传失败] {r}")
    return r["media_id"]


def add_draft(token, article):
    # 🔴 必须显式 ensure_ascii=False + UTF-8 字节提交：早期用 json= 参数导致中文被
    # 转义后未被微信正确解码，草稿正文在后台显示成 \uXXXX 乱码。
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    r = requests.post(
        f"{API}/cgi-bin/draft/add",
        params={"access_token": token},
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30,
    ).json()
    if "media_id" not in r:
        sys.exit(f"[建草稿失败] {r}")
    return r["media_id"]


def freepublish(token, media_id):
    r = requests.post(f"{API}/cgi-bin/freepublish/submit", params={"access_token": token},
                      json={"media_id": media_id}, timeout=30).json()
    return r


# ---------------------------------------------------------------- 主流程
def prepare(slug):
    fm, body = load_post(slug)
    title = clean(fm.get("wechat_title", "")) or clean(fm.get("title", ""))
    raw_title = clean(fm.get("title", ""))
    if len(title.encode("utf-8")) > 63:
        title = fit_bytes(title, 60)
        print(f"[警告] 标题超64字节限制，已裁短 → {title}（建议在 md 加 wechat_title 字段定制）")
    digest = fit_bytes(clean(fm.get("description", "")), 115)
    image_rel = clean(fm.get("image", ""))
    cover = ROOT / "static" / image_rel.lstrip("/") if image_rel else None
    # 优先用公众号专用封面（2.35:1），避免微信按 2.35:1 居中裁切切到两段式文字上下；
    # 若不存在则回退到博客头图（4:1）由微信自行裁切。
    wechat_cover = ROOT / "static" / "covers" / "wechat" / f"{slug}.jpg"
    if wechat_cover.exists():
        cover = wechat_cover
    html = md_to_wechat_html(body)
    return title, digest, cover, html, fm, raw_title


def log_draft(slug, media_id, published):
    logs = json.loads(DRAFT_LOG.read_text(encoding="utf-8")) if DRAFT_LOG.exists() else {}
    logs[slug] = {"media_id": media_id, "published": published, "time": time.strftime("%Y-%m-%d %H:%M")}
    DRAFT_LOG.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]

    if cmd == "list":
        for p in sorted(POSTS_DIR.glob("*.md")):
            fm, _ = load_post(p.stem)
            if clean(fm.get("draft", "true")).lower() == "false":
                print(f"{p.stem:28s} {clean(fm.get('title',''))}")
        return

    if cmd == "drafts":
        # 真正查询微信草稿箱（list 只列本地文章，不等于草稿箱实际内容）
        c = api_post("/cgi-bin/draft/count", {})
        if "total_count" not in c:
            sys.exit(f"[count失败] {c}")
        total = c["total_count"]
        titles, offset = [], 0
        while offset < total:
            r = api_post("/cgi-bin/draft/batchget",
                         {"offset": offset, "count": 20, "no_content": 1}, timeout=20)
            if "item" not in r:
                sys.exit(f"[batchget失败] {r}")
            for it in r["item"]:
                news = (it.get("content") or {}).get("news_item") or [{}]
                t = news[0].get("title") or ("(无标题)" + it.get("media_id", "")[:16])
                titles.append(t)
            offset += 20
        print(f"草稿箱共 {total} 篇：")
        for i, t in enumerate(titles, 1):
            print(f"  {i:2d}. {t}")
        local = []
        for p in sorted(POSTS_DIR.glob("*.md")):
            fm, _ = load_post(p.stem)
            if clean(fm.get("draft", "true")).lower() == "false":
                local.append((p.stem, clean(fm.get("wechat_title", "")) or clean(fm.get("title", ""))))
        missing = [(s, t) for s, t in local if t not in titles]
        if missing:
            print("\n[注意] 本地有文章但草稿箱没有对应草稿，补建命令：")
            for s, t in missing:
                print(f"  python scripts/wechat_publisher.py draft {s}    # {t}")
        else:
            print("\n[OK] 本地可发文章在草稿箱均有对应草稿")
        return

    if cmd == "verify":
        # 建完草稿必须跑一遍：校验正文是否为正常中文，防乱码事故流向发布
        total = api_post("/cgi-bin/draft/count", {}).get("total_count", 0)
        items, offset = [], 0
        while offset < total:
            r = api_post("/cgi-bin/draft/batchget",
                         {"offset": offset, "count": 20, "no_content": 1}, timeout=20)
            items.extend(r.get("item") or [])
            offset += 20
        print(f"校验草稿箱 {len(items)} 篇正文编码：")
        bad = 0
        for it in items:
            obj = api_post("/cgi-bin/draft/get", {"media_id": it["media_id"]}, timeout=25)
            art = (obj.get("news_item") or [{}])[0]
            text = re.sub(r"<[^>]+>", "", art.get("content", ""))
            zh = len(re.findall("[一-龥]", text))
            if not zh:
                bad += 1
            print(f"  {'✅正常' if zh else '❌乱码'}  {art.get('title', '')[:26]:28s} 正文汉字 {zh}")
        if bad:
            print(f"\n[结论] 有 {bad} 篇乱码，禁止发布！需重建（内容源在本地 md，重建即可）")
        else:
            print("\n[结论] 全部正常，可以发布")
        return

    if len(sys.argv) < 3:
        sys.exit("缺 slug 参数")
    slug = sys.argv[2]
    title, digest, cover, html, fm, raw_title = prepare(slug)

    if cmd == "build":
        PREVIEW_DIR.mkdir(exist_ok=True)
        out = PREVIEW_DIR / f"{slug}.html"
        out.write_text(f"<h1>{title}</h1>\n{html}", encoding="utf-8")
        print(f"[预览已生成] {out}")

    elif cmd == "draft":
        token = get_token()
        thumb = upload_cover(token, cover)
        media_id = add_draft(token, {
            "title": title, "author": CFG.get("author", ""), "digest": digest,
            "content": html, "thumb_media_id": thumb,
            "need_open_comment": 1, "only_fans_can_comment": 0,
            "content_source_url": f"{SITE}/posts/{slug}/",
        })
        log_draft(slug, media_id, published=False)
        print(f"[草稿OK] {slug} media_id={media_id}\n去 mp.weixin.qq.com 草稿箱可见。发布需另跑 publish 命令。")

    elif cmd == "rm":
        # 删除草稿箱里某篇草稿（已发布或重复时清理；内容随时可从本地 md 重建）
        logs = json.loads(DRAFT_LOG.read_text(encoding="utf-8")) if DRAFT_LOG.exists() else {}
        mid = logs.get(slug, {}).get("media_id")
        if not mid:
            sys.exit(f"[无记录] {slug} 不在本地建稿记录里")
        r = api_post("/cgi-bin/draft/delete", {"media_id": mid})
        if r.get("errcode") == 0:
            logs.pop(slug, None)
            DRAFT_LOG.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[删除 {slug}] {r}")

    elif cmd == "publish":
        token = get_token()
        thumb = upload_cover(token, cover)
        media_id = add_draft(token, {
            "title": title, "author": CFG.get("author", ""), "digest": digest,
            "content": html, "thumb_media_id": thumb,
            "need_open_comment": 1, "only_fans_can_comment": 0,
            "content_source_url": f"{SITE}/posts/{slug}/",
        })
        pub = freepublish(token, media_id)
        ok = pub.get("errcode", 0) == 0
        log_draft(slug, media_id, published=ok)
        print(f"[发布] {'成功' if ok else '失败'} {pub}\n草稿 media_id={media_id}")

    else:
        sys.exit(f"未知命令 {cmd}，见文件头用法")


if __name__ == "__main__":
    main()
