/* ══════════════════════════════════════════════════════════════
   移动端只保留浅色主题 + 调色板锁定（2026-10-21 锋哥令）
   「手机端深浅没有太大区别干脆移动端只有浅色就好了」

   为什么需要这个脚本（CSS 已经兜住了，这里是行为层的第二道保险）：
     ① 主题 main.js 会监听 prefers-color-scheme 的 change 事件，
        系统切深色时把 data-theme 改成 "dark"；
     ② 主题 main.js:103 applyPalette(resolvePalette()) 会读 localStorage 的
        'PocketPalettePreset' 并应用 —— 项目虽已隐藏调色板 UI（showPicker=false），
        但这段 JS 仍在跑 → 残留旧值会让 data-palette 变成别的色系，
        导致 custom.css 里所有 [data-palette="deep-sea-blue"] 覆盖全部失效，
        站点退回主题默认暖米色系（暖褐底 + 粉白标题 + 米黄卡片）。
     ③ 手机浏览器开「桌面版网站」时 CSS 视口 ≥768px，
        只靠 max-width 判定会漏 → 因此加 (pointer:coarse) 触屏判定。

   桌面端（真桌面浏览器，非触屏）完全不受影响。
   ══════════════════════════════════════════════════════════════ */
(function () {
    var root = document.documentElement;
    var SITE_PALETTE = 'deep-sea-blue';

    var narrow = window.matchMedia('(max-width: 767px)');
    var coarse = window.matchMedia('(pointer: coarse)');
    function isMobile() { return narrow.matches || coarse.matches; }

    function fix() {
        /* 调色板锁定：无论主题 JS 写了什么，都强制回到品牌色系 */
        if (root.dataset.palette !== SITE_PALETTE) {
            root.dataset.palette = SITE_PALETTE;
        }
        if (!isMobile()) return;
        /* 移动端强制浅色 */
        if (root.dataset.theme !== 'light') {
            root.dataset.theme = 'light';
            root.dataset.scheme = 'light';
        }
        if (root.style.colorScheme !== 'light') {
            root.style.colorScheme = 'light';
        }
    }

    /* 立即执行一次 */
    fix();
    /* 主题 main.js 是 defer 加载、可能在本脚本之后才执行并覆盖 → 延迟纠正 */
    window.setTimeout(fix, 0);
    window.setTimeout(fix, 200);
    window.setTimeout(fix, 800);
    /* DOMContentLoaded 触发时，所有 defer 脚本（含主题 main.js）均已执行完 → 再兜一次 */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fix);
    } else {
        fix();
    }

    /* 视口 / 设备类型变化 */
    var onChange = function () { fix(); };
    if (narrow.addEventListener) narrow.addEventListener('change', onChange);
    else if (narrow.addListener) narrow.addListener(onChange);
    if (coarse.addEventListener) coarse.addEventListener('change', onChange);
    else if (coarse.addListener) coarse.addListener(onChange);

    /* 系统配色偏好变化时（主题 main.js 会把 data-theme 改成 dark）再纠正 */
    var media = window.matchMedia('(prefers-color-scheme: dark)');
    var onMedia = function () {
        window.setTimeout(fix, 0);
        window.setTimeout(fix, 50);
    };
    if (media.addEventListener) media.addEventListener('change', onMedia);
    else if (media.addListener) media.addListener(onMedia);

    /* 兜底轮询：主题 main.js 可能在任意时刻写入 dark / 错误 palette */
    window.setInterval(function () {
        fix();
    }, 1000);
})();
