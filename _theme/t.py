import json, asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch()
        ctx=await b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,is_mobile=True,has_touch=True)
        pg=await ctx.new_page()
        out={}
        for name in ["light","dark"]:
            await pg.goto("https://mufeng168.top/",wait_until="networkidle",timeout=60000)
            await pg.evaluate(f"document.documentElement.setAttribute('data-theme','{name}')")
            await pg.wait_for_timeout(800)
            d=await pg.evaluate("""()=>{
              const g=(s)=>{const e=document.querySelector(s);return e?getComputedStyle(e):null};
              const body=getComputedStyle(document.body);
              const card=document.querySelector('.post-card,.widget-simple,.funnel-card');
              return {
                htmlAttrs:[...document.documentElement.attributes].map(a=>a.name+'='+a.value).join(' '),
                bodyBg: body.backgroundColor, bodyImg: body.backgroundImage.slice(0,60),
                bodyColor: body.color,
                varBg: getComputedStyle(document.documentElement).getPropertyValue('--background').trim(),
                varFg: getComputedStyle(document.documentElement).getPropertyValue('--foreground').trim(),
                varCard: getComputedStyle(document.documentElement).getPropertyValue('--card').trim(),
                cardBg: card?getComputedStyle(card).backgroundColor:null,
                headerBg: g('.site-header__inner')?g('.site-header__inner').backgroundColor:null
              };
            }""")
            out[name]=d
            await pg.screenshot(path=f"theme-{name}.png")
        await b.close()
    print(json.dumps(out,ensure_ascii=False,indent=1))
asyncio.run(main())
