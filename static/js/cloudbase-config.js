// ============================================================
// CloudBase 配置 —— HTTP 直连版
// 免费体验版加不了 Web安全域名（OperationDenied.FreePackageDenied），
// 故前端不走 Web SDK/匿名登录，直接 POST 云函数的 HTTP 访问地址。
// 此文件不含任何密钥；防刷靠函数内 IP 限频 + 前端 localStorage 去重。
// ============================================================
window.CLOUDBASE_CONFIG = {
  // CloudBase 环境 ID（仅备注用，前端实际用的是下面的 apiUrl）
  envId: "mufeng-blog-d0g1cd76cd6d944e8",

  // 云函数 interact 的 HTTP 访问地址（必填）。
  // 获取方式：控制台 → 云函数/托管 → 函数 interact → HTTP 访问服务/触发路径
  //   → 开启并把触发路径设为 /interact → 复制形如
  //   https://mufeng-blog-d0g1cd76cd6d944e8.service.tcloudbase.com/interact
  apiUrl: "https://mufeng-blog-d0g1cd76cd6d944e8-1340448166.ap-shanghai.app.tcloudbase.com/interact",

  // 文档类登录墙开关（需要 SDK 登录，当前架构未启用；保留字段备用）
  docGatingEnabled: false,

  // 微信登录入口（需要 SDK，当前架构未启用；保留字段备用）
  wechatAppId: ""
};
