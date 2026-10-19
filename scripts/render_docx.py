# -*- coding: utf-8 -*-
import os, sys
import win32com.client as wc
import pypdfium2 as pdfium

BLOG = r"E:/workbuddy工作台/四季发财公司/12_运营工程区/沐风博客"
SRC = r"E:/workbuddy工作台/四季发财公司/01_项目库/上线转化中/B_公文秒成Pro/交付包源码与文档/gongwen-writing/assets/DOCX模板"
TMP = os.path.join(BLOG, "scripts", "_render_tmp")
OUT = os.path.join(BLOG, "static", "img", "gw-templates")
os.makedirs(TMP, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

# 文章 -> 源 docx -> 输出 png
MAPPING = [
    ("模板_通知_示例版.docx", "gw-notify.png"),
    ("模板_通报_示例版.docx", "gw-tongbao.png"),
    ("模板_请示_示例版.docx", "gw-qingshi.png"),
    ("模板_报告_示例版.docx", "gw-baogao.png"),
    ("模板_通告_示例版.docx", "gw-tonggao.png"),
    ("模板_函_示例版.docx",   "gw-han.png"),
]

DPI = 150
SCALE = DPI / 72.0

word = None
try:
    word = wc.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    word.ScreenUpdating = False
    for docx_name, png_name in MAPPING:
        docx_path = os.path.join(SRC, docx_name)
        pdf_path = os.path.join(TMP, png_name.replace(".png", ".pdf"))
        png_path = os.path.join(OUT, png_name)
        doc = word.Documents.Open(docx_path)
        doc.ExportAsFixedFormat(pdf_path, 17)  # 17 = wdExportFormatPDF
        doc.Close(False)
        # PDF -> PNG
        pdf = pdfium.PdfDocument(pdf_path)
        page = pdf[0]
        bmp = page.render(scale=SCALE)
        pil = bmp.to_pil()
        if pil.mode != "RGB":
            pil = pil.convert("RGB")
        pil.save(png_path, "PNG")
        pdf.close()
        print(f"OK {docx_name} -> {png_name} ({pil.width}x{pil.height})")
    print("ALL_DONE")
except Exception as e:
    print("ERR:", repr(e))
    sys.exit(1)
finally:
    if word:
        try:
            word.Quit()
        except Exception:
            pass
