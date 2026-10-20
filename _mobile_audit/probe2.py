# -*- coding: utf-8 -*-
"""补充取证：导航栏 / 页头 / 卡片字号 / 表格代码块 精确定位（只读）"""
import asyncio
import json
import os

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

JS = r"""
() => {
  const vw = window.innerWidth, R = n => Math.round(n*10)/10;
  const out = {};
  const vis = el => { const cs=getComputedStyle(el);
    if(cs.display==='none'||cs.visibility==='hidden'||parseFloat(cs.opacity)===0) return false;
    const r=el.getBoundingClientRect(); return !(r.width===0&&r.height===0); };
  const lb = el => { const id=el.id?'#'+el.id:''; let c='';
    if(typeof el.className==='string'&&el.className.trim()) c='.'+el.className.trim().split(/\s+/).slice(0,4).join('.');
    return el.tagName.toLowerCase()+id+c; };

  // ---------- 导航栏精测 ----------
  const navs = [];
  document.querySelectorAll('nav, .main-nav, .nav').forEach(n => {
    if(!vis(n)) return;
    const r = n.getBoundingClientRect(); const cs = getComputedStyle(n);
    const items = [];
    n.querySelectorAll('a,button,li').forEach(a => {
      if(!vis(a)) return;
      const ar = a.getBoundingClientRect();
      const acs = getComputedStyle(a);
      items.push({ el: lb(a), left: R(ar.left), right: R(ar.right), w: R(ar.width), h: R(ar.height),
        text: (a.textContent||'').trim().replace(/\s+/g,' ').slice(0,20),
        fs: acs.fontSize, pad: acs.padding, href: (a.getAttribute('href')||'').slice(0,40),
        active: a.className.indexOf('active')>=0 || a.getAttribute('aria-current')!==null,
        // 命中测试：该链接中心点是否真能点到自己
        hitTest: (() => {
          const cx = ar.left + ar.width/2, cy = ar.top + ar.height/2;
          if (cx < 0 || cx > vw || cy < 0 || cy > window.innerHeight) return 'offscreen';
          const top = document.elementFromPoint(cx, cy);
          if (!top) return 'null';
          return (top === a || a.contains(top)) ? 'clickable' : ('blocked-by:'+lb(top));
        })()
      });
    });
    // 向上找真正的滚动容器
    let sc = n, scrollInfo = null;
    while (sc && sc !== document.documentElement) {
      const scs = getComputedStyle(sc);
      if (['auto','scroll'].indexOf(scs.overflowX) >= 0 || sc.scrollWidth > sc.clientWidth + 1) {
        scrollInfo = scrollInfo || { el: lb(sc), scrollW: sc.scrollWidth, clientW: sc.clientWidth,
                                     scrollLeft: Math.round(sc.scrollLeft), overflowX: scs.overflowX };
      }
      sc = sc.parentElement;
    }
    navs.push({
      el: lb(n), left: R(r.left), right: R(r.right), w: R(r.width), h: R(r.height),
      scrollW: n.scrollWidth, clientW: n.clientWidth, scrollLeft: Math.round(n.scrollLeft),
      overflowX: cs.overflowX, overflowY: cs.overflowY,
      display: cs.display, flexWrap: cs.flexWrap, whiteSpace: cs.whiteSpace,
      itemsTotal: items.length,
      itemsVisibleInViewport: items.filter(i => i.left >= -1 && i.right <= vw + 1).length,
      itemsFullyHidden: items.filter(i => i.right < 0 || i.left > vw).length,
      items: items,
      scrollInfo,
      // 尝试向右滚动看还有多少内容
      canScrollRight: n.scrollWidth - n.clientWidth - n.scrollLeft,
    });
  });
  out.navs = navs;

  // ---------- 页头精测 ----------
  const hs = [];
  document.querySelectorAll('header, .site-header, #site-header').forEach(h => {
    if(!vis(h)) return;
    const r = h.getBoundingClientRect();
    const parts = [];
    h.querySelectorAll('*').forEach(c => {
      if(!vis(c)) return;
      const cr = c.getBoundingClientRect();
      if (cr.width < 2 || cr.height < 2) return;
      const txt = (c.textContent||'').trim().replace(/\s+/g,' ');
      const tag = c.tagName.toLowerCase();
      // 只保留叶子文本节点 / 图片 / 交互元素
      const isLeaf = c.children.length === 0;
      if (!isLeaf && ['a','button','img','input'].indexOf(tag) < 0) return;
      if (!txt && ['img','input'].indexOf(tag) < 0) return;
      parts.push({ el: lb(c), tag, x: R(cr.left), y: R(cr.top), w: R(cr.width), h: R(cr.height),
                   text: txt.slice(0,22), fs: getComputedStyle(c).fontSize });
    });
    hs.push({ el: lb(h), x: R(r.left), y: R(r.top), w: R(r.width), h: R(r.height),
      scrollW: h.scrollWidth, clientW: h.clientWidth,
      parts: parts.slice(0, 30) });
  });
  out.headers = hs;

  // ---------- 卡片 / 摘要字号（首页 列表页）----------
  const cards = [];
  document.querySelectorAll('article.post-card, .post-card, .card').forEach(c => {
    if(!vis(c)) return;
    const title = c.querySelector('h2,h3,.post-card__title,.card-title');
    const summary = c.querySelector('.post-card__summary, .summary, .excerpt, p');
    const meta = c.querySelector('.post-card__meta, .meta, .post-meta');
    const g = (n) => n ? { el: lb(n), fs: getComputedStyle(n).fontSize, lh: getComputedStyle(n).lineHeight,
                           w: R(n.getBoundingClientRect().width),
                           text: (n.textContent||'').trim().replace(/\s+/g,' ').slice(0,40) } : null;
    cards.push({ el: lb(c), title: g(title), summary: g(summary), meta: g(meta) });
  });
  out.cards = cards.slice(0, 6);

  // ---------- 表格 / 代码块 ----------
  const tb = [];
  document.querySelectorAll('table, pre, .highlight, .chroma, .table-wrapper, figure').forEach(el => {
    if(!vis(el)) return;
    const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    let p = el.parentElement, pInfo = [];
    for (let i=0;i<3 && p;i++){ const pcs=getComputedStyle(p);
      pInfo.push(lb(p)+'[ox='+pcs.overflowX+' sw='+p.scrollWidth+' cw='+p.clientWidth+']'); p=p.parentElement; }
    tb.push({ el: lb(el), w: R(r.width), right: R(r.right), scrollW: el.scrollWidth, clientW: el.clientWidth,
      selfOX: cs.overflowX, parentChain: pInfo,
      rows: el.tagName.toLowerCase()==='table' ? el.querySelectorAll('tr').length : null,
      cols: el.tagName.toLowerCase()==='table' ? (el.querySelectorAll('tr:first-child > *').length) : null });
  });
  out.tables = tb;

  // ---------- 小点击目标明细（带命中测试）----------
  const taps = [];
  document.querySelectorAll('a,button,[role=button]').forEach(el => {
    if(!vis(el)) return;
    const r = el.getBoundingClientRect();
    if (r.height >= 40) return;
    const cs = getComputedStyle(el);
    const inP = (() => { let p=el.parentElement; while(p){ const t=lb(p);
      if(/article-content|post-content|wl-card|wl-cards|wl-panel/.test(t)) return true; p=p.parentElement;} return false; })();
    taps.push({ el: lb(el), h: R(r.height), w: R(r.width), display: cs.display,
      text: (el.textContent||'').trim().replace(/\s+/g,' ').slice(0,26),
      inArticleOrComment: inP, isInline: cs.display.indexOf('inline')>=0,
      fs: cs.fontSize, pad: cs.padding,
      tag: el.tagName.toLowerCase() });
  });
  out.taps = taps;

  // ---------- 点击目标 <40 且非行内 ----------
  out.tapsBlock = taps.filter(t => !t.isInLine && t.display.indexOf('inline') < 0);

  // ---------- 页脚 / 其它 ----------
  const f = document.querySelector('footer');
  out.footer = f ? { el: lb(f), h: R(f.getBoundingClientRect().height),
                     scrollW: f.scrollWidth, clientW: f.clientWidth } : null;

  // 全页最小字号扫描（可见文本节点）
  const fsMap = {};
  document.querySelectorAll('p,span,li,td,div,small,a,label,time').forEach(el => {
    if(!vis(el)) return;
    if (el.children.length > 0) return;
    const t = (el.textContent||'').trim(); if (t.length < 2) return;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < 13) { const k = fs+'px'; fsMap[k] = (fsMap[k]||0)+1; }
  });
  out.tinyText = fsMap;
  out.tinyTextTotal = Object.values(fsMap).reduce((a,b)=>a+b,0);

  return out;
}
"""

async def main():
    res = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--ignore-certificate-errors"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                                  is_mobile=True, has_touch=True, user_agent=UA, locale="zh-CN",
                                  ignore_https_errors=True)
        pg = await ctx.new_page()
        for name, url in PAGES:
            print('[*]', name)
            await pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            try:
                await pg.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            await pg.wait_for_timeout(2500)
            res[name] = await pg.evaluate(JS)
            res[name]["_url"] = url
        await b.close()
    with open(os.path.join(OUT, "_probe2.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("DONE")

asyncio.run(main())
