// ============================================================
// CloudBase 配置 —— 部署前请填写 envId（必填），其余按需改
// 此文件由博客前端直接加载，不含任何密钥（匿名/微信登录走 CloudBase 自带鉴权）。
// ============================================================
window.CLOUDBASE_CONFIG = {
  // 你的 CloudBase 环境 ID（腾讯云控制台 → 云开发 → 环境概览 获取）
  envId: "YOUR_ENV_ID",

  // 新版 @cloudbase/js-sdk 的「全量 SDK」CDN 地址。
  // 若下方默认地址失效（如返回 502），请到 CloudBase 文档「Web 端 SDK → 通过 CDN 引入」
  // 复制最新的 <script src> 替换本行即可。
  sdkUrl: "https://tcb.cloudbase.net/cloudbase-js-sdk/latest/index.js",

  // 统一云函数名（见 cloudbase/functions/interact，需部署到 CloudBase）
  cloudFn: "interact",

  // 文档类登录墙开关：false = 所有内容公开（默认，先留接口）；true = /docs/ 下文章需登录可见
  docGatingEnabled: false,

  // 微信登录入口：留空则前端不显示「微信登录」按钮。
  // 填你的公众号 AppID（需 CloudBase 已开启「微信授权」登录方式并绑定该公众号）。
  wechatAppId: ""
};
