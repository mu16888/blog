// ============================================================
// 博客统计 / 留资 / 登录墙 前端逻辑（依赖 CloudBase Web SDK）
// 加固：① 阅读数按天 localStorage 去重（防刷新刷阅读量）
//       ② 互动按钮 localStorage 持久去重 + 已点态（防重复点赞/收藏/转发/关注）
//       ③ 留资 honeypot 防机器人 + 前端 5s 防连点
// 所有写操作走云函数 interact（服务端可信），前端不直接改库。
// ============================================================
(function () {
  "use strict";
  var cfg = window.CLOUDBASE_CONFIG || {};
  if (!cfg.envId || cfg.envId === "YOUR_ENV_ID") {
    if (navigator && !navigator.webdriver) {
      console.warn("[mufeng-stats] 未配置 CloudBase envId，统计/留资未启用。请在 static/js/cloudbase-config.js 填写。");
    }
    return;
  }

  var app = null, auth = null;
  var FIELDS = ["reads", "likes", "favorites", "shares", "follows"];

  function todayKey() {
    var d = new Date();
    return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate();
  }
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  function injectSDK(cb) {
    if (window.cloudbase) return cb();
    if (!cfg.sdkUrl) {
      console.error("[mufeng-stats] 缺少 sdkUrl，无法加载 CloudBase SDK（请到 CloudBase 文档复制最新 CDN 地址）。");
      return;
    }
    var s = document.createElement("script");
    s.src = cfg.sdkUrl;
    s.onload = cb;
    s.onerror = function () {
      console.error("[mufeng-stats] SDK 加载失败，请检查 cloudbase-config.js 的 sdkUrl（CloudBase 文档 → Web 端 SDK → 通过 CDN 引入）。");
    };
    document.head.appendChild(s);
  }

  function initApp() {
    try {
      if (window.cloudbase.registerAuth) window.cloudbase.registerAuth(window.cloudbase);
      app = window.cloudbase.init({ env: cfg.envId });
      auth = app.auth();
    } catch (e) {
      console.error("[mufeng-stats] init error", e);
      return;
    }
    anonLogin();
  }

  // 游客自动匿名登录（免注册即可互动）；失败也继续（仅浏览/留资降级）
  function anonLogin() {
    var p;
    try { p = auth.signIn({ anonymous: true }); }
    catch (e) { p = auth.signInAnonymously ? auth.signInAnonymously() : Promise.reject(e); }
    Promise.resolve(p)
      .then(boot)
      .catch(function (e) { console.warn("[mufeng-stats] 匿名登录失败，互动降级为仅浏览", e); boot(); });
  }

  function callFn(data) {
    if (!app) return Promise.resolve({ ok: false });
    return app.callFunction({ name: cfg.cloudFn || "interact", data: data })
      .then(function (r) { return (r && r.result) || {}; })
      .catch(function (e) { console.error("[mufeng-stats] fn error", e); return { ok: false }; });
  }

  function boot() {
    var box = document.querySelector(".mufeng-stats");
    if (!box) return;
    var slug = box.getAttribute("data-slug");

    if (cfg.docGatingEnabled) applyDocGate();

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
        lsSet(readKey, JSON.stringify({ date: todayKey() })); // 无论是否 throttled，当天不再重试
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

    // 5) 微信登录入口（仅当配置了 wechatAppId）
    var wxBtn = document.getElementById("ms-wechat");
    if (wxBtn && cfg.wechatAppId) {
      wxBtn.hidden = false;
      wxBtn.addEventListener("click", function () {
        try {
          auth.signIn({ wechat: { appId: cfg.wechatAppId, scope: "snsapi_base", redirectUrl: location.href } });
        } catch (e) {
          if (auth.wechatAuthProvider) auth.wechatAuthProvider({ appid: cfg.wechatAppId }).signIn();
        }
      });
    }
  }

  // 文档墙：docGatingEnabled 开启且当前是 /docs/ 文章时，未登录则隐藏正文、显示提示
  function applyDocGate() {
    var isDoc = location.pathname.indexOf("/docs/") === 0;
    if (!isDoc || !auth) return;
    var content = document.querySelector(".article-content");
    var gate = document.getElementById("ms-doc-gate");
    auth.getLoginState().then(function (st) {
      var logged = st && st.user;
      if (!logged) {
        if (content) content.style.display = "none";
        if (gate) gate.hidden = false;
      }
    }).catch(function () {
      if (content) content.style.display = "none";
      if (gate) gate.hidden = false;
    });
  }

  injectSDK(initApp);
})();
