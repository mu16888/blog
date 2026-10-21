/* ══════════════════════════════════════════════════════════════
   全站浅色锁定 + 调色板锁定（2026-10-21 锋哥令升级版）
   「手机端还是无法使用，干脆取消深色模式只有一种原白色背景」

   原方案是"仅移动端锁浅色"（判定式：视口窄 OR 触屏），但真实设备上
   仍有漏网可能（锋哥手机依旧出现深色）。现升级为**无条件锁浅色**：
   任何设备、任何系统偏好、任何 localStorage 残留，data-theme 恒为 light。

   为什么需要这个脚本（head 内联脚本已经锁了一次，这里是行为层保险）：
     ① 主题 main.js 会监听 prefers-color-scheme 的 change 事件，
        系统切深色时把 data-theme 改成 "dark" → 本脚本持续纠正回 light；
     ② 主题 main.js:103 applyPalette(resolvePalette()) 会读 localStorage 的
        'PocketPalettePreset' 并应用 → 残留旧值会把 data-palette 改成
        别的色系，custom.css 里所有 [data-palette="deep-sea-blue"] 覆盖
        全部失效（症状：暖褐底 + 粉白标题 + 米黄卡片）→ 持续纠正回品牌色系。
   ══════════════════════════════════════════════════════════════ */
(function () {
    var root = document.documentElement;
    var SITE_PALETTE = 'deep-sea-blue';

    function fix() {
        if (root.dataset.theme !== 'light') {
            root.dataset.theme = 'light';
            root.dataset.scheme = 'light';
        }
        if (root.style.colorScheme !== 'light') {
            root.style.colorScheme = 'light';
        }
        /* 调色板锁定：无论主题 JS 写了什么，都强制回到品牌色系 */
        if (root.dataset.palette !== SITE_PALETTE) {
            root.dataset.palette = SITE_PALETTE;
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

    /* 系统配色偏好变化时（主题 main.js 会把 data-theme 改成 dark）再纠正 */
    var media = window.matchMedia('(prefers-color-scheme: dark)');
    var onMedia = function () {
        window.setTimeout(fix, 0);
        window.setTimeout(fix, 50);
    };
    if (media.addEventListener) media.addEventListener('change', onMedia);
    else if (media.addListener) media.addListener(onMedia);

    /* 兜底轮询：主题 main.js 可能在任意时刻写入 dark / 错误 palette */
    window.setInterval(fix, 1000);
})();
