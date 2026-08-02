#!/usr/bin/env python3
"""Add speaker notes from the transcript markdown into the research deck."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "研究進度-cFS-FreeRTOS-POC.pptx"
TRANSCRIPT = ROOT / "研究進度-逐字稿.md"
OUT = ROOT / "研究進度-cFS-FreeRTOS-POC-含逐字稿.pptx"

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

ET.register_namespace("p", P_NS)
ET.register_namespace("a", A_NS)
ET.register_namespace("r", R_NS)


def q(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


def xml_bytes(root: ET.Element) -> bytes:
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def parse_notes() -> list[str]:
    text = TRANSCRIPT.read_text(encoding="utf-8")
    parts = re.split(r"^## 第 \d+ 頁：.*$", text, flags=re.MULTILINE)
    notes = [part.strip() for part in parts[1:]]
    if len(notes) != 6:
        raise RuntimeError(f"Expected 6 note sections, got {len(notes)}")
    return notes


def next_rid(root: ET.Element) -> str:
    max_id = 0
    for rel in root.findall(q(REL_NS, "Relationship")):
        rid = rel.attrib.get("Id", "")
        if rid.startswith("rId") and rid[3:].isdigit():
            max_id = max(max_id, int(rid[3:]))
    return f"rId{max_id + 1}"


def add_relationship(xml: bytes, rel_id: str, rel_type: str, target: str) -> bytes:
    root = ET.fromstring(xml)
    for rel in root.findall(q(REL_NS, "Relationship")):
        if rel.attrib.get("Type") == rel_type and rel.attrib.get("Target") == target:
            return xml
    rel = ET.SubElement(root, q(REL_NS, "Relationship"))
    rel.set("Id", rel_id)
    rel.set("Type", rel_type)
    rel.set("Target", target)
    return xml_bytes(root)


def add_content_type_overrides(xml: bytes, slide_count: int) -> bytes:
    root = ET.fromstring(xml)
    existing = {node.attrib.get("PartName") for node in root.findall(q(CT_NS, "Override"))}

    additions = [
        (
            "/ppt/notesMasters/notesMaster1.xml",
            "application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml",
        )
    ]
    additions.extend(
        (
            f"/ppt/notesSlides/notesSlide{i}.xml",
            "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml",
        )
        for i in range(1, slide_count + 1)
    )

    for part_name, content_type in additions:
        if part_name not in existing:
            node = ET.SubElement(root, q(CT_NS, "Override"))
            node.set("PartName", part_name)
            node.set("ContentType", content_type)

    return xml_bytes(root)


def add_notes_master_to_presentation(xml: bytes, rel_id: str) -> bytes:
    root = ET.fromstring(xml)
    if root.find(q(P_NS, "notesMasterIdLst")) is not None:
        return xml

    notes_list = ET.Element(q(P_NS, "notesMasterIdLst"))
    notes_id = ET.SubElement(notes_list, q(P_NS, "notesMasterId"))
    notes_id.set("id", "2147483648")
    notes_id.set(q(R_NS, "id"), rel_id)

    sld_master = root.find(q(P_NS, "sldMasterIdLst"))
    insert_at = list(root).index(sld_master) + 1 if sld_master is not None else 0
    root.insert(insert_at, notes_list)
    return xml_bytes(root)


def make_notes_master_xml() -> bytes:
    root = ET.Element(q(P_NS, "notesMaster"))

    c_sld = ET.SubElement(root, q(P_NS, "cSld"))
    sp_tree = ET.SubElement(c_sld, q(P_NS, "spTree"))
    nv_grp = ET.SubElement(sp_tree, q(P_NS, "nvGrpSpPr"))
    ET.SubElement(nv_grp, q(P_NS, "cNvPr"), {"id": "1", "name": ""})
    ET.SubElement(nv_grp, q(P_NS, "cNvGrpSpPr"))
    ET.SubElement(nv_grp, q(P_NS, "nvPr"))
    grp = ET.SubElement(sp_tree, q(P_NS, "grpSpPr"))
    ET.SubElement(grp, q(A_NS, "xfrm"))

    ET.SubElement(
        root,
        q(P_NS, "clrMap"),
        {
            "bg1": "lt1",
            "tx1": "dk1",
            "bg2": "lt2",
            "tx2": "dk2",
            "accent1": "accent1",
            "accent2": "accent2",
            "accent3": "accent3",
            "accent4": "accent4",
            "accent5": "accent5",
            "accent6": "accent6",
            "hlink": "hlink",
            "folHlink": "folHlink",
        },
    )
    return xml_bytes(root)


def make_notes_master_rels() -> bytes:
    root = ET.Element(q(REL_NS, "Relationships"))
    rel = ET.SubElement(root, q(REL_NS, "Relationship"))
    rel.set("Id", "rId1")
    rel.set("Type", f"{R_NS}/theme")
    rel.set("Target", "../theme/theme1.xml")
    return xml_bytes(root)


def add_text_body(parent: ET.Element, text: str) -> None:
    tx_body = ET.SubElement(parent, q(P_NS, "txBody"))
    ET.SubElement(tx_body, q(A_NS, "bodyPr"))
    ET.SubElement(tx_body, q(A_NS, "lstStyle"))
    for paragraph_text in text.split("\n\n"):
        p = ET.SubElement(tx_body, q(A_NS, "p"))
        r = ET.SubElement(p, q(A_NS, "r"))
        ET.SubElement(
            r,
            q(A_NS, "rPr"),
            {"lang": "zh-TW", "sz": "1200", "dirty": "0"},
        )
        t = ET.SubElement(r, q(A_NS, "t"))
        t.text = paragraph_text.replace("\n", " ")
        ET.SubElement(p, q(A_NS, "endParaRPr"), {"lang": "zh-TW", "sz": "1200"})


def add_placeholder(sp_tree: ET.Element, shape_id: int, name: str, ph_type: str, idx: str, text: str | None = None) -> None:
    sp = ET.SubElement(sp_tree, q(P_NS, "sp"))
    nv = ET.SubElement(sp, q(P_NS, "nvSpPr"))
    ET.SubElement(nv, q(P_NS, "cNvPr"), {"id": str(shape_id), "name": name})
    c_nv_sp = ET.SubElement(nv, q(P_NS, "cNvSpPr"))
    ET.SubElement(c_nv_sp, q(A_NS, "spLocks"), {"noGrp": "1"})
    nv_pr = ET.SubElement(nv, q(P_NS, "nvPr"))
    ET.SubElement(nv_pr, q(P_NS, "ph"), {"type": ph_type, "idx": idx})
    ET.SubElement(sp, q(P_NS, "spPr"))
    if text is not None:
        add_text_body(sp, text)


def make_notes_slide_xml(notes: str) -> bytes:
    root = ET.Element(q(P_NS, "notes"))

    c_sld = ET.SubElement(root, q(P_NS, "cSld"))
    sp_tree = ET.SubElement(c_sld, q(P_NS, "spTree"))
    nv_grp = ET.SubElement(sp_tree, q(P_NS, "nvGrpSpPr"))
    ET.SubElement(nv_grp, q(P_NS, "cNvPr"), {"id": "1", "name": ""})
    ET.SubElement(nv_grp, q(P_NS, "cNvGrpSpPr"))
    ET.SubElement(nv_grp, q(P_NS, "nvPr"))
    grp = ET.SubElement(sp_tree, q(P_NS, "grpSpPr"))
    ET.SubElement(grp, q(A_NS, "xfrm"))

    add_placeholder(sp_tree, 2, "Slide Image Placeholder 1", "sldImg", "1")
    add_placeholder(sp_tree, 3, "Notes Placeholder 2", "body", "2", notes)

    clr_map = ET.SubElement(root, q(P_NS, "clrMapOvr"))
    ET.SubElement(clr_map, q(A_NS, "masterClrMapping"))
    return xml_bytes(root)


def make_notes_slide_rels(slide_idx: int) -> bytes:
    root = ET.Element(q(REL_NS, "Relationships"))
    rel_slide = ET.SubElement(root, q(REL_NS, "Relationship"))
    rel_slide.set("Id", "rId1")
    rel_slide.set("Type", f"{R_NS}/slide")
    rel_slide.set("Target", f"../slides/slide{slide_idx}.xml")
    rel_master = ET.SubElement(root, q(REL_NS, "Relationship"))
    rel_master.set("Id", "rId2")
    rel_master.set("Type", f"{R_NS}/notesMaster")
    rel_master.set("Target", "../notesMasters/notesMaster1.xml")
    return xml_bytes(root)


def main() -> None:
    notes = parse_notes()
    with zipfile.ZipFile(SRC, "r") as zf:
        package = {name: zf.read(name) for name in zf.namelist()}

    package["[Content_Types].xml"] = add_content_type_overrides(package["[Content_Types].xml"], len(notes))

    pres_rels = ET.fromstring(package["ppt/_rels/presentation.xml.rels"])
    notes_master_rid = next_rid(pres_rels)
    package["ppt/_rels/presentation.xml.rels"] = add_relationship(
        package["ppt/_rels/presentation.xml.rels"],
        notes_master_rid,
        f"{R_NS}/notesMaster",
        "notesMasters/notesMaster1.xml",
    )
    package["ppt/presentation.xml"] = add_notes_master_to_presentation(package["ppt/presentation.xml"], notes_master_rid)
    package["ppt/notesMasters/notesMaster1.xml"] = make_notes_master_xml()
    package["ppt/notesMasters/_rels/notesMaster1.xml.rels"] = make_notes_master_rels()

    for idx, note in enumerate(notes, 1):
        slide_rels_name = f"ppt/slides/_rels/slide{idx}.xml.rels"
        slide_rels_xml = package[slide_rels_name]
        slide_rels_root = ET.fromstring(slide_rels_xml)
        note_rid = next_rid(slide_rels_root)
        package[slide_rels_name] = add_relationship(
            slide_rels_xml,
            note_rid,
            f"{R_NS}/notesSlide",
            f"../notesSlides/notesSlide{idx}.xml",
        )
        package[f"ppt/notesSlides/notesSlide{idx}.xml"] = make_notes_slide_xml(note)
        package[f"ppt/notesSlides/_rels/notesSlide{idx}.xml.rels"] = make_notes_slide_rels(idx)

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in package.items():
            zf.writestr(name, data)

    print(OUT)


if __name__ == "__main__":
    main()
