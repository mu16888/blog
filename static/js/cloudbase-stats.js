// ============================================================
// 博客统计 / 留资 前端逻辑 —— HTTP 直连云函数版
// 走 CloudBase「HTTP 访问服务」默认域名直连云函数 interact，
// 不依赖 Web SDK / 匿名登录 / Web安全域名（免费版加不了域名白名单）。
// 加固：① 阅读数按天 localStorage 去重（防刷新刷阅读量）
//       ② 互动按钮 localStorage 持久去重 + 已点态（防重复点赞/收藏/转发/关注）
//       ③ 留资 honeypot 防机器人 + 前端 5s 防连点
//       ④ 服务端另有按 IP 限频兜底（见 cloudbase/functions/interact/index.js）
// ============================================================
(function () {
  "use strict";
  var cfg = window.CLOUDBASE_CONFIG || {};
  var API_URL = cfg.apiUrl || "";
  if (!API_URL || API_URL.indexOf("PASTE_") === 0) {
    if (navigator && !navigator.webdriver) {
      console.warn("[mufeng-stats] 未配置云函数 HTTP 访问地址，统计/留资未启用。请在 static/js/cloudbase-config.js 填写 apiUrl。");
    }
    return;
  }

  var FIELDS = ["reads", "likes", "favorites", "shares", "follows"];

  function todayKey() {
    var d = new Date();
    return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate();
  }
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  // 直连云函数：POST JSON，函数侧已带 CORS 头
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
      if (!res.ok) return { ok: false, msg: "http " + res.status };
      return res.json().catch(function () { return { ok: false, msg: "bad json" }; });
    }).catch(function (e) {
      if (timer) clearTimeout(timer);
      console.warn("[mufeng-stats] 接口不可达", e && e.message);
      return { ok: false };
    });
  }

  function boot() {
    var box = document.querySelector(".mufeng-stats");
    if (!box) return;
    var slug = box.getAttribute("data-slug");

    // 1) 读取计数（含阅读数）
    callFn({ action: "getCounts", slug: slug }).then(function (r) {
      if (!r.ok) return;
      FIELDS.forEach(function (f) {
        var el = document.getElementById("ms-" + f);
        if (el) el.textContent = (r.counts && r.counts[f]) || 0;
      });
    });

    // 2) 阅读数：当天首次访问才 +1（防刷新/连开刷量）；云函数另有 5s 兜底
    var readKey = "ms_read_" + slug;
    var readDone = false;
    try { var rv = lsGet(readKey); readDone = rv && JSON.parse(rv).date === todayKey(); } catch (e) {}
    if (!readDone) {
      callFn({ action: "incr", slug: slug, field: "reads" }).then(function (r) {
        // 仅在真实写入成功后才落标记：请求失败（网络抖动/超时）时下次访问会重试，
        // 避免一次失败就当天永久停摆。
        if (r.ok && !r.throttled) lsSet(readKey, JSON.stringify({ date: todayKey() }));
        if (r.ok) {
          var el = document.getElementById("ms-reads");
          if (el) el.textContent = (r.counts && r.counts.reads) || 0;
        }
      });
    }

    // 3) 点赞 / 收藏 / 转发 / 关注：localStorage 持久去重 + 已点态（防重复 + 防刷）
    box.querySelectorAll(".ms-btn[data-field]").forEach(function (btn) {
      var field = btn.getAttribute("data-field");
      var doneKey = "ms_" + field + "_" + slug;
      if (lsGet(doneKey) === "1") { btn.disabled = true; btn.classList.add("ms-done"); return; }
      btn.addEventListener("click", function () {
        if (btn.disabled) return;
        btn.disabled = true;
        callFn({ action: "incr", slug: slug, field: field }).then(function (r) {
          if (r.ok) {
            var el = document.getElementById("ms-" + field);
            if (el) el.textContent = (r.counts && r.counts[field]) || 0;
            // 仅当真实 +1（未触发限频）才持久标记为已点，避免误锁按钮
            if (!r.throttled) { lsSet(doneKey, "1"); btn.classList.add("ms-done"); }
          }
          setTimeout(function () { btn.disabled = false; }, 1200);
        });
      });
    });

    // 4) 留资表单：honeypot 防机器人 + 前端 5s 防连点
    var form = document.getElementById("ms-lead-form");
    if (form) {
      var submitBtn = form.querySelector('button[type="submit"]');
      var lastSubmit = 0;
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var now = Date.now();
        if (now - lastSubmit < 5000) return; // 前端防连点
        lastSubmit = now;
        var contact = (form.contact.value || "").trim();
        var type = form.type.value;
        var note = (form.note.value || "").trim();
        if (!contact) return;
        var msg = document.getElementById("ms-lead-msg");
        msg.textContent = "提交中…";
        if (submitBtn) { submitBtn.disabled = true; setTimeout(function () { submitBtn.disabled = false; }, 5000); }
        callFn({
          action: "lead",
          contact: contact,
          type: type,
          note: note,
          _hp: (form._hp ? form._hp.value : ""),
          ua: navigator.userAgent
        }).then(function (r) {
          if (r.ok) { msg.textContent = "已收到，谢谢！"; form.reset(); }
          else msg.textContent = "提交失败：" + (r.msg || "");
        });
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
