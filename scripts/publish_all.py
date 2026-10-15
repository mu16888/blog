#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一键多平台发布：博客（GitHub→Cloudflare）+ 公众号（官方接口）

用法（仓库根目录）:
  python scripts/publish_all.py <slug>                 # 博客上线 + 公众号建草稿并发布
  python scripts/publish_all.py <slug> --draft-only    # 公众号只建草稿不发布（首发前人工过目用）

文章要求：content/posts/<slug>.md，draft:false，image 字段有封面。
"""
import datetime
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import wechat_publisher as wp  # noqa: E402

GIT_CANDS = [
    r"D:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files\Git\cmd\git.exe",
]
GIT = next((c for c in GIT_CANDS if Path(c).exists()), "git")


def run(args, timeout=300):
    p = subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def blog_deploy():
    """博客上线：add + commit + push（push 最多重试 5 次）。"""
    rc, out = run([GIT, "add", "-A"])
    if rc != 0:
        print(f"[博客] git add 失败:\n{out}")
        return False
    rc, out = run([GIT, "commit", "-m", "publish: %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M")])
    if rc != 0 and "nothing to commit" not in out:
        print(f"[博客] git commit 失败:\n{out}")
        return False
    for i in range(1, 6):
        rc, out = run([GIT, "push", "origin", "main"])
        if rc == 0:
            print("[博客] ✅ 已推送 GitHub，Cloudflare 约 1 分钟后自动上线")
            return True
        print(f"[博客] push 第{i}次失败，重试…")
    print(f"[博客] ❌ 连续 5 次推送失败:\n{out}")
    return False


def wechat_publish(slug, draft_only):
    """公众号：封面→素材库，建草稿；draft_only=False 再调发布接口。"""
    title, digest, cover, html, fm, raw_title = wp.prepare(slug)
    if wp.clean(fm.get("draft", "true")).lower() != "false":
        print(f"[公众号] ⚠️ {slug} 还是 draft:true，跳过（先在 md 里改 draft:false）")
        return False
    token = wp.get_token()
    thumb = wp.upload_cover(token, cover)
    article = {
        "title": title, "author": wp.CFG.get("author", ""), "digest": digest,
        "content": html, "thumb_media_id": thumb,
        "need_open_comment": 1, "only_fans_can_comment": 0,
        "content_source_url": f"{wp.SITE}/posts/{slug}/",
    }
    media_id = wp.add_draft(token, article)
    if draft_only:
        wp.log_draft(slug, media_id, published=False)
        print(f"[公众号] ✅ 草稿已建（未发布）media_id={media_id}")
        return True
    pub = wp.freepublish(token, media_id)
    ok = pub.get("errcode", 0) == 0
    wp.log_draft(slug, media_id, published=ok)
    print(f"[公众号] {'✅ 已发布' if ok else '❌ 发布失败'} {pub}")
    return ok


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    slug = sys.argv[1]
    draft_only = "--draft-only" in sys.argv
    print(f"===== 一键发布 {slug} =====")
    ok_blog = blog_deploy()
    ok_wx = wechat_publish(slug, draft_only)
    print("===== 结果 =====")
    print(f"博客:   {'✅' if ok_blog else '❌'}")
    print(f"公众号: {'✅' if ok_wx else '❌'}")
    sys.exit(0 if (ok_blog and ok_wx) else 1)


if __name__ == "__main__":
    main()
