// ============================================================
// CloudBase 云函数 interact（加固版 · 支持双通道）
// 通道A：Web SDK callFunction（正常 SDK 调用）
// 通道B：HTTP 访问服务直连（免费版无法加 Web 安全域名时的绕行方案）
//        走 HTTP 触发时 event 为 { httpMethod, headers, body, isBase64Encoded, ... }
// 能力：计数读取/自增 + 留资写入
// 加固点：
//   ① 内存限频 —— HTTP 模式按客户端 IP + slug + field 去重（SDK 模式按 UID）
//   ② 读数缓存 —— getCounts 30s TTL，降低数据库读次数
//   ③ 留资白名单 + honeypot + UA 记录 —— 防机器人垃圾留资
//   ④ reads 单独 5s 兜底窗口（前端已按天去重，此为第二道防线）
// 安全：所有写操作均经此函数（服务端可信），前端无数据库写权限。
// 依赖：@cloudbase/node-sdk（云函数运行时内置）
// ============================================================
const cloud = require("@cloudbase/node-sdk");
const app = cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = app.database();
const _ = db.command;

const FIELDS = ["reads", "likes", "favorites", "shares", "follows"];
const LEAD_TYPES = ["wechat", "email", "phone", "other"];

// ---- CORS 响应头（HTTP 直连模式必须，允许博客域名跨域调用）----
const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",            // 公开统计接口，无敏感数据，放开来源即可
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Max-Age": "86400"
};

// ---- 限频窗口（毫秒）：同一 key 在窗口内只放行一次 ----
const RL_WINDOW = {
  reads: 5000,      // 阅读兜底去重 5s
  likes: 10000,     // 互动按钮 10s
  favorites: 10000,
  shares: 10000,
  follows: 10000,
  lead: 60000       // 留资 60s
};
const rl = Object.create(null); // key -> 上次放行时间戳
function rateLimited(key, windowMs) {
  const now = Date.now();
  const last = rl[key] || 0;
  if (now - last < windowMs) return true; // 仍在窗口内 → 拦截
  rl[key] = now;
  return false; // 放行
}

// ---- 读数缓存：降数据库读（TTL 30s；incr 成功后失效以便返回最新值）----
const CACHE_TTL = 30000;
const cache = Object.create(null); // slug -> { ts, counts }
async function readCounts(slug) {
  const hit = cache[slug];
  const now = Date.now();
  if (hit && now - hit.ts < CACHE_TTL) return hit.counts;
  const res = await db.collection("counters").doc(slug).get();
  const row = (res.data && res.data[0]) || {};
  const counts = {};
  FIELDS.forEach((f) => { counts[f] = row[f] || 0; });
  cache[slug] = { ts: now, counts };
  return counts;
}

// 客户端标识：SDK 登录态 → IP 头 → 兜底 anon
async function getClientKey(headers) {
  try {
    const state = await app.auth().getLoginState();
    if (state && state.user && state.user.uid) return state.user.uid;
  } catch (e) { /* HTTP 触发无登录态，走 IP */ }
  const h = headers || {};
  const ip = h["x-real-ip"] || (h["x-forwarded-for"] || "").split(",")[0].trim();
  return ip ? "ip:" + ip : "anon";
}

// ---- 业务主体（两种通道共用）----
async function handler(data, clientKey) {
  const action = data.action;
  const slug = data.slug;

  if (action === "getCounts") {
    if (!slug) return { ok: false, msg: "slug required" };
    const counts = await readCounts(slug);
    return { ok: true, counts };
  }

  if (action === "incr") {
    const field = data.field;
    if (!slug || !field || !FIELDS.includes(field)) return { ok: false, msg: "bad params" };
    // 限频：窗口内重复请求不重复自增，直接返回当前计数（带 throttled 标记）
    if (rateLimited(clientKey + ":" + slug + ":" + field, RL_WINDOW[field] || 10000)) {
      const counts = await readCounts(slug);
      return { ok: true, counts, throttled: true };
    }
    const upd = await db.collection("counters").doc(slug).update({ [field]: _.inc(1) }).catch(() => ({ updated: 0 }));
    if (!upd.updated) {
      await db.collection("counters").doc(slug).set({ _id: slug, [field]: 1 }).catch(() => {});
    }
    delete cache[slug]; // 失效缓存
    const counts = await readCounts(slug); // 重建缓存 + 返回最新
    return { ok: true, counts };
  }

  if (action === "lead") {
    // honeypot：机器人自动填充的隐藏字段，收到非空即判定为垃圾
    if ((data._hp || "").trim()) return { ok: false, msg: "spam" };
    const contact = (data.contact || "").trim();
    const type = data.type;
    if (!contact || !LEAD_TYPES.includes(type)) return { ok: false, msg: "contact & valid type required" };
    if (!/^[一-龥\w.@+\-]{2,60}$/.test(contact)) return { ok: false, msg: "bad contact" };
    if (rateLimited(clientKey + ":lead", RL_WINDOW.lead)) return { ok: false, msg: "too frequent" };
    await db.collection("leads").add({
      client: clientKey,
      contact,
      type,
      note: (data.note || "").slice(0, 200),
      ua: (data.ua || "").slice(0, 200),
      created_at: new Date().toISOString()
    });
    return { ok: true };
  }

  return { ok: false, msg: "unknown action" };
}

exports.main = async (event) => {
  // ---- 通道B：HTTP 访问服务直连 ----
  if (event && event.httpMethod) {
    // 预检请求直接放行
    if (event.httpMethod === "OPTIONS") {
      return { statusCode: 204, headers: CORS_HEADERS, body: "" };
    }
    if (event.httpMethod !== "POST") {
      return { statusCode: 405, headers: CORS_HEADERS, body: JSON.stringify({ ok: false, msg: "method not allowed" }) };
    }
    let data = {};
    try {
      let raw = event.body || "{}";
      if (event.isBase64Encoded) raw = Buffer.from(raw, "base64").toString("utf8");
      data = JSON.parse(raw);
    } catch (e) {
      return { statusCode: 400, headers: CORS_HEADERS, body: JSON.stringify({ ok: false, msg: "bad json" }) };
    }
    const clientKey = await getClientKey(event.headers);
    const result = await handler(data, clientKey);
    return { statusCode: 200, headers: CORS_HEADERS, body: JSON.stringify(result) };
  }

  // ---- 通道A：Web SDK callFunction ----
  const clientKey = await getClientKey(null);
  return handler(event || {}, clientKey);
};
