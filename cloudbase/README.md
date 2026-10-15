# 博客统计 / 留资 / 登录后端（腾讯云 CloudBase）

博客静态站部署在 Cloudflare Pages，统计与留资数据走 **腾讯云 CloudBase（云开发）**——
国内数据中心、不出境；原生带匿名/微信登录与数据库权限规则，覆盖了「未来登录用户权限比游客高（文档类）」的扩展需求。

## 架构
- Cloudflare Pages 托管静态站（不变），前端 `static/js/cloudbase-stats.js` 经 `tcb-js-sdk` 直连 CloudBase（天然 CORS）。
- 游客：CloudBase **匿名登录**（自动 UID）→ 可浏览、点赞/收藏/转发/关注、留资。
- 登录用户：配置公众号 AppID 后，前端「微信登录」按钮一键登录，拿真实 openid。
- 所有写操作走云函数 `interact`（服务端可信），前端不直接改库。
- 文档墙：`cloudbase-config.js` 的 `docGatingEnabled` 开 = `/docs/` 下文章需登录可见（现默认关，留接口）。

## 防刷与缓存设计（已内置，无需额外配置）
- **前端去重（第一道）**：阅读数按「浏览器 + 当天」localStorage 去重，防止刷新/连开刷阅读量；点赞/收藏/转发/关注按「浏览器 + 篇目」持久去重并显示「已点」态，防重复点击；留资表单 5s 前端防连点。
- **服务端限频（第二道）**：云函数 `interact` 按 `UID+slug+field` 内存限频（互动按钮 10s、留资 60s、阅读 5s 兜底窗口），窗口内重复请求不重复自增，直接返回当前计数（带 `throttled` 标记）。
- **读数缓存**：`getCounts` 30s TTL 内存缓存，降低数据库读次数（个人站量级下免费额度绰绰有余）。
- **机器人防护**：留资表单内置 honeypot 隐藏字段，CloudBase 端收到非空即判定为垃圾拒绝；并限制留资类型白名单（`wechat/email/phone/other`）+ 联系方式格式校验。
- 说明：serverless 内存限频在冷启动时重置，故与前端去重构成**双层防护**，个人内容号足够；若日后需硬限频，再加 Turnstile 人机验证或云函数实例级持久计数即可。

## 你需要做的（控制台，涉及你的账号凭证，来福不碰）

> ⚠️ **2026-10-15 实测更新**：免费体验版**加不了 Web 安全域名**（API 报 `OperationDenied.FreePackageDenied`，官方套餐限制）。
> 因此前端已改为 **HTTP 直连云函数**（不依赖 Web SDK / 匿名登录 / 域名白名单），原第 2、3 步不再必需，新增第 7 步。
> 防刷能力不受影响：函数按客户端 IP 限频（互动 10s / 留资 60s / 阅读 5s）+ 前端 localStorage 双层去重。

1. ~~新建环境~~ ✅ 已完成：环境 ID `mufeng-blog-d0g1cd76cd6d944e8`（上海，体验版，到期 2027-04-15）。
2. ~~开匿名登录~~ 已开（备用，当前架构用不到）。
3. ~~Web 安全域名~~ **免费版加不了，跳过**（升级个人版 ¥19.9/月 后可补加，届时可切回 SDK 模式）。
4. **建数据库集合**：左侧「文档型数据库」→ 点 **新建集合** → 依次建 `counters`、`leads`（集合权限默认即可，写操作由云函数服务端完成）。
5. **部署云函数**：左侧「云函数」→ 点 **新建云函数** → 函数名填 `interact`（一字不差）→ 运行环境 Node.js → 创建后进在线编辑器，把本仓库 `cloudbase/functions/interact/index.js` 整段粘贴进 `index.js`，`package.json` 同样替换 → 点 **保存并安装依赖**（必须点这个）→ 等状态"部署成功"。
6. **开 HTTP 访问服务（关键新步骤）**：进入函数 `interact` → 找「HTTP 访问服务」（或「触发」标签）→ 开启/创建路由，**触发路径填 `/interact`** → 保存后复制完整访问地址，形如
   `https://mufeng-blog-d0g1cd76cd6d944e8.service.tcloudbase.com/interact`
   （新版控制台也可能是 `https://mufeng-blog-d0g1cd76cd6d944e8.ap-shanghai.app.tcloudbase.com/interact` 格式，以页面显示为准）。
7. **回填 apiUrl**：把第 6 步复制的地址发来福（或自己填进 `static/js/cloudbase-config.js` 的 `apiUrl` 字段）→ git push → Cloudflare 自动部署 → 线上联调。

## 本地验证（来福做 / 你也可做）
- 仓库根：`hugo --minify -d _buildtest` 确认页面含统计条、按钮、留资表单，无报错。
- CloudBase 侧：用测试环境联调匿名登录、计数自增、留资写入。

## 发布
- 改完 `cloudbase-config.js` 后，`git add . && git commit && git push origin main` → Cloudflare 自动部署。
- 线上实测：开文章阅读+1、点按钮计数变、提交表单 `leads` 多一条。

## 费用
- CloudBase 免费体验版 ¥0/月（3000 资源点）；个人版 ¥19.9/月可选。博客量级远低于免费额度。
