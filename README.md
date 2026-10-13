# 沐风博客（Hugo + Cloudflare Pages）

静态博客源码。部署：Cloudflare Pages 连 GitHub 仓库 `mu16888/blog`，推送后自动构建发布。

## 本地预览
仓库根目录下执行：
```
../tools/hugo.exe server -s . --bind 0.0.0.0
```
然后浏览器开 http://localhost:1313

## 写文章
在 `content/posts/` 下新建 `.md` 文件（参考 `content/posts/welcome.md`）。
 front matter 示例：
```
---
title: "标题"
date: 2026-10-13
draft: false
tags: ["标签1", "标签2"]
---
正文用 Markdown 写。
```

## 改首页落地页 / 社交链接
都在 `hugo.yaml`：
- `params.profileMode`：落地页昵称、签名、头像（放 `static/avatar.png` 后把 `imageUrl` 改成 `/avatar.png`）、按钮
- `params.socialIcons`：微信 / 小红书 / 知乎 / 邮箱 —— 把 `REPLACE_ME` 换成你的真实地址

## 部署到 Cloudflare Pages
1. Cloudflare 后台 → Workers & Pages → Create → Pages → 连 GitHub `mu16888/blog`
2. Framework preset: **Hugo**（构建命令 `hugo --minify`，输出目录 `public`，无需改）
3. 部署完成后 → Custom domains → 加 `mufeng168.top` 与 `blog.mufeng168.top`（CF 自动建 DNS，保留代理）
4. 之后每次 `git push` 即自动重新发布
