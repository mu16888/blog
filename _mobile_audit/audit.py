# -*- coding: utf-8 -*-
"""
沐风博客 手机端体验实测 —— 检测脚本（只读，不修改站点任何文件）
视口：iPhone 390x844 @2x
"""
import asyncio
import json
import os
import sys

from playwright.async_api import async_playwright

OUT = r"E:\workbuddy工作台\四季发财公司\12_运营工程区\沐风博客\_mobile_audit"
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1")

PAGES = [
    ("01-home", "https://mufeng168.top/"),
    ("02-posts", "https://mufeng168.top/posts/"),
    ("03-article", "https://mufeng168.top/posts/gww-banned-words/"),
    ("04-product", "https://mufeng168.top/products/gongwensecpro/"),
    ("05-interact", "https://mufeng168.top/interact/"),
]

JS_PROBE = r"""
() => {
  const vw = window.innerWidth;
  const out = {};
  const R = (n) => Math.round(n * 10) / 10;

  const vis = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return false;
    return true;
  };
  const label = (el) => {
    const id = el.id ? '#' + el.id : '';
    let cls = '';
    if (typeof el.className === 'string' && el.className.trim()) {
      cls = '.' + el.className.trim().split(/\s+/).slice(0, 4).join('.');
    }
    return el.tagName.toLowerCase() + id + cls;
  };
  const clipAncestor = (el) => {
    let p = el.parentElement;
    while (p && p !== document.documentElement && p !== document.body) {
      const cs = getComputedStyle(p);
      if (['auto', 'scroll', 'hidden', 'clip'].indexOf(cs.overflowX) >= 0) {
        return { el: label(p), overflowX: cs.overflowX, scrollW: p.scrollWidth, clientW: p.clientWidth };
      }
      p = p.parentElement;
    }
    return null;
  };

  out.viewport = { w: vw, h: window.innerHeight, dpr: window.devicePixelRatio };
  out.docScrollWidth = document.documentElement.scrollWidth;
  out.bodyScrollWidth = document.body.scrollWidth;
  out.docScrollHeight = document.documentElement.scrollHeight;
  out.hasHorizontalOverflow = document.documentElement.scrollWidth > vw;
  out.overflowPx = document.documentElement.scrollWidth - vw;
  out.metaViewport = (() => {
    const m = document.querySelector('meta[name=viewport]');
    return m ? m.getAttribute('content') : null;
  })();

  // ---- 1. 横向溢出元素 ----
  const over = [];
  document.querySelectorAll('*').forEach((el) => {
    if (!vis(el)) return;
    const r = el.getBoundingClientRect();
    if (r.right > vw + 1 || r.left < -1) {
      over.push({
        el: label(el),
        left: R(r.left), right: R(r.right), width: R(r.width), height: R(r.height),
        text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 50),
        clippedBy: clipAncestor(el),
        // 自身是否可横向滚动容器
        selfScrollable: (() => {
          const cs = getComputedStyle(el);
          return (['auto', 'scroll'].indexOf(cs.overflowX) >= 0) ? { scrollW: el.scrollWidth, clientW: el.clientWidth } : null;
        })(),
      });
    }
  });
  out.overflowCount = over.length;
  out.overflowElements = over.slice(0, 80);

  // ---- 2. 正文字号 ----
  const sel = ['.post-content', '.post-body', '.entry-content', '.article-content',
               '.post-content-inner', 'article .content', '.single-content', 'main .content'];
  let contentRoot = null;
  for (const s of sel) { const n = document.querySelector(s); if (n) { contentRoot = n; break; } }
  if (!contentRoot) contentRoot = document.querySelector('article') || document.querySelector('main');
  out.contentRoot = contentRoot ? label(contentRoot) : null;

  const paraStats = {};
  const paraSamples = [];
  if (contentRoot) {
    contentRoot.querySelectorAll('p, li').forEach((p) => {
      if (!vis(p)) return;
      const t = (p.textContent || '').trim();
      if (t.length < 8) return;
      const cs = getComputedStyle(p);
      const key = cs.fontSize + ' / ' + cs.lineHeight;
      paraStats[key] = (paraStats[key] || 0) + 1;
      if (paraSamples.length < 3) {
        paraSamples.push({ el: label(p), fontSize: cs.fontSize, lineHeight: cs.lineHeight,
                           fontFamily: cs.fontFamily.split(',')[0].replace(/"/g, '') });
      }
    });
  }
  out.paraFontSizeStats = paraStats;
  out.paraSamples = paraSamples;

  // 正文整体宽度
  if (contentRoot) {
    const cr = contentRoot.getBoundingClientRect();
    out.contentRect = { width: R(cr.width), left: R(cr.left), right: R(cr.right) };
    const ccs = getComputedStyle(contentRoot);
    out.contentRootFontSize = ccs.fontSize;
    out.contentRootLineHeight = ccs.lineHeight;
  }

  // 标题字号
  const hSizes = [];
  document.querySelectorAll('h1,h2,h3').forEach((h) => {
    if (!vis(h)) return;
    const r = h.getBoundingClientRect();
    hSizes.push({ el: label(h), fontSize: getComputedStyle(h).fontSize,
                  width: R(r.width), right: R(r.right),
                  text: (h.textContent || '').trim().slice(0, 40) });
  });
  out.headingSizes = hSizes.slice(0, 12);

  // ---- 3. 点击目标 < 40px ----
  const small = [];
  document.querySelectorAll('a, button, [role=button], input[type=submit], label').forEach((el) => {
    if (!vis(el)) return;
    const r = el.getBoundingClientRect();
    if (r.height < 40) {
      const cs = getComputedStyle(el);
      small.push({
        tag: el.tagName.toLowerCase(), el: label(el),
        height: R(r.height), width: R(r.width),
        display: cs.display,
        text: ((el.textContent || '') || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().replace(/\s+/g, ' ').slice(0, 30),
        inContent: contentRoot ? contentRoot.contains(el) : false,
        href: (el.getAttribute('href') || '').slice(0, 60),
      });
    }
  });
  out.smallTapTargets = small;
  out.smallTapTargetCount = small.length;

  // 全部可点击元素总数
  let clickableTotal = 0;
  document.querySelectorAll('a, button, [role=button]').forEach((el) => { if (vis(el)) clickableTotal++; });
  out.clickableTotal = clickableTotal;

  // ---- 4. 页头区域布局 ----
  const heads = [];
  document.querySelectorAll('header, .site-header, #header, .navbar, nav, .nav').forEach((h) => {
    if (!vis(h)) return;
    const r = h.getBoundingClientRect();
    const kids = [];
    h.querySelectorAll('a, button, img, h1, h2, span, li, div, input').forEach((c) => {
      if (!vis(c)) return;
      const cr = c.getBoundingClientRect();
      if (cr.width < 2 || cr.height < 2) return;
      const txt = (c.textContent || '').trim().replace(/\s+/g, ' ');
      if (!txt && c.tagName.toLowerCase() !== 'img' && c.tagName.toLowerCase() !== 'input') return;
      kids.push({ el: label(c), x: R(cr.left), y: R(cr.top), w: R(cr.width), h: R(cr.height),
                  text: txt.slice(0, 24), fs: getComputedStyle(c).fontSize,
                  src: (c.getAttribute('src') || '').slice(-30) });
    });
    heads.push({
      el: label(h), x: R(r.left), y: R(r.top), w: R(r.width), h: R(r.height),
      scrollW: h.scrollWidth, clientW: h.clientWidth,
      display: getComputedStyle(h).display,
      children: kids.slice(0, 45),
    });
  });
  out.headers = heads.slice(0, 6);

  // ---- 5. 图片 / 代码块 / 表格 ----
  const blocks = [];
  document.querySelectorAll('img, pre, table, .highlight, .chroma, figure, iframe, video, .table-wrapper').forEach((el) => {
    if (!vis(el)) return;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    const parent = el.parentElement ? (() => {
      const pcs = getComputedStyle(el.parentElement);
      return { el: label(el.parentElement), overflowX: pcs.overflowX,
               scrollW: el.parentElement.scrollWidth, clientW: el.parentElement.clientWidth };
    })() : null;
    blocks.push({
      el: label(el), width: R(r.width), height: R(r.height),
      right: R(r.right),
      scrollW: el.scrollWidth, clientW: el.clientWidth,
      selfOverflowX: cs.overflowX,
      natural: (el.tagName.toLowerCase() === 'img') ? (el.naturalWidth + 'x' + el.naturalHeight) : null,
      parent: parent,
      src: (el.getAttribute('src') || '').slice(-50),
    });
  });
  out.blocks = blocks.slice(0, 60);
  out.oversizeBlocks = blocks.filter((b) => b.right > vw + 1 || b.scrollW > b.clientW + 1 || b.width > vw + 1);

  // ---- 6. 表单控件（评论框）----
  const forms = [];
  document.querySelectorAll('input, textarea, .wl-editor, .wl-input, select').forEach((el) => {
    if (!vis(el)) return;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    forms.push({
      el: label(el), type: el.getAttribute('type') || el.tagName.toLowerCase(),
      width: R(r.width), height: R(r.height), right: R(r.right),
      fontSize: cs.fontSize, overflowX: cs.overflowX,
      placeholder: (el.getAttribute('placeholder') || '').slice(0, 30),
    });
  });
  out.formControls = forms.slice(0, 30);

  // ---- 7. Waline 容器 ----
  const wl = [];
  document.querySelectorAll('#waline, .waline, .wl-cards, .wl-panel, .wl-editor').forEach((el) => {
    if (!vis(el)) return;
    const r = el.getBoundingClientRect();
    wl.push({ el: label(el), w: R(r.width), h: R(r.height), right: R(r.right),
              scrollW: el.scrollWidth, clientW: el.clientWidth });
  });
  out.waline = wl;

  return out;
}
"""


async def smooth_scroll(page):
    """滚到底再回顶，触发懒加载与 Waline 渲染"""
    try:
        h = await page.evaluate("() => document.documentElement.scrollHeight")
        y = 0
        while y < h:
            y += 700
            await page.evaluate(f"() => window.scrollTo(0, {y})")
            await page.wait_for_timeout(120)
            h = await page.evaluate("() => document.documentElement.scrollHeight")
        await page.evaluate("() => window.scrollTo(0, 0)")
        await page.wait_for_timeout(300)
    except Exception as e:
        print("  scroll warn:", e)


async def audit_page(page, name, url):
    print(f"[*] {name} -> {url}")
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        await page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        print("  networkidle timeout, continue")
    await page.wait_for_timeout(2500)

    await smooth_scroll(page)
    await page.wait_for_timeout(1500)

    data = await page.evaluate(JS_PROBE)
    data["url"] = url
    data["finalUrl"] = page.url

    # 截图（全页）
    shot = os.path.join(OUT, name + ".png")
    await page.screenshot(path=shot, full_page=True)
    print(f"  [saved] {shot}")

    # 首屏截图
    shot2 = os.path.join(OUT, name + "-fold.png")
    await page.screenshot(path=shot2, full_page=False)

    # 原始 JSON
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return data


async def main():
    os.makedirs(OUT, exist_ok=True)
    results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--ignore-certificate-errors"])
        ctx = await browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            user_agent=UA,
            locale="zh-CN",
            ignore_https_errors=True,
        )
        page = await ctx.new_page()
        page.on("console", lambda m: None)
        for name, url in PAGES:
            try:
                results[name] = await audit_page(page, name, url)
            except Exception as e:
                print(f"  [ERROR] {name}: {e}")
                results[name] = {"url": url, "error": str(e)}
        await browser.close()

    with open(os.path.join(OUT, "_all.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main())
