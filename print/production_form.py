"""Fill prod_form_template.docx with production data and print it through Word (COM).

Fill logic is pure XML (no Word needed). Word is only used to export the PDF
preview and to print.
"""
import copy
import os
import zipfile
from contextlib import contextmanager
from datetime import datetime

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W}


def _q(tag):
    return f"{{{W}}}{tag}"


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def batch_text(data):
    try:
        req, per = float(data.get("qty_required", 0)), float(data.get("qty_per_batch", 1))
        n = int(req / per) if per > 0 else 1
        return f"{n} batch{'es' if n != 1 else ''} by {per:.3f} KG."
    except Exception:
        return "1 batch by 0.000 KG."


def build_values(data, wip_no=False):
    """Bookmark name -> text. Keys match the bookmarks in the template."""
    summary = batch_text(data)
    cust = str(data.get("customer", ""))
    if len(cust) > 28:  # longer than the cell: Word would wrap and push the form down
        cust = cust[:25] + "..."
    values = {
        "prod_id": data.get("prod_id", ""),
        "prod_date": data.get("production_date", ""),
        "order_no": data.get("order_form_no", ""),
        "formula_no": data.get("formulation_id", ""),
        "product_code": data.get("product_code", ""),
        "product_color": data.get("product_color", ""),
        "dosage": data.get("dosage", ""),
        "customer": cust,
        "lot_no": data.get("lot_number", ""),
        "mixing_time": data.get("mixing_time", ""),
        "machine_no": data.get("machine_no", ""),
        "qty_required": data.get("qty_required", ""),
        "qty_per_batch": data.get("qty_per_batch", ""),
        "qty_to_produce": data.get("qty_produced", ""),
        "batch_text": summary.upper(),
        "note": f"NOTE: {summary}",
        "total": f"{_f(data.get('qty_produced')):.6f}",
        "prepared_by": data.get("prepared_by", ""),
        "printed_on": datetime.now().strftime("%m/%d/%y %I:%M %p"),
    }
    if wip_no:  # only used if the template has a "wip_no" bookmark
        values["wip_no"] = data.get("wip_no", "")
    return values


def _make_run(paragraph, text):
    """A run carrying the paragraph-mark formatting (font, bold, size) of the template."""
    run = etree.Element(_q("r"))
    rpr = paragraph.find("w:pPr/w:rPr", NS)
    if rpr is not None:
        run.append(copy.deepcopy(rpr))
    t = etree.SubElement(run, _q("t"))
    t.text = str(text)
    t.set(f"{{{XML}}}space", "preserve")
    return run


def _set_bookmark(root, name, text):
    # The header box is stored twice by Word (text box + fallback), so fill every match.
    for bm in root.xpath(f"//w:bookmarkStart[@w:name='{name}']", namespaces=NS):
        bm.addnext(_make_run(bm.getparent(), text))


def _set_borders(tr, top, bottom):
    """Keep only the requested top/bottom borders on every cell of a row."""
    for borders in tr.iterfind("w:tc/w:tcPr/w:tcBorders", NS):
        for child in list(borders):
            borders.remove(child)
        for side, on in (("top", top), ("bottom", bottom)):  # schema order: top before bottom
            if on:
                e = etree.SubElement(borders, _q(side))
                e.set(_q("val"), "single")
                e.set(_q("sz"), "4")
                e.set(_q("space"), "0")
                e.set(_q("color"), "auto")


def _fill_materials(root, mats):
    tbl = root.xpath("//w:tbl[contains(string(.), 'MATERIAL CODE')]", namespaces=NS)[0]
    rows = tbl.findall("w:tr", NS)
    proto = copy.deepcopy(rows[1])  # first blank row = row template
    note_row = rows[-1]  # NOTE / TOTAL row stays last
    for r in rows[1:-1]:
        tbl.remove(r)

    items = mats or [{}]
    last = len(items) - 1
    for i, m in enumerate(items):
        tr = copy.deepcopy(proto)
        for el in tr.iter():
            for attr in (f"{{{W14}}}paraId", f"{{{W14}}}textId"):
                el.attrib.pop(attr, None)
        code = str(m.get("material_code", "")).strip()
        if code:  # blank code = blank row, same as before
            vals = [code[:24],
                    f"{_f(m.get('large_scale')):.6f}",
                    f"{_f(m.get('small_scale')):.6f}",
                    f"{_f(m.get('total_weight')):.6f}"]
            for tc, v in zip(tr.findall("w:tc", NS), vals):
                p = tc.find("w:p", NS)
                p.append(_make_run(p, v))
        # line under the header (first row) and under the last material only
        _set_borders(tr, top=(i == 0), bottom=(i == last))
        note_row.addprevious(tr)


def fill_template(template_path, out_path, data, mats, wip_no=False):
    with zipfile.ZipFile(template_path) as zin:
        root = etree.fromstring(zin.read("word/document.xml"))
        _fill_materials(root, mats)
        for name, text in build_values(data, wip_no).items():
            _set_bookmark(root, name, text)
        xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                zout.writestr(item, xml if item.filename == "word/document.xml" else zin.read(item.filename))


# ---------------------------------------------------------------- Word (COM)
@contextmanager
def _word():
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()  # required because this runs in a worker thread
    app = None
    try:
        app = win32com.client.DispatchEx("Word.Application")  # own instance, never the user's open Word
        app.Visible = False
        app.DisplayAlerts = 0
        yield app
    finally:
        if app is not None:
            try:
                app.Quit(False)
            except Exception:
                pass
        del app
        pythoncom.CoUninitialize()


def export_pdf(docx_path, pdf_path):
    with _word() as app:
        doc = app.Documents.Open(os.path.abspath(docx_path), ReadOnly=True, AddToRecentFiles=False)
        try:
            doc.ExportAsFixedFormat(os.path.abspath(pdf_path), 17)  # 17 = PDF
        finally:
            doc.Close(False)
        del doc


def print_docx(docx_path, printer_name):
    with _word() as app:
        app.ActivePrinter = printer_name
        doc = app.Documents.Open(os.path.abspath(docx_path), ReadOnly=True, AddToRecentFiles=False)
        try:
            doc.PrintOut(Background=False)  # wait until the job is handed to the spooler
        finally:
            doc.Close(False)
        del doc