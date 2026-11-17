#!/usr/bin/env python3
"""One-time helper to extract IDML stories + hyperlink URLs into draft YAML/JSON.

This is EOL - I used it once to migrate my InDesign CV to the Typst version.
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def load_hyperlinks(idml_dir: Path) -> dict[str, str]:
    root = ET.parse(idml_dir / "designmap.xml").getroot()
    dests = {}
    for d in root.findall(".//HyperlinkURLDestination"):
        dests[d.attrib["DestinationUniqueKey"]] = d.attrib.get("DestinationURL", "").strip()

    source_to_url = {}
    for h in root.findall(".//Hyperlink"):
        src = h.attrib.get("Source")
        key = h.attrib.get("DestinationUniqueKey")
        if src and key in dests:
            url = dests[key]
            # Normalize missing scheme from InDesign quirks
            if url.startswith(("github.com/", "gitlab.")):
                url = "https://" + url
            source_to_url[src] = url
    return source_to_url


def extract_paragraph_markup(p_elem: ET.Element, urls: dict[str, str]) -> str:
    parts = []

    def walk_csr(csr: ET.Element):
        style = csr.attrib.get("AppliedCharacterStyle", "")
        font_style = csr.attrib.get("FontStyle", "")
        pos = csr.attrib.get("Position", "")
        is_bold = "Bold" in style or "BOLD" in style or "Bold" in font_style
        is_italic = "Italic" in font_style
        is_super = "superscr" in style or pos == "Superscript"

        for child in csr:
            if child.tag == "Content" and child.text:
                txt = child.text
                if is_bold and is_italic:
                    parts.append(f"***{txt}***")
                elif is_bold:
                    parts.append(f"**{txt}**")
                elif is_italic:
                    parts.append(f"*{txt}*")
                else:
                    parts.append(txt)
            elif child.tag == "Br":
                parts.append("\n")
            elif child.tag == "HyperlinkTextSource":
                hid = child.attrib.get("Self")
                url = urls.get(hid, "")
                # Collect text inside hyperlink (may be direct Content or nested CharacterStyleRange)
                htext = "".join(c.text or "" for c in child.iter("Content"))
                if is_super or any("Superscript" in c.attrib.get("Position", "") for c in child.iter("CharacterStyleRange")):
                    parts.append(f"^[{htext}]({url})")
                else:
                    parts.append(f"[{htext}]({url})")

    for csr in p_elem.findall("CharacterStyleRange"):
        walk_csr(csr)
    return "".join(parts).strip()


def extract_tables(story_path: Path, urls: dict[str, str]) -> list[list[list[str]]]:
    root = ET.parse(story_path).getroot()
    tables = []
    for tbl in root.findall(".//Table"):
        rows_map: dict[int, dict[int, str]] = {}
        for cell in tbl.findall("Cell"):
            col, row = map(int, cell.attrib["Name"].split(":"))
            paras = [extract_paragraph_markup(p, urls) for p in cell.findall("ParagraphStyleRange")]
            rows_map.setdefault(row, {})[col] = "\n".join(p for p in paras if p)
        rows = []
        for r in sorted(rows_map):
            rows.append([rows_map[r].get(c, "") for c in sorted(rows_map[r])])
        tables.append(rows)
    return tables


if __name__ == "__main__":
    idml_dir = Path(sys.argv[1])
    urls = load_hyperlinks(idml_dir)
    out = {
        "story_u145_tables": extract_tables(idml_dir / "Stories/Story_u145.xml", urls),
        "story_u163_tables": extract_tables(idml_dir / "Stories/Story_u163.xml", urls),
    }
    Path("extracted_idml.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Extracted {len(out['story_u145_tables'])} + {len(out['story_u163_tables'])} tables -> extracted_idml.json")