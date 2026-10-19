# -*- coding: utf-8 -*-
"""查公众号 afdian-ruhu 草稿的线上状态：本地记录 + 草稿箱是否还在。"""
import json
import sys

sys.path.insert(0, r"E:\workbuddy工作台\四季发财公司\12_运营工程区\沐风博客\scripts")
import wechat_publisher as wp

SLUG = "afdian-ruhu"
logs = json.loads(wp.DRAFT_LOG.read_text(encoding="utf-8"))
rec = logs.get(SLUG, {})
print("[本地记录]", json.dumps(rec, ensure_ascii=False))

media_id = rec.get("media_id")
if not media_id:
    sys.exit("[FAIL] 无 media_id")

# 拉线上草稿详情
d = wp.api_post("/cgi-bin/draft/get", {"media_id": media_id}, timeout=25)
items = d.get("news_item") or [{}]
art = items[0]
print("[线上标题]", art.get("title"))
print("[线上更新时间]", art.get("update_time"))
content = art.get("content", "")
print("[正文含爱发电主页链接]", "afdian.com/a/mufengai" in content)

# 列出草稿箱全部，看 afdian-ruhu 是否还在（还在=未发布）
lst = wp.api_post("/cgi-bin/draft/batchget", {"offset": 0, "count": 20, "no_content": 1}, timeout=25)
items2 = lst.get("item") or []
print("[草稿箱条数]", len(items2))
for it in items2:
    t = ((it.get("content") or {}).get("news_item") or [{}])[0].get("title", "?")
    print("   -", it.get("update_time"), "|", t)