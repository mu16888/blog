/* ══════════════════════════════════════════════════════════════
   移动端只保留浅色主题（2026-10-21 锋哥令）
   「手机端深浅没有太大区别干脆移动端只有浅色就好了」

   为什么需要这个脚本（CSS 已经兜住了，这里是行为层的第二道保险）：
     ① 主题 head 内联脚本 helpers/color-scheme.html 会读 localStorage 与
        prefers-color-scheme，若系统是深色或用户之前点过深色，
        会把 <html data-theme> 设成 "dark"；
     ② 主题 main.js 监听 prefers-color-scheme 的 change 事件，
        也会在系统切深色时把 data-theme 改成 "dark"；
     ③ 桌面端 localStorage 存的 "dark" 会被手机端读到（同一浏览器同源）。

   CSS 那段把深色变量全拉回浅色，视觉上已经是浅色；但 data-theme 属性
   仍是 "dark"，会影响 <meta name="color-scheme">、系统滚动条/表单控件配色、
   以及少数依赖 [data-theme] 属性的第三方脚本。
   → 这里在移动端强制把 data-theme 拉回 "light"，并持续纠正。
   桌面端（>768px）完全不受影响。
   ══════════════════════════════════════════════════════════════ */
(function () {
    var MQ = window.matchMedia('(max-width: 767px)');
    var root = document.documentElement;

    function forceLight() {
        if (!MQ.matches) return;
        if (root.dataset.theme !== 'light') {
            root.dataset.theme = 'light';
            root.dataset.scheme = 'light';
        }
        if (root.style.colorScheme !== 'light') {
            root.style.colorScheme = 'light';
        }
    }

    // 立即执行一次（脚本放在 body 末尾，DOM 已就绪）
    forceLight();

    // 主题 main.js 是 defer 加载的，可能在本站脚本之后才执行并覆盖 data-theme
    window.setTimeout(forceLight, 0);
    window.setTimeout(forceLight, 200);

    // 视口跨越 768px（如平板旋转、手机横竖屏切换）时重新纠正
    var onChange = function () { forceLight(); };
    if (MQ.addEventListener) {
        MQ.addEventListener('change', onChange);
    } else if (MQ.addListener) {
        MQ.addListener(onChange);
    }

    // 系统配色偏好变化时（主题 main.js 会把 data-theme 改成 dark）再纠正一次
    var media = window.matchMedia('(prefers-color-scheme: dark)');
    var onMedia = function () {
        // 让主题先处理，随后我们再拉回浅色
        window.setTimeout(forceLight, 0);
        window.setTimeout(forceLight, 50);
    };
    if (media.addEventListener) {
        media.addEventListener('change', onMedia);
    } else if (media.addListener) {
        media.addListener(onMedia);
    }

    // 兜底轮询：主题 main.js 可能在任意时刻写入 dark
    var guard = window.setInterval(function () {
        if (!MQ.matches) {
            window.clearInterval(guard);
            return;
        }
        forceLight();
    }, 1000);
})();
