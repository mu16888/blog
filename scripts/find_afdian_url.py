# -*- coding: utf-8 -*-
"""找已发布的《我入驻「爱发电」了》正式链接（认证私信要填）。"""
import re
import sys

sys.path.insert(0, r"E:\workbuddy工作台\四季发财公司\12_运营工程区\沐风博客\scripts")
import wechat_publisher as wp

KEY = "爱发电"
found = []

# 1) 已发布列表（freepublish batchget）
try:
    d = wp.api_post("/cgi-bin/freepublish/batchget",
                    {"offset": 0, "count": 20, "no_content": 1}, timeout=25)
    items = d.get("item") or []
    print("[已发布条数]", len(items))
    for it in items:
        det = (it.get("article_detail") or {}).get("item") or []
        t = det[0].get("title", "") if det else ""
        u = det[0].get("article_url", "") if det else ""
        print("   -", it.get("update_time"), "|", t, "|", u)
        if KEY in t:
            found.append((it.get("publish_id"), t, u))
except Exception as e:
    print("[freepublish batchget 失败]", e)

# 2) 回退：草稿箱里找（若还没发布）
if not found:
    try:
        lst = wp.api_post("/cgi-bin/draft/batchget",
                          {"offset": 0, "count": 20, "no_content": 1}, timeout=25)
        for it in lst.get("item") or []:
            t = ((it.get("content") or {}).get("news_item") or [{}])[0].get("title", "")
            print("[草稿]", t)
            if KEY in t:
                print("   -> media_id:", it.get("media_id"))
    except Exception as e:
        print("[draft batchget 失败]", e)

if found:
    print("\n===== 找到已发布文章 =====")
    for pid, t, u in found:
        print("publish_id:", pid)
        print("标题:", t)
        print("链接:", u)
else:
    print("\n[结果] 未在已发布/草稿箱定位到标题含“爱发电”的文章")