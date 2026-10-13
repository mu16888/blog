# -*- coding: utf-8 -*-
"""沐风博客 - 图形化发布工具（双击运行，无黑框）"""
import os
import sys
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

BASE = os.path.dirname(os.path.abspath(__file__))
POSTS = os.path.join(BASE, 'content', 'posts')
HUGO = os.path.join(BASE, 'tools', 'hugo.exe')


def find_git():
    """git 不在 PATH，多处候选自动找。"""
    cands = [
        r'D:\Program Files\Git\cmd\git.exe',
        r'C:\Program Files\Git\cmd\git.exe',
        r'C:\Program Files (x86)\Git\cmd\git.exe',
        r'C:\Users\Administrator\AppData\Local\Programs\Git\cmd\git.exe',
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    # 退到 PATH
    from shutil import which
    w = which('git')
    return w or None


GIT = find_git()

log_q = queue.Queue()


def run_cmd(args, cwd=BASE, timeout=600):
    """跑一条命令，实时吐输出到队列。"""
    try:
        p = subprocess.Popen(
            args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            bufsize=1, universal_newlines=True, encoding='utf-8', errors='replace',
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        for line in p.stdout:
            log_q.put(line.rstrip())
        p.wait(timeout=timeout)
        return p.returncode
    except Exception as e:
        log_q.put('ERROR: %s' % e)
        return -1


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('沐风博客 - 发布工具')
        self.geometry('760x600')
        self.configure(bg='#f5f5f5')
        self.resizable(False, False)

        style = ttk.Style()
        try:
            style.theme_use('vista')
        except Exception:
            pass

        self._build_ui()
        self.after(100, self._poll_log)
        threading.Thread(target=self._refresh_article_list, daemon=True).start()

    # ---------- UI ----------
    def _build_ui(self):
        head = tk.Label(self, text='沐风博客发布工具', font=('Microsoft YaHei UI', 14, 'bold'),
                        bg='#f5f5f5', fg='#1a1a1a')
        head.pack(pady=(14, 2))

        sub = tk.Label(self, text='写文章 → 选文章 → 点发布 → 等 1 分钟看网站',
                       font=('Microsoft YaHei UI', 9), bg='#f5f5f5', fg='#666')
        sub.pack(pady=(0, 12))

        # 文章列表区
        frame_list = tk.LabelFrame(self, text='我的文章', font=('Microsoft YaHei UI', 10, 'bold'),
                                   bg='#f5f5f5', padx=8, pady=6)
        frame_list.pack(fill='x', padx=16)

        list_row = tk.Frame(frame_list, bg='#f5f5f5')
        list_row.pack(fill='x')

        self.article_list = tk.Listbox(list_row, height=7, font=('Consolas', 10),
                                       activestyle='none', selectmode='browse')
        self.article_list.pack(side='left', fill='both', expand=True)

        scroll = tk.Scrollbar(list_row, command=self.article_list.yview)
        scroll.pack(side='left', fill='y')
        self.article_list.config(yscrollcommand=scroll.set)

        # 按钮区
        frame_btn = tk.Frame(self, bg='#f5f5f5')
        frame_btn.pack(fill='x', padx=16, pady=10)

        self._mkbtn(frame_btn, '写新文章', self.on_new, '#2d7dd2').pack(side='left', padx=4)
        self._mkbtn(frame_btn, '编辑选中', self.on_edit, '#28a745').pack(side='left', padx=4)
        self._mkbtn(frame_btn, '删除选中', self.on_delete, '#dc3545').pack(side='left', padx=4)
        self._mkbtn(frame_btn, '本地预览', self.on_preview, '#6f42c1').pack(side='left', padx=4)
        self._mkbtn(frame_btn, '打开网站', self.on_site, '#fd7e14').pack(side='left', padx=4)

        # 状态 + 日志
        frame_log = tk.LabelFrame(self, text='运行日志', font=('Microsoft YaHei UI', 10, 'bold'),
                                  bg='#f5f5f5', padx=8, pady=6)
        frame_log.pack(fill='both', expand=True, padx=16, pady=(0, 16))

        self.log_text = tk.Text(frame_log, height=13, font=('Consolas', 9),
                                bg='#1e1e1e', fg='#d4d4d4', insertbackground='white',
                                relief='flat', wrap='word')
        self.log_text.pack(side='left', fill='both', expand=True)
        self.log_text.insert('end', '就绪。\n')
        self.log_text.config(state='disabled')

        self.publish_btn = self._mkbtn(self, '★ 发布到网站（点我做最后一步）',
                                       self.on_publish, '#0d6efd')
        self.publish_btn.pack(pady=(0, 14))
        self.publish_btn.config(state='disabled', height=2)

    def _mkbtn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, font=('Microsoft YaHei UI', 9),
                         bg=color, fg='white', activebackground=color,
                         activeforeground='white', relief='flat', cursor='hand2',
                         padx=14, pady=6, bd=0)

    # ---------- helpers ----------
    def log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert('end', msg + '\n')
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def _poll_log(self):
        try:
            while True:
                self.log(log_q.get_nowait())
        except queue.Empty:
            pass
        self.after(120, self._poll_log)

    def _md_files(self):
        if not os.path.isdir(POSTS):
            return []
        return sorted([f for f in os.listdir(POSTS) if f.lower().endswith('.md')])

    def _refresh_article_list(self):
        self.article_list.delete(0, 'end')
        for f in self._md_files():
            self.article_list.insert('end', f)
        self.after(100, lambda: self.publish_btn.config(
            state='normal' if self._md_files() else 'disabled'))

    def _selected(self):
        idx = self.article_list.curselection()
        return self.article_list.get(idx[0]) if idx else None

    def _open_in_notepad(self, path):
        subprocess.Popen(['notepad.exe', path],
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))

    # ---------- 按钮动作 ----------
    def on_new(self):
        name = filedialog.asksaveasfilename(
            initialdir=POSTS, title='新建文章（文件名请用英文 + .md）',
            defaultextension='.md', filetypes=[('Markdown 文件', '*.md')],
            initialfile='my-post.md')
        if not name:
            return
        if not name.endswith('.md'):
            name += '.md'
        tpl = ('---\n'
               'title: "我的新文章"\n'
               'date: %s\n'
               'draft: true\n'
               'tags: ["随笔"]\n'
               'description: "一句话简介"\n'
               '---\n\n'
               '在这里写正文。\n' % tk.datetime.datetime.now().strftime('%Y-%m-%d'))
        with open(name, 'w', encoding='utf-8') as f:
            f.write(tpl)
        self.log('已创建：%s（模板已填好，draft 是 true 暂时不发布）' % os.path.basename(name))
        self._refresh_article_list()
        self._open_in_notepad(name)

    def on_edit(self):
        f = self._selected()
        if not f:
            messagebox.showinfo('提示', '请先在上面的列表里选中一篇文章')
            return
        self._open_in_notepad(os.path.join(POSTS, f))

    def on_delete(self):
        f = self._selected()
        if not f:
            messagebox.showinfo('提示', '请先选中要删除的文章')
            return
        if not messagebox.askyesno('确认删除', '确定要删除《%s》吗？\n\n删除后需要点“发布”才会真正生效。' % f):
            return
        try:
            os.remove(os.path.join(POSTS, f))
            self.log('已删除：%s' % f)
            self._refresh_article_list()
        except Exception as e:
            messagebox.showerror('删除失败', str(e))

    def on_preview(self):
        if not os.path.exists(HUGO):
            messagebox.showerror('错误', '找不到 hugo.exe：%s' % HUGO)
            return
        threading.Thread(target=self._preview_worker, daemon=True).start()

    def _preview_worker(self):
        self.log('启动本地预览服务器…')
        subprocess.Popen(['cmd.exe', '/c', 'start', 'http://localhost:1313'],
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        run_cmd([HUGO, 'server', '-s', BASE, '--bind', '0.0.0.0'])
        self.log('预览已停止。')

    def on_site(self):
        subprocess.Popen(['cmd.exe', '/c', 'start', 'https://mufeng168.top'],
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))

    def on_publish(self):
        if messagebox.askyesno('确认发布',
                               '将把以下内容推送到网站：\n\n'
                               '· %d 篇文章\n'
                               '· 配置与脚本改动\n\n'
                               '确定继续吗？' % len(self._md_files())):
            self.publish_btn.config(state='disabled', text='正在发布，请稍候…')
            threading.Thread(target=self._publish_worker, daemon=True).start()

    def _publish_worker(self):
        self.log('=' * 46)
        self.log('[1/3] 暂存改动…')
        if run_cmd([GIT, 'add', '-A']) != 0:
            self._publish_done(False, '暂存失败')
            return

        self.log('[2/3] 提交…')
        rc = run_cmd([GIT, 'commit', '-m',
                      'update: %s' % tk.datetime.datetime.now().strftime('%Y-%m-%d %H:%M')])
        if rc != 0:
            self.log('（没有新改动，跳过提交步骤）')

        self.log('[3/3] 推送到 GitHub…')
        if run_cmd([GIT, 'push', 'origin', 'main']) != 0:
            self._publish_done(False, '推送失败')
            return

        self._publish_done(True, None)

    def _publish_done(self, ok, err):
        if ok:
            self.log('=' * 46)
            self.log('发布成功！约 1 分钟后刷新 https://mufeng168.top 即可看到')
            messagebox.showinfo('发布成功',
                                '已推送到 GitHub。\n\n'
                                'Cloudflare 会在约 1 分钟内自动重新构建，\n'
                                '然后刷新 https://mufeng168.top 就能看到你的文章。')
        else:
            messagebox.showerror('发布失败',
                                 '%s\n\n请看下方日志的红色报错。\n\n'
                                 '如果是 proxy 127.0.0.1 的问题，\n'
                                 '双击项目里的 fix-proxy.bat 再试一次。' % (err or '未知错误'))
        self.publish_btn.config(state='normal', text='★ 发布到网站（点我做最后一步）')


if __name__ == '__main__':
    try:
        app = App()
        app.mainloop()
    except tk.TclError:
        # 无图形界面（沙箱）时静默退出
        sys.exit(0)
