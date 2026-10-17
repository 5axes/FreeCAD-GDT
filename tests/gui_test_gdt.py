# -*- coding: utf-8 -*-
"""End-to-end GUI test of the GD&T workbench, run *inside* FreeCAD.

Launched by ``tools/run_gui_tests.py`` (``FreeCAD.exe tests/gui_test_gdt.py``).
The script drives the real commands and task panels (it clicks the panel
buttons and feeds the Draft point picker through its coordinate entry
callback), saves and reopens a document, opens the historical sample files,
then writes a JSON report and quits FreeCAD.

Environment variables:
    GDT_TEST_OUT      path of the JSON report (required)
    GDT_TEST_WORKDIR  scratch folder for saved documents (required)
    GDT_TEST_SAMPLES  folder of historical .FCStd files (optional)
"""

import glob
import json
import os
import shutil
import sys
import time
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui

try:
    from PySide import QtWidgets
except ImportError:  # very old PySide shim
    QtWidgets = QtGui

OUT = os.environ.get("GDT_TEST_OUT")
WORKDIR = os.environ.get("GDT_TEST_WORKDIR")
SAMPLES = os.environ.get("GDT_TEST_SAMPLES", "")

WB = "GDandTWorkbench"
COMMANDS = ["dd_annotationPlane", "dd_datumFeature", "dd_datumSystem",
            "dd_geometricTolerance", "dd_inventory"]
GDT_TYPES = ["AnnotationPlane", "DatumFeature", "DatumSystem",
             "GeometricTolerance", "Annotation"]

results = []
_report_pos = [0]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def mw():
    return Gui.getMainWindow()


def pump(n=5):
    for _ in range(n):
        QtWidgets.QApplication.processEvents()
        time.sleep(0.02)


def report_widget():
    for w in mw().findChildren(QtWidgets.QTextEdit):
        if w.objectName() == "Report view":
            return w
    return None


def console_since_last():
    """Return the Report view text written since the previous call."""
    w = report_widget()
    if w is None:
        return ""
    text = w.toPlainText()
    new = text[_report_pos[0]:]
    _report_pos[0] = len(text)
    return new


def console_problems(text):
    """Keep error lines, and whole Python tracebacks."""
    keys = ("Traceback", "Error", "error:", "Exception", "<Exception>")
    out, in_tb = [], False
    for line in text.splitlines():
        if "Traceback" in line:
            in_tb = True
        if in_tb or any(k in line for k in keys):
            out.append(line)
        if in_tb and line and not line.startswith((" ", "\t", "Traceback")):
            in_tb = False
    return out


def record(tid, name, status, detail="", console=""):
    problems = console_problems(console)
    if status == "PASS" and problems:
        status = "WARN"
    results.append({"id": tid, "name": name, "status": status,
                    "detail": detail, "console": problems[:30]})
    App.Console.PrintMessage("[GDT-TEST] {} {} {} {}\n".format(tid, status, name, detail))


def run(tid, name, func):
    console_since_last()
    try:
        detail = func()
        status = "PASS"
        if isinstance(detail, tuple):
            status, detail = detail
    except Exception:
        status = "FAIL"
        detail = traceback.format_exc()
    pump()
    record(tid, name, status, detail or "", console_since_last())
    return status


def gdt_type(obj):
    proxy = getattr(obj, "Proxy", None)
    return getattr(proxy, "Type", None)


def objects_of(doc, typ):
    return [o for o in doc.Objects if gdt_type(o) == typ]


def select_face(obj, sub):
    Gui.Selection.clearSelection()
    doc = obj.Document
    Gui.Selection.addSelection(doc.Name, obj.Name, sub)
    pump()


def select_in_body(body, sub_path):
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(body.Document.Name, body.Name, sub_path)
    pump()


def task_button(title_startswith):
    for b in mw().findChildren(QtWidgets.QPushButton):
        if b.isVisible() and b.text().startswith(title_startswith):
            return b
    return None


def close_task_dialog():
    try:
        Gui.Control.closeDialog()
    except Exception:
        pass
    pump()


def pick(point):
    """Feed the Draft point picker as if the user typed coordinates."""
    tb = getattr(Gui, "draftToolBar", None)
    cb = getattr(tb, "pointcallback", None) if tb else None
    if cb is None:
        raise RuntimeError("Draft point picker is not waiting for a point")
    cb(point, True, False)
    pump()


def is_active(cmd):
    c = Gui.Command.get(cmd)
    return bool(c and c.isActive())


def find_combo(form, index):
    combos = [c for c in form.findChildren(QtWidgets.QComboBox) if c.isVisible()]
    return combos[index] if index < len(combos) else None


def choose(combo, index):
    combo.setCurrentIndex(index)
    combo.activated.emit(index)
    pump()


def invalid_objects(doc):
    bad = []
    for o in doc.Objects:
        st = o.State
        if "Invalid" in st or "Error" in st:
            bad.append("{} {}".format(o.Name, st))
    return bad


def gdt_inventory(doc):
    return {t: len(objects_of(doc, t)) for t in GDT_TYPES}


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

ctx = {}


def t_lazy_loading():
    """FreeCAD start-up must not import the workbench modules (W-01)."""
    loaded = [m for m in ("GDT", "datumFeature", "inventory") if m in sys.modules]
    return ("PASS" if not loaded else "FAIL"), "modules charges au demarrage : {}".format(loaded)


def t_wb_registered():
    wbs = Gui.listWorkbenches()
    if WB not in wbs:
        return "FAIL", "Workbench absent : {}".format(sorted(wbs))
    return "MenuText={}".format(getattr(wbs[WB], "MenuText", "?"))


def t_activate():
    Gui.activateWorkbench(WB)
    pump(10)
    active = Gui.activeWorkbench().__class__.__name__
    if active != WB:
        return "FAIL", "active workbench = {}".format(active)
    return "activated"


def t_toolbar_menu():
    tbs = [t.objectName() for t in mw().findChildren(QtWidgets.QToolBar)]
    menus = [m.title() for m in mw().menuBar().findChildren(QtWidgets.QMenu)]
    ok_tb = any("GD&T" in n for n in tbs)
    ok_menu = any("GD&T" in m.replace("&&", "&") for m in menus)
    detail = "toolbar={} menu={}".format(ok_tb, ok_menu)
    return ("PASS" if ok_tb and ok_menu else "FAIL"), detail


def t_commands_icons():
    missing, noicon = [], []
    for name in COMMANDS:
        c = Gui.Command.get(name)
        if c is None:
            missing.append(name)
            continue
        info = c.getInfo()
        pix = info.get("pixmap") or info.get("Pixmap") or ""
        if not pix or QtGui.QIcon(pix).isNull():
            noicon.append("{}({})".format(name, pix))
    icons = ["GDT", "annotationPlane", "datumFeature", "datumSystem", "geometricTolerance",
             "inventory", "annotation", "planeGDT", "subGDT", "diameter",
             "Characteristic/position", "FeatureControlFrame/maximumMaterialCondition"]
    for i in icons:
        if QtGui.QIcon(":/dd/icons/{}.svg".format(i)).pixmap(16, 16).isNull():
            noicon.append(i)
    if missing or noicon:
        return "FAIL", "missing={} noicon={}".format(missing, noicon)
    return "{} commandes, {} icones verifiees".format(len(COMMANDS), len(icons))


def t_setup_doc():
    doc = App.newDocument("GDTTest")
    box = doc.addObject("Part::Box", "Box")
    box.Length, box.Width, box.Height = 40, 30, 10
    cyl = doc.addObject("Part::Cylinder", "Cyl")
    cyl.Radius, cyl.Height = 5, 20
    cyl.Placement.Base = App.Vector(20, 15, 10)
    doc.recompute()
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
    pump(10)
    ctx.update(doc=doc, box=box, cyl=cyl)
    return "Box + Cylindre"


def t_create_ap():
    doc, box = ctx["doc"], ctx["box"]
    select_face(box, "Face6")  # top face z=10
    if not is_active("dd_annotationPlane"):
        return "FAIL", "commande inactive avec une face selectionnee"
    Gui.runCommand("dd_annotationPlane")
    pump(10)
    b = task_button("Add Annotation Plane")
    if b is None:
        return "FAIL", "bouton du panneau introuvable"
    b.click()
    pump(10)
    close_task_dialog()
    aps = objects_of(doc, "AnnotationPlane")
    if len(aps) != 1:
        return "FAIL", "{} AnnotationPlane".format(len(aps))
    ap = aps[0]
    ctx["ap"] = ap
    return "AP={} p1={} dir={}".format(ap.Label, ap.p1, ap.Direction)


def _create_with_pick(cmd, title, sub, obj, pick_offset, setup=None):
    doc = ctx["doc"]
    select_face(obj, sub)
    if not is_active(cmd):
        return "FAIL", "commande {} inactive sur {}".format(cmd, sub)
    Gui.runCommand(cmd)
    pump(10)
    b = task_button(title)
    if b is None:
        return "FAIL", "bouton du panneau introuvable"
    if setup:
        setup(b.parent())
    face = obj.Shape.getElement(sub)
    target = face.CenterOfMass + pick_offset
    b.click()
    pump(10)
    tb = getattr(Gui, "draftToolBar", None)
    waiting = tb is not None and getattr(tb, "pointcallback", None) is not None
    ctx.setdefault("picks", []).append((cmd, sub, waiting))
    if waiting:
        record_wp(cmd)
        pick(target)
    close_task_dialog()
    return None


def record_wp(cmd):
    """Remember the Draft working plane used by the point picker."""
    import WorkingPlane
    wp = WorkingPlane.get_working_plane(update=False)
    ctx.setdefault("wp", []).append((cmd, App.Vector(wp.axis), App.Vector(wp.position)))


def t_create_df():
    doc = ctx["doc"]
    r = _create_with_pick("dd_datumFeature", "Add Datum Feature", "Face1", ctx["box"],
                          App.Vector(-15, 0, 10))
    if r:
        return r
    dfs, ann, dss = (objects_of(doc, t) for t in ("DatumFeature", "Annotation", "DatumSystem"))
    if len(dfs) != 1 or len(ann) != 1:
        return "FAIL", "DF={} Annotation={}".format(len(dfs), len(ann))
    ctx["df"] = dfs[0]
    vobj = ctx["box"].ViewObject
    ctx["face1"] = (tuple(vobj.DiffuseColor)[0] if len(vobj.DiffuseColor) >= 6 else None,
                    [m.Transparency for m in vobj.ShapeAppearance]
                    if hasattr(vobj, "ShapeAppearance") else [])
    return "DF={} Annotation={} DS auto={}".format(dfs[0].Label, ann[0].Label, len(dss))


def t_create_ds():
    doc = ctx["doc"]
    Gui.Selection.clearSelection()
    if not is_active("dd_datumSystem"):
        return "FAIL", "commande inactive"
    before = len(objects_of(doc, "DatumSystem"))
    Gui.runCommand("dd_datumSystem")
    pump(10)
    b = task_button("Add Datum System")
    if b is None:
        return "FAIL", "bouton du panneau introuvable"
    primary = find_combo(b.parent(), 0)
    if primary is not None and primary.count() > 1:
        choose(primary, 1)
    b.click()
    pump(10)
    close_task_dialog()
    dss = objects_of(doc, "DatumSystem")
    if len(dss) != before + 1:
        return "FAIL", "{} -> {} DatumSystem".format(before, len(dss))
    ds = dss[-1]
    ctx["ds"] = ds
    return "DS={} Primary={}".format(ds.Label, ds.Primary.Label if ds.Primary else None)


def _set_tolerance(form, text="0.05 mm"):
    edits = [e for e in form.findChildren(QtWidgets.QLineEdit)
             if e.isVisible() and e.metaObject().className() == "Gui::InputField"]
    if edits:
        edits[0].setText(text)
        pump()


def t_create_gt():
    doc = ctx["doc"]

    def setup(form):
        _set_tolerance(form)
        ds_combo = None
        for c in form.findChildren(QtWidgets.QComboBox):
            if c.isVisible() and c.count() > 1 and c.itemText(0) == "" and \
                    any("DS" in c.itemText(i) for i in range(c.count())):
                ds_combo = c
        if ds_combo is not None:
            choose(ds_combo, ds_combo.count() - 1)

    r = _create_with_pick("dd_geometricTolerance", "Add Geometric Tolerance", "Face2",
                          ctx["box"], App.Vector(15, 0, 10), setup)
    if r:
        return r
    gts = objects_of(doc, "GeometricTolerance")
    if len(gts) != 1:
        return "FAIL", "{} GeometricTolerance".format(len(gts))
    gt = gts[0]
    ctx["gt"] = gt
    return "GT={} {} tol={} DS={}".format(gt.Label, gt.Characteristic, gt.ToleranceValue,
                                         gt.DS.Label if gt.DS else None)


def t_create_gt_cyl():
    doc = ctx["doc"]

    def setup(form):
        _set_tolerance(form, "0.02 mm")
        for c in form.findChildren(QtWidgets.QComboBox):
            if c.isVisible() and c.count() == 2 and c.itemText(0) == "" and c.itemText(1) == "":
                choose(c, 1)  # diameter symbol
                break

    cyl = ctx["cyl"]
    lateral = None
    for i, f in enumerate(cyl.Shape.Faces):
        if f.Surface.__class__.__name__ == "Cylinder":
            lateral = "Face{}".format(i + 1)
    r = _create_with_pick("dd_geometricTolerance", "Add Geometric Tolerance", lateral,
                          cyl, App.Vector(10, 10, 10), setup)
    if r:
        return r
    gts = objects_of(doc, "GeometricTolerance")
    if len(gts) != 2:
        return "FAIL", "{} GeometricTolerance".format(len(gts))
    ann = [a for a in objects_of(doc, "Annotation") if gts[-1] in a.GT]
    circ = ann[0].circumferenceBool if ann else None
    return "GT={} Circumference={} annotation.circumferenceBool={} diameter={}".format(
        gts[-1].Label, gts[-1].Circumference, circ, ann[0].diameter if ann else None)


def t_gt_existing_annotation():
    """A tolerance on the face already carrying the datum joins its annotation (F-06)."""
    doc = ctx["doc"]
    n_ann = len(objects_of(doc, "Annotation"))
    r = _create_with_pick("dd_geometricTolerance", "Add Geometric Tolerance", "Face1",
                          ctx["box"], App.Vector(-15, 0, 15))
    if r:
        return r
    gts = objects_of(doc, "GeometricTolerance")
    ann = [a for a in objects_of(doc, "Annotation") if a.DF == ctx["df"]]
    joined = bool(ann) and gts[-1] in ann[0].GT
    detail = "annotations {} -> {} ; GT dans l'annotation du DF : {}".format(
        n_ann, len(objects_of(doc, "Annotation")), joined)
    return ("PASS" if joined else "FAIL"), detail


def t_multi_object_selection():
    """Selecting faces on two different objects must not crash (P-01)."""
    doc = ctx["doc"]
    box, cyl = ctx["box"], ctx["cyl"]
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, box.Name, "Face3")
    Gui.Selection.addSelection(doc.Name, cyl.Name, "Face2")
    pump()
    console_since_last()
    active = is_active("dd_geometricTolerance")
    probs = console_problems(console_since_last())
    if not active:
        return "FAIL", "commande inactive ; console={}".format(probs[:3])
    n = len(objects_of(doc, "GeometricTolerance"))
    Gui.runCommand("dd_geometricTolerance")
    pump(10)
    b = task_button("Add Geometric Tolerance")
    if b is None:
        close_task_dialog()
        return "FAIL", "panneau non ouvert ; console={}".format(
            console_problems(console_since_last())[:3])
    b.click()
    pump(10)
    pick(box.Shape.getElement("Face3").CenterOfMass + App.Vector(0, -15, 10))
    close_task_dialog()
    n2 = len(objects_of(doc, "GeometricTolerance"))
    return ("PASS" if n2 == n + 1 else "FAIL"), "GT {} -> {}".format(n, n2)


def t_face_color():
    """The datum face gets the datum colour and stays opaque (I-05)."""
    face1, transp = ctx["face1"]  # colours just after datum A was put on Face1
    if face1 is None:
        return "FAIL", "couleurs par face non appliquees"
    transp = [round(t, 2) for t in transp]
    blue = face1[2] > 0.9 and face1[0] < 0.1
    opaque = not transp or transp[0] < 0.5
    detail = "Face1={} transparence par face={}".format(tuple(round(c, 2) for c in face1), transp)
    return ("PASS" if blue and opaque else "FAIL"), detail


def t_working_plane():
    """While picking the anchor point, the Draft working plane must be the AP (I-01)."""
    checks = ctx.get("wp", [])
    if not checks:
        return "FAIL", "aucune saisie de point enregistree"
    ap = ctx["ap"]
    msgs, ok = ["saisies demandees : {}".format(ctx.get("picks"))], True
    for cmd, axis, pos in checks:
        parallel = abs(abs(axis.normalize().dot(ap.Direction)) - 1) < 1e-6
        on_plane = abs((pos - ap.PointWithOffset).dot(ap.Direction)) < 1e-6
        ok &= parallel and on_plane
        msgs.append("{}: axe={} pos={} -> parallele={} dans_plan={}".format(
            cmd, axis, pos, parallel, on_plane))
    return ("PASS" if ok else "FAIL"), "\n".join(msgs)


def t_body_non_tip():
    """Face of a Body feature that is NOT the tip, in a moved App::Part (I-04)."""
    doc = App.newDocument("GDTBody2")
    part = doc.addObject("App::Part", "Part")
    part.Placement.Base = App.Vector(0, 200, 0)
    body = doc.addObject("PartDesign::Body", "Body")
    part.addObject(body)
    box = doc.addObject("PartDesign::AdditiveBox", "Box")
    body.addObject(box)
    box.Length, box.Width, box.Height = 20, 20, 5
    cyl = doc.addObject("PartDesign::AdditiveCylinder", "Cyl")
    body.addObject(cyl)
    cyl.Radius, cyl.Height = 3, 10
    doc.recompute()
    pump(5)
    expected = box.Shape.getElement("Face6")  # top of the box, local to the Body
    exp_center = part.Placement.multVec(expected.CenterOfMass)
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, part.Name, "Body.Box.Face6")
    pump()
    try:
        if not is_active("dd_annotationPlane"):
            return "FAIL", "commande inactive"
        Gui.runCommand("dd_annotationPlane")
        pump(10)
        b = task_button("Add Annotation Plane")
        if b is None:
            return "FAIL", "bouton du panneau introuvable"
        b.click()
        pump(10)
        close_task_dialog()
        aps = objects_of(doc, "AnnotationPlane")
        if not aps:
            return "FAIL", "aucun AP cree"
        p1 = aps[0].p1
        ok = (p1 - exp_center).Length < 1e-6
        return ("PASS" if ok else "FAIL"), "p1={} attendu={}".format(p1, exp_center)
    finally:
        close_task_dialog()
        App.closeDocument(doc.Name)


def t_render():
    doc = ctx["doc"]
    msgs = []
    status = "PASS"
    for a in objects_of(doc, "Annotation"):
        vp = a.ViewObject.Proxy
        npts = vp.data.point.getNum() if hasattr(vp, "data") else -1
        texts = [str(t.string.getValues()[0]) if t.string.getNum() else ""
                 for t in getattr(vp, "textGT", [])]
        texts = [t for t in texts if t]
        df = str(vp.textDF.string.getValues()[0]) if hasattr(vp, "textDF") and vp.textDF.string.getNum() else ""
        if npts <= 0:
            status = "FAIL"
        msgs.append("{}: points={} textes={} DF='{}'".format(a.Label, npts, texts, df))
    return status, " | ".join(msgs)


def t_groups():
    doc = ctx["doc"]
    msgs, status = [], "PASS"
    for a in objects_of(doc, "Annotation"):
        parent = a.getParentGroup()
        pname = parent.Name if parent else None
        if not pname or not gdt_type(parent) or getattr(parent, "Type", "") != "Plane":
            status = "FAIL"
        msgs.append("{} -> {}".format(a.Label, pname))
    return status, "; ".join(msgs)


def t_inventory():
    if not is_active("dd_inventory"):
        return "FAIL", "commande inactive"
    Gui.runCommand("dd_inventory")
    pump(10)
    n = len([b for b in mw().findChildren(QtWidgets.QPushButton)
             if b.isVisible() and b.text() == "Modify"])
    close_task_dialog()
    if n == 0:
        return "FAIL", "aucun formulaire Modify visible"
    return "{} formulaires".format(n)


def _inventory_form(label):
    """Open the inventory and return (form widget, Modify button, Delete button)."""
    Gui.runCommand("dd_inventory")
    pump(10)
    form = modify = delete = None
    for b in mw().findChildren(QtWidgets.QPushButton):
        if b.text() in ("Modify", "Delete") and b.parent() is not None \
                and b.parent().windowTitle() == label:
            form = b.parent()
            if b.text() == "Modify":
                modify = b
            else:
                delete = b
    return form, modify, delete


def t_inventory_modify():
    gt = ctx["gt"]
    form, modify, _ = _inventory_form(gt.Label)
    if modify is None:
        close_task_dialog()
        return "FAIL", "formulaire {} introuvable".format(gt.Label)
    fields = [e for e in form.findChildren(QtWidgets.QLineEdit)
              if e.metaObject().className() == "Gui::InputField"]
    fields[0].setText("0.1 mm")
    pump()
    modify.click()
    pump(10)
    close_task_dialog()
    ok = abs(gt.ToleranceValue - 0.1) < 1e-9
    return ("PASS" if ok else "FAIL"), "ToleranceValue={}".format(gt.ToleranceValue)


def t_inventory_delete():
    doc = ctx["doc"]
    ds = ctx["ds"]
    label, name = ds.Label, ds.Name
    n = len(objects_of(doc, "DatumSystem"))
    _, _, delete = _inventory_form(label)
    if delete is None:
        close_task_dialog()
        return "FAIL", "formulaire {} introuvable".format(label)
    delete.click()
    pump(10)
    close_task_dialog()
    n2 = len(objects_of(doc, "DatumSystem"))
    gone = doc.getObject(name) is None
    return ("PASS" if gone and n2 == n - 1 else "FAIL"), "DatumSystem {} -> {}".format(n, n2)


def t_save_reopen():
    doc = ctx["doc"]
    before = gdt_inventory(doc)
    labels = sorted(o.Label for o in doc.Objects)
    path = os.path.join(WORKDIR, "gdt_roundtrip.FCStd")
    doc.saveAs(path)
    App.closeDocument(doc.Name)
    pump(10)
    doc2 = App.openDocument(path)
    pump(10)
    doc2.recompute()
    pump(10)
    after = gdt_inventory(doc2)
    labels2 = sorted(o.Label for o in doc2.Objects)
    bad = invalid_objects(doc2)
    vp_missing = [o.Name for o in doc2.Objects if gdt_type(o) and
                  getattr(o.ViewObject, "Proxy", None) is None]
    ctx["doc"] = doc2
    detail = "avant={} apres={} invalides={} VP manquants={}".format(before, after, bad, vp_missing)
    ok = before == after and labels == labels2 and not bad and not vp_missing
    return ("PASS" if ok else "FAIL"), detail


def t_body_face():
    """Annotation plane on a face of a PartDesign feature inside a Body (I-04)."""
    doc = App.newDocument("GDTBody")
    body = doc.addObject("PartDesign::Body", "Body")
    box = doc.addObject("PartDesign::AdditiveBox", "Box")
    body.addObject(box)
    box.Length, box.Width, box.Height = 20, 20, 5
    body.Placement.Base = App.Vector(100, 0, 0)
    doc.recompute()
    pump(5)
    select_in_body(body, "Box.Face6")
    if not is_active("dd_annotationPlane"):
        App.closeDocument(doc.Name)
        return "FAIL", "commande inactive"
    Gui.runCommand("dd_annotationPlane")
    pump(10)
    b = task_button("Add Annotation Plane")
    if b is None:
        App.closeDocument(doc.Name)
        return "FAIL", "bouton du panneau introuvable"
    b.click()
    pump(10)
    close_task_dialog()
    aps = objects_of(doc, "AnnotationPlane")
    detail = "AP={}".format(len(aps))
    status = "FAIL"
    if aps:
        p1 = aps[0].p1
        detail += " p1={} (attendu x~110, z=5)".format(p1)
        if abs(p1.x - 110) < 1e-6 and abs(p1.z - 5) < 1e-6:
            status = "PASS"
    doc.recompute()
    pump()
    App.closeDocument(doc.Name)
    return status, detail


def t_samples():
    files = sorted(glob.glob(os.path.join(SAMPLES, "*.FCStd"))) if SAMPLES else []
    if not files:
        return "WARN", "aucun fichier historique"
    lines, status = [], "PASS"
    for src in files:
        dst = os.path.join(WORKDIR, "hist_" + os.path.basename(src))
        shutil.copyfile(src, dst)
        console_since_last()
        try:
            d = App.openDocument(dst)
            pump(10)
            # anchor points as stored in the file (computed by the old code)
            stored = {o.Name: App.Vector(o.p1) for o in d.Objects
                      if gdt_type(o) in ("AnnotationPlane", "Annotation")}
            d.recompute()
            pump(10)
            drift = max([(d.getObject(n).p1 - v).Length for n, v in stored.items()] or [0.0])
            inv = gdt_inventory(d)
            bad = invalid_objects(d)
            noproxy = [o.Name for o in d.Objects if o.TypeId.endswith("Python") and
                       getattr(o, "Proxy", None) is None]
            probs = console_problems(console_since_last())
            # save with the current code, reopen: link scope warnings must be gone
            resaved = os.path.join(WORKDIR, "resaved_" + os.path.basename(src))
            d.saveAs(resaved)
            App.closeDocument(d.Name)
            pump()
            console_since_last()
            d = App.openDocument(resaved)
            pump(10)
            scope = [l for l in console_since_last().splitlines() if "allowed scope" in l]
            # drift is informative: it also exists with the original code (face
            # renumbering between FreeCAD versions), see the test report
            ok = not bad and not noproxy and not probs and not scope
            st = "OK" if ok else "PB"
            if st != "OK":
                status = "WARN" if status == "PASS" else status
            lines.append("{} [{}] {} derive_p1={:.3g} invalides={} sansProxy={} "
                         "avert_portee_apres_reenregistrement={} console={}".format(
                             os.path.basename(src), st, inv, drift, bad, noproxy,
                             len(scope), probs[:3]))
            App.closeDocument(d.Name)
        except Exception as e:
            status = "FAIL"
            lines.append("{} [EXC] {}".format(os.path.basename(src), e))
        pump()
    return status, "\n".join(lines)


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def finish():
    startup = ctx.get("startup_console", "")
    data = {
        "freecad": ".".join(App.Version()[:3]),
        "python": sys.version.split()[0],
        "qt": QtCore.qVersion(),
        "startup_problems": console_problems(startup),
        "results": results,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    for name in list(App.listDocuments()):
        try:
            App.closeDocument(name)
        except Exception:
            pass
    pump()
    os._exit(0)


def main():
    try:
        ctx["startup_console"] = console_since_last()
        steps = [
            ("T24", "Chargement differe (rien d'importe au demarrage)", t_lazy_loading),
            ("T01", "Workbench enregistre", t_wb_registered),
            ("T02", "Activation du workbench", t_activate),
            ("T03", "Barre d'outils et menu", t_toolbar_menu),
            ("T04", "Commandes et icones", t_commands_icons),
            ("T05", "Document de test", t_setup_doc),
            ("T06", "Creation Annotation Plane", t_create_ap),
            ("T07", "Creation Datum Feature (+DS auto)", t_create_df),
            ("T08", "Creation Datum System", t_create_ds),
            ("T09", "Creation Geometric Tolerance", t_create_gt),
            ("T10", "Tolerance sur cylindre (diametre)", t_create_gt_cyl),
            ("T17", "GT ajoutee a l'annotation existante", t_gt_existing_annotation),
            ("T18", "Selection multi-objets", t_multi_object_selection),
            ("T19", "Plan de travail Draft aligne sur l'AP", t_working_plane),
            ("T21", "Couleur de la face referencee (opaque)", t_face_color),
            ("T11", "Rendu Coin des annotations", t_render),
            ("T12", "Rangement dans le groupe du plan", t_groups),
            ("T13", "Inventaire", t_inventory),
            ("T22", "Inventaire : modification d'une GT", t_inventory_modify),
            ("T23", "Inventaire : suppression d'un DS", t_inventory_delete),
            ("T14", "Sauvegarde / reouverture", t_save_reopen),
            ("T15", "Face d'une fonction dans un Body", t_body_face),
            ("T20", "Face non-Tip d'un Body dans un App::Part deplace", t_body_non_tip),
            ("T16", "Fichiers historiques Doc/*.FCStd", t_samples),
        ]
        prereq = {"T06": "T05", "T07": "T06", "T08": "T07", "T09": "T06",
                  "T10": "T06", "T11": "T07", "T12": "T07", "T14": "T05",
                  "T17": "T07", "T18": "T06", "T19": "T07", "T21": "T07",
                  "T22": "T09", "T23": "T08"}
        status = {}
        for tid, name, func in steps:
            if tid in ("T02", "T03", "T04", "T05") and status.get("T01") == "FAIL":
                record(tid, name, "SKIP", "workbench absent")
                status[tid] = "SKIP"
                continue
            dep = prereq.get(tid)
            if dep and status.get(dep) in ("FAIL", "SKIP"):
                record(tid, name, "SKIP", "prerequis {} en echec".format(dep))
                status[tid] = "SKIP"
                continue
            status[tid] = run(tid, name, func)
            close_task_dialog()
    except Exception:
        record("TXX", "Erreur du banc de test", "FAIL", traceback.format_exc())
    finish()


QtCore.QTimer.singleShot(3000, main)
