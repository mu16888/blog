// ============================================================
// CloudBase 配置 —— 部署前请填写 envId（必填），其余按需改
// 此文件由博客前端直接加载，不含任何密钥（匿名/微信登录走 CloudBase 自带鉴权）。
// ============================================================
window.CLOUDBASE_CONFIG = {
  // 你的 CloudBase 环境 ID（腾讯云控制台 → 云开发 → 环境概览 获取）
  envId: "mufeng-blog-d0g1cd76cd6d944e8",

  // 新版 @cloudbase/js-sdk 的「全量 SDK」CDN 地址（默认官方源）。
  // 前端已内置多 CDN 容错：官方源失败会自动回退 jsdelivr / unpkg，无需你手动改。
  // 仅当你的网络三个 CDN 都不可达时，才手动把 SDK 下载到 static/js/cloudbase-sdk.js，
  // 并将本行改为 "/js/cloudbase-sdk.js"。
  sdkUrl: "https://tcb.cloudbase.net/cloudbase-js-sdk/latest/index.js",

  // 统一云函数名（见 cloudbase/functions/interact，需部署到 CloudBase）
  cloudFn: "interact",

  // 文档类登录墙开关：false = 所有内容公开（默认，先留接口）；true = /docs/ 下文章需登录可见
  docGatingEnabled: false,

  // 微信登录入口：留空则前端不显示「微信登录」按钮。
  // 填你的公众号 AppID（需 CloudBase 已开启「微信授权」登录方式并绑定该公众号）。
  wechatAppId: ""
};
