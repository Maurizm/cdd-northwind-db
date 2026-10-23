"""Generate the PBIP/PBIR report tree from report_contract.py.

Only formatting, layout and container metadata are added here. Every field
binding, filter, query semantic and connection string comes verbatim from
report_contract; nothing is rederived or rewritten.
"""

import argparse
import copy
import json
import sys
from pathlib import Path

from report_contract import bookmarks, connection_files, pages

HERE = Path(__file__).resolve().parent
SCHEMA = (
    "https://developer.microsoft.com/json-schemas/"
    "fabric/item/report/definition/"
)

# Design tokens - formatting only, no query semantics.
PAGE_BG = "#F5F3EE"
PANEL_BG = "#FFFFFF"
TEXT = "#253331"
TEAL = "#155E63"
ORANGE = "#D88935"
BORDER = "#E3DED4"
LABEL_FONT = "DIN"
HEADING_FONT = "Georgia"
HEADING_RECT = (32, 16, 576, 48)
STORY_RECT = (32, 768, 1088, 36)
STORY_SUFFIX = " | Importes sin moneda definida"

# Selection sources/targets for native cross-filtering interactions.
# Buttons and textboxes are never filtering sources or targets.
FILTERING_SOURCES = {
    "slicer", "barChart", "clusteredBarChart", "columnChart",
    "clusteredColumnChart", "lineChart", "lineClusteredColumnComboChart",
    "tableEx", "pivotTable", "scatterChart", "azureMap",
}
FILTERING_TARGETS = (FILTERING_SOURCES - {"slicer"}) | {"card"}
DISCOUNT_TITLES = {"Descuentos", "Tasa de Descuento"}

# Action companion property per actionButton action type.
ACTION_PROPS = {
    "PageNavigation": "navigationSection",
    "Bookmark": "bookmark",
    "Drillthrough": "drillthroughSection",
    "WebUrl": "webUrl",
}

THEME = {
    "name": "NorthWind",
    "dataColors": ["#155E63", "#D88935", "#253331", "#4E7A6F",
                   "#C7B89B", "#6B8F8A", "#A45A2A", "#8FA396"],
    "background": "#FFFFFF",
    "foreground": "#253331",
    "tableAccent": "#155E63",
    "textClasses": {
        "title": {"fontFace": "DIN", "fontSize": 11, "color": "#253331"},
        "header": {"fontFace": "Georgia", "fontSize": 18,
                   "color": "#253331"},
        "callout": {"fontFace": "DIN", "fontSize": 26, "color": "#253331"},
        "label": {"fontFace": "DIN", "fontSize": 9, "color": "#253331"},
    },
}


def lit(value):
    return {"expr": {"Literal": {"Value": value}}}


def solid(hex_color):
    return {"solid": {"color": lit(f"'{hex_color}'")}}


def panel_objects(title):
    return {
        "title": [{"properties": {
            "text": lit(f"'{title}'"),
            "show": lit("true"),
            "fontColor": solid(TEXT),
            "fontFamily": lit(f"'{LABEL_FONT}'"),
            "fontSize": lit("10D"),
            "alignment": lit("'left'"),
        }}],
        "background": [{"properties": {
            "show": lit("true"),
            "color": solid(PANEL_BG),
            "transparency": lit("0D"),
        }}],
        "border": [{"properties": {
            "show": lit("true"),
            "color": solid(BORDER),
            "radius": lit("6D"),
        }}],
    }


def button_visual(entry):
    """Action-button objects in the dual-entry pattern the engine requires."""
    action = entry["action"]
    link = {"show": lit("true"), "type": lit(f"'{action['type']}'")}
    if action.get("target"):
        link[ACTION_PROPS[action["type"]]] = lit(f"'{action['target']}'")
    selected = entry.get("selected")
    fill_color = TEAL if selected else PANEL_BG
    font_color = PANEL_BG if selected else TEAL
    outline = [{"properties": {"show": lit("false")}}] if selected else [
        {"properties": {"show": lit("true")}},
        {"properties": {"color": solid(TEAL)},
         "selector": {"id": "default"}},
    ]
    return {
        "visualType": "actionButton",
        "objects": {
            "text": [
                {"properties": {"show": lit("true")}},
                {"properties": {
                    "text": lit(f"'{entry['title']}'"),
                    "fontSize": lit("11D"),
                    "fontFamily": lit(f"'{LABEL_FONT}'"),
                    "fontColor": solid(font_color),
                    "horizontalAlignment": lit("'center'"),
                }, "selector": {"id": "default"}},
            ],
            "icon": [
                {"properties": {"show": lit("false")}},
                {"properties": {
                    "shapeType": lit("'rightArrow'"),
                    "placement": lit("'left'"),
                }, "selector": {"id": "default"}},
            ],
            "fill": [
                {"properties": {"show": lit("true")}},
                {"properties": {"fillColor": solid(fill_color)},
                 "selector": {"id": "default"}},
            ],
            "outline": outline,
            "shape": [
                {"properties": {
                    "tileShape": lit("'rectangleRounded'"),
                    "roundEdge": lit("8L")}},
                {"properties": {
                    "tileShape": lit("'rectangleRounded'")},
                 "selector": {"id": "default"}},
            ],
        },
        "visualContainerObjects": {
            "background": [{"properties": {"show": lit("false")}}],
            "border": [{"properties": {"show": lit("false")}}],
            "visualLink": [{"properties": link}],
        },
        "drillFilterOtherVisuals": True,
    }


def visual_doc(entry, z):
    rect = entry["rect"]
    kind = entry["visual"]["visualType"]
    if kind == "actionButton":
        visual = button_visual(entry)
    else:
        visual = copy.deepcopy(entry["visual"])
        visual["visualContainerObjects"] = panel_objects(entry["title"])
        objects = visual.setdefault("objects", {})
        if kind in ("barChart", "clusteredBarChart", "columnChart",
                    "clusteredColumnChart", "lineChart",
                    "lineClusteredColumnComboChart", "scatterChart"):
            objects.setdefault("dataPoint", [
                {"properties": {"defaultColor": solid(TEAL)}}
            ])
        elif kind == "card" and entry["title"] in DISCOUNT_TITLES:
            objects["labels"] = [{"properties": {"color": solid(ORANGE)}}]
        elif kind == "slicer":
            objects["data"] = [{"properties": {"mode": lit("'Dropdown'")}}]
    doc = {
        "$schema": SCHEMA + "visualContainer/2.1.0/schema.json",
        "name": entry["name"],
        "position": {
            "x": rect[0], "y": rect[1], "z": z,
            "width": rect[2], "height": rect[3], "tabOrder": z,
        },
        "visual": visual,
    }
    if "filterConfig" in entry:
        doc["filterConfig"] = copy.deepcopy(entry["filterConfig"])
    if entry.get("hidden"):
        doc["isHidden"] = True
    return doc


def textbox_doc(name, rect, text, style, z):
    return {
        "$schema": SCHEMA + "visualContainer/2.1.0/schema.json",
        "name": name,
        "position": {
            "x": rect[0], "y": rect[1], "z": z,
            "width": rect[2], "height": rect[3], "tabOrder": z,
        },
        "visual": {
            "visualType": "textbox",
            "objects": {"general": [{"properties": {"paragraphs": [{
                "horizontalTextAlignment": "left",
                "textRuns": [{"value": text, "textStyle": style}],
            }]}}]},
            "visualContainerObjects": {
                "title": [{"properties": {"show": lit("false")}}],
                "background": [{"properties": {"show": lit("false")}}],
                "border": [{"properties": {"show": lit("false")}}],
            },
        },
    }


def page_doc(page):
    doc = {
        "$schema": SCHEMA + "page/1.4.0/schema.json",
        "name": page["name"],
        "displayName": page["title"],
        "displayOption": "FitToPage",
        "width": page["width"],
        "height": page["height"],
        "objects": {"background": [{"properties": {
            "color": solid(PAGE_BG), "transparency": lit("0D")}}]},
        "visualInteractions": page_interactions(page),
    }
    for key in ("type", "pageBinding", "filterConfig", "visibility"):
        if key in page:
            doc[key] = copy.deepcopy(page[key])
    return doc


def page_interactions(page):
    sources = [v["name"] for v in page["visuals"]
               if v["visual"]["visualType"] in FILTERING_SOURCES]
    return [
        {"source": source, "target": target["name"], "type": "DataFilter"}
        for target in page["visuals"]
        if target["visual"]["visualType"] in FILTERING_TARGETS
        for source in sources
        if source != target["name"]
    ]


def guard_dirs(root, expected, label):
    if not root.is_dir():
        return
    extra = sorted(d.name for d in root.iterdir()
                   if d.is_dir() and d.name not in expected)
    if extra:
        sys.exit(
            f"refusing to overwrite unexpected {label} under "
            f"{root}: {', '.join(extra)}"
        )


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def layout_js(model_pages):
    """JS data block consumed by preview.html; contract fields only."""
    data = [{
        "name": page["name"],
        "title": page["title"],
        "story": page["story"] + STORY_SUFFIX,
        "visuals": [{
            "name": v["name"],
            "title": v["title"],
            "t": v["visual"]["visualType"],
            "r": v["rect"],
            **({"cls": "discount"} if v["title"] in DISCOUNT_TITLES else {}),
            **({"h": True} if v.get("hidden") else {}),
        } for v in page["visuals"]],
    } for page in model_pages]
    return (
        "// Generated by build_report.py from report_contract.py - "
        "do not edit.\nconst PAGES = "
        + json.dumps(data, indent=2, ensure_ascii=False) + ";\n"
    )


def build(server, database, output):
    report = output / "NorthWind.Report"
    pages_dir = report / "definition" / "pages"
    model_pages = pages()
    names = [p["name"] for p in model_pages]

    # Fail safely up front: refuse to run if the tree contains anything we
    # did not generate, instead of deleting a user's own visuals.
    expected_names = {}
    for page in model_pages:
        expected = {v["name"] for v in page["visuals"]}
        expected |= {f"{page['name']}_heading", f"{page['name']}_story"}
        expected_names[page["name"]] = expected
    guard_dirs(pages_dir, set(names), "page directories")
    for page in model_pages:
        guard_dirs(pages_dir / page["name"] / "visuals",
                   expected_names[page["name"]], "visual directories")
    bookmarks_dir = report / "definition" / "bookmarks"
    guard_dirs(bookmarks_dir, set(), "bookmark directories")

    for rel, payload in connection_files(server, database).items():
        write_json(output / rel, payload)

    write_json(report / "definition" / "version.json", {
        "$schema": SCHEMA + "versionMetadata/1.0.0/schema.json",
        "version": "2.0.0",
    })
    write_json(report / "definition" / "report.json", {
        "$schema": SCHEMA + "report/2.0.0/schema.json",
        "themeCollection": {"customTheme": {
            "name": "NorthWind", "reportVersionAtImport": "2.0.0",
            "type": "RegisteredResources"}},
        "resourcePackages": [{
            "name": "RegisteredResources", "type": "RegisteredResources",
            "items": [{"name": "NorthWind", "path": "NorthWind.json",
                       "type": "CustomTheme"}]}],
    })
    write_json(report / "StaticResources" / "RegisteredResources" /
               "NorthWind.json", THEME)
    write_json(pages_dir / "pages.json", {
        "$schema": SCHEMA + "pagesMetadata/1.0.0/schema.json",
        "pageOrder": names, "activePageName": names[0],
    })
    bookmark_data = bookmarks()
    write_json(bookmarks_dir / "bookmarks.json", {
        "$schema": SCHEMA + "bookmarksMetadata/1.0.0/schema.json",
        "items": bookmark_data["items"],
    })
    for bookmark_name, payload in bookmark_data["files"].items():
        write_json(bookmarks_dir / f"{bookmark_name}.bookmark.json",
                   {"$schema": SCHEMA + "bookmark/2.1.0/schema.json",
                    **payload})
    (output / "preview-layout.js").write_text(
        layout_js(model_pages), encoding="utf-8")

    written = 0
    for page in model_pages:
        page_dir = pages_dir / page["name"]
        visuals_dir = page_dir / "visuals"
        write_json(page_dir / "page.json", page_doc(page))
        heading = textbox_doc(
            f"{page['name']}_heading", HEADING_RECT,
            f"NORTHWIND / {page['title']}",
            {"fontFamily": HEADING_FONT, "fontSize": "20pt",
             "fontWeight": "bold", "color": TEXT}, 0)
        write_json(visuals_dir / heading["name"] / "visual.json", heading)
        for z, entry in enumerate(page["visuals"], start=1):
            doc = visual_doc(entry, z)
            write_json(visuals_dir / entry["name"] / "visual.json", doc)
            written += 1
        story = textbox_doc(
            f"{page['name']}_story", STORY_RECT,
            page["story"] + STORY_SUFFIX,
            {"fontFamily": HEADING_FONT, "fontSize": "10pt",
             "fontStyle": "italic", "color": TEXT},
            len(page["visuals"]) + 1)
        write_json(visuals_dir / story["name"] / "visual.json", story)
        written += 2
    return names, written


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssas-server", default="localhost")
    parser.add_argument("--ssas-database", default="NorthWindOLAP")
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    page_names, visual_count = build(
        args.ssas_server, args.ssas_database, args.output)
    print(f"Generated report for {args.ssas_server}/{args.ssas_database}: "
          f"{len(page_names)} pages, {visual_count} visuals under "
          f"{args.output}")
