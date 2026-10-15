// ============================================================
// 站点级 PV / UV 统计 —— 复用博客已有的 CloudBase 云函数 interact
// 不再用第三方不蒜子（国内访问不稳，计数常年显示 0）。
// 计数写入 counters 集合的两个特殊文档：
//   site-pv —— 站点总访问（页面浏览量）
//   site-uv —— 站点访客数（按天 localStorage 去重，近似 UV）
// 防刷：① 前端按天去重（同一天同一浏览器只算一次）
//       ② 云函数侧 5s 限频兜底（同 IP 5s 内只 +1）
// ============================================================
(function () {
  "use strict";
  var cfg = window.CLOUDBASE_CONFIG || {};
  var API_URL = cfg.apiUrl || "";
  if (!API_URL || API_URL.indexOf("PASTE_") === 0) return;

  function todayKey() {
    var d = new Date();
    return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate();
  }
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  function callFn(data) {
    var ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, 8000) : null;
    return fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      signal: ctrl ? ctrl.signal : undefined
    }).then(function (res) {
      if (timer) clearTimeout(timer);
      if (!res.ok) return { ok: false };
      return res.json().catch(function () { return { ok: false }; });
    }).catch(function () {
      if (timer) clearTimeout(timer);
      return { ok: false };
    });
  }

  function paint(id, v) {
    var el = document.getElementById(id);
    if (el) el.textContent = v;
  }

  function boot() {
    var day = todayKey();

    // 1) 先读当前 PV / UV 显示出来
    callFn({ action: "getCounts", slug: "site-pv" }).then(function (r) {
      if (r.ok && r.counts) paint("site-pv", r.counts.reads || 0);
    });
    callFn({ action: "getCounts", slug: "site-uv" }).then(function (r) {
      if (r.ok && r.counts) paint("site-uv", r.counts.reads || 0);
    });

    // 2) 当天首次访问才 +1（PV/UV 同一天只计一次，防刷新刷量）
    //    标记只在「写入成功」后才落盘：请求失败下次访问会重试，
    //    避免旧实现「先落标记再请求」导致一次失败当天永久停摆。
    var pvFlag = "site_pv_" + day;
    var uvFlag = "site_uv_" + day;

    if (lsGet(pvFlag) !== "1") {
      callFn({ action: "incr", slug: "site-pv", field: "reads" }).then(function (r) {
        if (r.ok && r.counts) paint("site-pv", r.counts.reads || 0);
        // 仅在真实写入成功（未被限频）时才落标记
        if (r.ok && !r.throttled) lsSet(pvFlag, "1");
      });
    }
    if (lsGet(uvFlag) !== "1") {
      callFn({ action: "incr", slug: "site-uv", field: "reads" }).then(function (r) {
        if (r.ok && r.counts) paint("site-uv", r.counts.reads || 0);
        if (r.ok && !r.throttled) lsSet(uvFlag, "1");
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
