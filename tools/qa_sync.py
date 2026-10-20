#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
互动页问答清单 · 双向同步工具
================================
锋哥用 Excel（qa.xlsx）填答案 → 跑本脚本 → 自动写回 data/qa.yaml → 网站读 yaml 上线。

用法（两条命令）：
  1) 生成/更新 Excel 表格（首次运行，或你想重新拉一份带最新问题清单的表时）：
         python tools/qa_sync.py export
  2) 把你填好的 Excel 导回 yaml（填完答案后运行这个）：
         python tools/qa_sync.py import

说明：
  · qa.xlsx 的 A 列「问题」是锁死的（只读参考），你要填的是 B 列「答案」和 C 列「是否已答」。
  · 「答案」列可以直接写多行，表格里按 Alt+Enter 换行即可，YAML 里会自动转成正确的格式。
  · 「是否已答」列填「是」= 显示在「已回答」区；填「否」= 显示在「待回答」区（默认）。
  · 导入时会自动备份 qa.yaml 为 qa.yaml.bak。
"""

import os
import sys
import json
import shutil

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import yaml

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX = os.path.join(BASE, "qa.xlsx")
YAML = os.path.join(BASE, "data", "qa.yaml")

C_HEAD = "1b2a4d"   # 藏青表头
C_Q = "f6f7f9"      # 淡白题目列
C_A = "ffffff"      # 白答案列


def load_yaml():
    if not os.path.exists(YAML):
        print("[错误] 找不到 %s" % YAML)
        sys.exit(1)
    with open(YAML, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
    return data


def _yaml_str(s):
    """安全地把字符串写成 YAML 标量（不用 yaml.dump —— 它会追加 '...' 结束标记，
    导致 Hugo 的 YAML 解析报 "value is not allowed in this context"）。"""
    s = str(s)
    if "\n" in s or s.strip() == "":
        return None  # 需要用块标量处理
    # 用 JSON 风格的引号转义：YAML 1.2 兼容 JSON 字符串语法
    return json.dumps(s, ensure_ascii=False)


def dump_yaml(items):
    # 备份必须放到 data/ 目录之外 —— Hugo 会把 data/ 下所有文件当数据文件解析，
    # 放 .bak 进去会导致构建报 "unmarshal of format \"\" is not supported" 直接失败。
    bak_dir = os.path.join(BASE, "tools", "_backup")
    os.makedirs(bak_dir, exist_ok=True)
    if os.path.exists(YAML):
        shutil.copyfile(YAML, os.path.join(bak_dir, "qa.yaml.bak"))
    with open(YAML, "w", encoding="utf-8", newline="\n") as f:
        header = (
            "# 互动页 · 高频问答清单\n"
            "# 本文件由 tools/qa_sync.py 从 qa.xlsx 自动生成，请勿手改（改表格再导回）\n"
            "# 锋哥编辑入口：qa.xlsx（B列答案 / C列是否已答）\n"
            "#\n"
            "# question : 访客看到的问题\n"
            "# category : 分类标签\n"
            "# answer   : 答案（空 = 待答）\n"
            "# whole    : 是否已答完整\n"
        )
        f.write(header)
        for it in items:
            q = _yaml_str(it["question"])
            c = _yaml_str(it["category"])
            if q is None:
                f.write("- question: |-\n")
                for line in it["question"].splitlines():
                    f.write("    %s\n" % line)
            else:
                f.write("- question: %s\n" % q)
            if c is None:
                f.write("  category: |-\n")
                for line in it["category"].splitlines():
                    f.write("    %s\n" % line)
            else:
                f.write("  category: %s\n" % c)
            ans = (it.get("answer") or "").strip()
            if ans:
                # 多行答案用块标量 |- 写入，保留换行且 YAML 合法
                f.write("  answer: |-\n")
                for line in ans.splitlines():
                    f.write("    %s\n" % line)
            else:
                f.write('  answer: ""\n')
            f.write("  whole: %s\n" % ("true" if it.get("whole") else "false"))


def export():
    items = load_yaml()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "问答清单"

    headers = ["问题（只读，不用改）", "答案（← 你填这里）", "是否已答（是/否）", "分类（只读）"]
    ws.append(headers)
    for c in range(1, 5):
        cell = ws.cell(row=1, column=c)
        cell.font = Font(bold=True, color="FFFFFF", size=11)
        cell.fill = PatternFill("solid", fgColor=C_HEAD)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(bottom=Side(style="thin", color="C9D3E4"))

    for it in items:
        ws.append([
            it["question"],
            (it.get("answer") or ""),
            "是" if it.get("whole") else "否",
            it["category"],
        ])

    thin = Side(style="thin", color="E4E7EE")
    for r in range(2, ws.max_row + 1):
        for c in range(1, 5):
            cell = ws.cell(row=r, column=c)
            cell.border = Border(top=thin, bottom=thin, left=thin, right=thin)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
        qc = ws.cell(row=r, column=1)
        qc.fill = PatternFill("solid", fgColor=C_Q)
        qc.font = Font(color="5A6478", size=10)
        qc.protection = openpyxl.styles.Protection(locked=True)
        ac = ws.cell(row=r, column=2)
        ac.fill = PatternFill("solid", fgColor=C_A)
        ac.font = Font(size=11)
        ac.protection = openpyxl.styles.Protection(locked=False)
        cc = ws.cell(row=r, column=3)
        cc.alignment = Alignment(horizontal="center", vertical="top")
        cc.font = Font(size=11)
        cc.protection = openpyxl.styles.Protection(locked=False)
        dc = ws.cell(row=r, column=4)
        dc.fill = PatternFill("solid", fgColor=C_Q)
        dc.font = Font(color="5A6478", size=10)
        dc.protection = openpyxl.styles.Protection(locked=True)

    ws.column_dimensions["A"].width = 46
    ws.column_dimensions["B"].width = 78
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 12
    ws.row_dimensions[1].height = 26
    for r in range(2, ws.max_row + 1):
        ws.row_dimensions[r].height = 46

    ws.freeze_panes = "A2"
    wb.save(XLSX)

    # 说明书
    readme = os.path.join(BASE, "问答填写说明.txt")
    with open(readme, "w", encoding="utf-8") as f:
        f.write(
            "互动页问答 · 填写说明\n"
            "=====================\n\n"
            "文件：qa.xlsx（用 Excel 或 WPS 打开）\n\n"
            "怎么填：\n"
            "1) B 列「答案」= 写你的答案。答案可以写很长、分几段都行；\n"
            "   要换行就按 Alt+Enter（或右键→设置单元格格式→换行）。\n"
            "2) C 列「是否已答」= 填「是」或「否」。\n"
            "     填「是」→ 这条出现在网页「已回答」区（点开看答案）。\n"
            "     填「否」→ 这条出现在「待回答」区，网页会提示访客留言补充。\n"
            "     建议：答案写完整了就改成「是」。\n"
            "3) A 列问题、D 列分类是只读的，别动。\n\n"
            "填完怎么上线：\n"
            "   告诉来福一句「问答填好了」即可，剩下的我来跑。\n"
            "   （技术上就是运行 python tools/qa_sync.py import，然后推送上线。）\n\n"
            "小提示：\n"
            "· 答案里可以写 **加粗**、- 列表、网址，网页会按 Markdown 渲染。\n"
            "· 不确定该不该公开的问题，答案里别写具体隐私/客户名。\n"
            "· 原始数据备份在 data/qa.yaml（自动生成，勿手改）。\n"
        )

    print("[完成] 已生成 Excel 表格：%s" % XLSX)
    print("        共 %d 条问题。填好 B 列答案 + C 列是否已答，告诉我一声我来上线。" % len(items))
    print("        填写说明：%s" % readme)


def import_xlsx():
    if not os.path.exists(XLSX):
        print("[错误] 找不到 %s，请先运行：python tools/qa_sync.py export" % XLSX)
        sys.exit(1)
    wb = openpyxl.load_workbook(XLSX)
    ws = wb["问答清单"]

    items = []
    for r in range(2, ws.max_row + 1):
        q = ws.cell(row=r, column=1).value
        if not q:
            continue
        ans = ws.cell(row=r, column=2).value or ""
        done = str(ws.cell(row=r, column=3).value or "").strip()
        cat = ws.cell(row=r, column=4).value or "其他"
        ans = str(ans).replace("\r\n", "\n").replace("\r", "\n").strip()
        items.append({
            "question": str(q).strip(),
            "category": str(cat).strip(),
            "answer": ans,
            "whole": done in ("是", "Y", "y", "true", "True", "1"),
        })

    dump_yaml(items)
    answered = sum(1 for i in items if i["whole"])
    print("[完成] 已写回 %s" % YAML)
    print("        共 %d 条，其中已答 %d 条、待答 %d 条。" % (len(items), answered, len(items) - answered))
    print("        备份：tools/_backup/qa.yaml.bak")
    print("        接下来跑一次 hugo 构建确认无误，再推送上线。")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "export"
    if cmd == "export":
        export()
    elif cmd == "import":
        import_xlsx()
    else:
        print("用法：python tools/qa_sync.py [export|import]")
        sys.exit(1)
