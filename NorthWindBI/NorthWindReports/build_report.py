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

from report_contract import connection_files, pages

HERE = Path(__file__).resolve().parent
SCHEMA = (
    "https://developer.microsoft.com/json-schemas/"
    "fabric/item/report/definition/"
)

# Design tokens - formatting only, no query semantics.
PAGE_BG = "#F0F2F5"
PANEL_BG = "#FFFFFF"
TEXT = "#252423"
BORDER = "#D2D0CE"
LABEL_FONT = "Segoe UI"
HEADING_FONT = "Segoe UI"
HEADING_RECT = (32, 16, 1376, 44)
FOOTER_RECT = (32, 784, 1376, 18)
FOOTER_TEXT = "Proyecto NorthWind BI - Grupo 5 | Business Intelligence"

# Paleta estándar clásica de Power BI con colores semánticos por métrica:
BLUE_SALES = "#118DFF"       # Azul clásico Power BI para Ventas / Facturación
GREEN_VOLUME = "#01B8AA"     # Verde agua para Unidades / Pedidos
ORANGE_DISCOUNT = "#FD625E"  # Rojo/Coral para Descuentos
AMBER_FREIGHT = "#F2C80F"    # Ámbar/Amarillo para Flete
PURPLE_LOGISTICS = "#744DA9" # Púrpura/Morado para Tiempos y Logística

# Selection sources/targets for native cross-filtering interactions.
FILTERING_SOURCES = {"slicer", "barChart", "lineChart", "tableEx"}
FILTERING_TARGETS = {"card", "barChart", "lineChart", "tableEx"}

THEME = {
    "name": "NorthWind",
    "dataColors": [
        BLUE_SALES, GREEN_VOLUME, ORANGE_DISCOUNT, AMBER_FREIGHT,
        PURPLE_LOGISTICS, "#374649", "#8AD4EB", "#FE9666"
    ],
    "background": "#FFFFFF",
    "foreground": "#252423",
    "tableAccent": BLUE_SALES,
    "textClasses": {
        "title": {"fontFace": LABEL_FONT, "fontSize": 11, "color": TEXT},
        "header": {"fontFace": HEADING_FONT, "fontSize": 18, "color": TEXT},
        "callout": {"fontFace": LABEL_FONT, "fontSize": 26, "color": TEXT},
        "label": {"fontFace": LABEL_FONT, "fontSize": 9, "color": TEXT},
    },
}


def visual_theme(entry):
    title = entry["title"]
    if "Descuento" in title:
        return ORANGE_DISCOUNT, "discount"
    if "Unidades" in title or title in ("Pedidos", "Pedidos Enviados"):
        return GREEN_VOLUME, "volume"
    if "Flete" in title:
        return AMBER_FREIGHT, "freight"
    if "envío" in title.lower() or "días" in title.lower() or "dias" in title.lower():
        return PURPLE_LOGISTICS, "logistics"
    return BLUE_SALES, "sales" 


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
            "radius": lit("4D"),
        }}],
    }


# Contract action type -> visualLink property that carries the target.
ACTION_PROPS = {"PageNavigation": "navigationSection"}


def button_visual(entry):
    """Action-button objects in the dual-entry pattern the engine requires."""
    action = entry["action"]
    link = {"show": lit("true"), "type": lit(f"'{action['type']}'")}
    if action.get("target"):
        link[ACTION_PROPS[action["type"]]] = lit(f"'{action['target']}'")
    if entry.get("tooltip"):
        link["tooltip"] = lit(f"'{entry['tooltip']}'")
    selected = entry.get("selected")
    accent = (entry.get("appearance") or {}).get("accent")
    if accent and not selected:
        fill_color, font_color = accent, "#FFFFFF"
        font_size, icon_show, icon_place = "16D", "true", "'right'"
        icon_props = {
            "shapeType": lit("'rightArrow'"),
            "placement": lit(icon_place),
            "lineColor": solid("#FFFFFF"),
        }
        outline = [{"properties": {"show": lit("false")}}]
        fill = [
            {"properties": {"show": lit("true")}},
            {"properties": {"fillColor": solid(fill_color)},
             "selector": {"id": "default"}},
            {"properties": {"fillColor": solid(
                entry["appearance"].get("hover", accent))},
             "selector": {"id": "hover"}},
        ]
    else:
        fill_color = BLUE_SALES if selected else PANEL_BG
        font_color = PANEL_BG if selected else BLUE_SALES
        font_size, icon_show, icon_place = "11D", "false", "'left'"
        icon_props = {
            "shapeType": lit("'rightArrow'"),
            "placement": lit(icon_place),
        }
        outline = [{"properties": {"show": lit("false")}}] if selected else [
            {"properties": {"show": lit("true")}},
            {"properties": {"color": solid(BLUE_SALES)},
             "selector": {"id": "default"}},
        ]
        fill = [
            {"properties": {"show": lit("true")}},
            {"properties": {"fillColor": solid(fill_color)},
             "selector": {"id": "default"}},
        ]
    return {
        "visualType": "actionButton",
        "objects": {
            "text": [
                {"properties": {"show": lit("true")}},
                {"properties": {
                    "text": lit(f"'{entry['title']}'"),
                    "fontSize": lit(font_size),
                    "fontFamily": lit(f"'{LABEL_FONT}'"),
                    "fontColor": solid(font_color),
                    "horizontalAlignment": lit("'center'"),
                }, "selector": {"id": "default"}},
            ],
            "icon": [
                {"properties": {"show": lit(icon_show)}},
                {"properties": icon_props,
                 "selector": {"id": "default"}},
            ],
            "fill": fill,
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


def image_visual(entry):
    """Packaged PNG via ResourcePackageItem; visualLink when actionable."""
    info = entry["image"]
    container = {
        "title": [{"properties": {"show": lit("false")}}],
        "background": [{"properties": {"show": lit("false")}}],
        "border": [{"properties": {"show": lit("false")}}],
        "general": [{"properties": {
            "altText": lit(f"'{info['alt']}'")}}],
    }
    action = entry.get("action")
    if action:
        link = {"show": lit("true"), "type": lit(f"'{action['type']}'")}
        if action.get("target"):
            link[ACTION_PROPS[action["type"]]] = lit(
                f"'{action['target']}'")
        container["visualLink"] = [{"properties": link}]
    return {
        "visualType": "image",
        "objects": {
            "general": [{"properties": {"imageUrl": {"expr": {
                "ResourcePackageItem": {
                    "PackageName": "RegisteredResources",
                    "PackageType": 1,
                    "ItemName": info["resource"],
                }}}}}],
            "imageScaling": [{"properties": {
                "imageScalingType": lit("'Normal'")}}],
        },
        "visualContainerObjects": container,
    }


def text_visual(entry):
    """Narrative textbox: separate bold title and regular body paragraphs."""
    info = entry["text"]
    strong = info.get("strong", True)
    paragraphs = [{
        "horizontalTextAlignment": "left",
        "textRuns": [{"value": info["title"], "textStyle": {
            "fontFamily": LABEL_FONT,
            "fontSize": "12pt" if strong else "10pt",
            "fontWeight": "bold" if strong else "normal",
            "color": TEXT}}],
    }]
    if info.get("body"):
        paragraphs.append({
            "horizontalTextAlignment": "left",
            "textRuns": [{"value": info["body"], "textStyle": {
                "fontFamily": LABEL_FONT, "fontSize": "10pt",
                "color": TEXT}}],
        })
    boxed = bool(info.get("panel"))
    background = {"show": lit("true" if boxed else "false")}
    border = {"show": lit("true" if boxed else "false")}
    if boxed:
        background["color"] = solid(PANEL_BG)
        background["transparency"] = lit("0D")
        border["color"] = solid(BORDER)
        border["radius"] = lit("4D")
    return {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": paragraphs}}]},
        "visualContainerObjects": {
            "title": [{"properties": {"show": lit("false")}}],
            "background": [{"properties": background}],
            "border": [{"properties": border}],
        },
    }


def visual_doc(entry, z):
    rect = entry["rect"]
    kind = entry["visual"]["visualType"]
    if kind == "actionButton":
        visual = button_visual(entry)
    elif kind == "image":
        visual = image_visual(entry)
    elif kind == "textbox":
        visual = text_visual(entry)
    else:
        visual = copy.deepcopy(entry["visual"])
        visual["visualContainerObjects"] = panel_objects(entry["title"])
        objects = visual.setdefault("objects", {})
        color, _ = visual_theme(entry)
        if kind in ("barChart", "lineChart"):
            objects["dataPoint"] = [
                {"properties": {"defaultColor": solid(color)}}
            ]
            objects["labels"] = [
                {"properties": {"show": lit("true")}}
            ]
        elif kind == "card":
            objects["labels"] = [{"properties": {"color": solid(color)}}]
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
    return doc


def textbox_doc(name, rect, text, style, z, bg_color=None, border_color=None):
    show_box = "true" if bg_color else "false"
    bg_props = {"show": lit(show_box)}
    if bg_color:
        bg_props["color"] = solid(bg_color)
        bg_props["transparency"] = lit("0D")
    border_props = {"show": lit(show_box)}
    if border_color or bg_color:
        border_props["color"] = solid(border_color or bg_color)
        border_props["radius"] = lit("4D")
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
                "background": [{"properties": bg_props}],
                "border": [{"properties": border_props}],
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
    for key in ("type", "pageBinding", "filterConfig"):
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
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def layout_js(model_pages):
    """JS data block consumed by preview.html; contract fields only."""
    data = [{
        "name": page["name"],
        "title": page["title"],
        "hr": page.get("heading_rect", list(HEADING_RECT)),
        "visuals": [{
            "name": v["name"],
            "title": v["title"],
            "t": v["visual"]["visualType"],
            "r": v["rect"],
            "cls": visual_theme(v)[1],
            "text": v.get("text"),
            "image": v.get("image"),
            "action": v.get("action"),
            "appearance": v.get("appearance"),
        } for v in page["visuals"]],
    } for page in model_pages]
    return (
        "// Generated by build_report.py from report_contract.py - "
        "do not edit.\nconst PAGES = "
        + json.dumps(data, indent=2, ensure_ascii=True) + ";\n"
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
        expected |= {f"{page['name']}_heading", f"{page['name']}_footer"}
        expected_names[page["name"]] = expected
    guard_dirs(pages_dir, set(names), "page directories")
    for page in model_pages:
        guard_dirs(pages_dir / page["name"] / "visuals",
                   expected_names[page["name"]], "visual directories")

    # Every packaged image must exist before a single byte is written.
    resources = {}
    for page in model_pages:
        for entry in page["visuals"]:
            info = entry.get("image")
            if info:
                name = info["resource"]
                if name in resources:
                    continue
                path = HERE / "assets" / "home" / name
                if not path.is_file():
                    sys.exit(f"missing image asset: {path}")
                resources[name] = path

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
                       "type": "CustomTheme"}] + [
                {"name": r, "path": r, "type": "Image"}
                for r in sorted(resources)]}],
    })
    static_dir = report / "StaticResources" / "RegisteredResources"
    write_json(static_dir / "NorthWind.json", THEME)
    for name, path in sorted(resources.items()):
        (static_dir / name).write_bytes(path.read_bytes())
    write_json(pages_dir / "pages.json", {
        "$schema": SCHEMA + "pagesMetadata/1.0.0/schema.json",
        "pageOrder": names, "activePageName": names[0],
    })
    (output / "preview-layout.js").write_text(
        layout_js(model_pages), encoding="utf-8")

    written = 0
    for page in model_pages:
        page_dir = pages_dir / page["name"]
        visuals_dir = page_dir / "visuals"
        write_json(page_dir / "page.json", page_doc(page))
        heading = textbox_doc(
            f"{page['name']}_heading",
            page.get("heading_rect", HEADING_RECT),
            f"NORTHWIND / {page['title']}",
            {"fontFamily": HEADING_FONT, "fontSize": "16pt",
             "fontWeight": "bold", "color": "#FFFFFF"}, 0,
            bg_color=BLUE_SALES, border_color=BLUE_SALES)
        write_json(visuals_dir / heading["name"] / "visual.json", heading)
        for z, entry in enumerate(page["visuals"], start=1):
            doc = visual_doc(entry, z)
            write_json(visuals_dir / entry["name"] / "visual.json", doc)
            written += 1
        footer = textbox_doc(
            f"{page['name']}_footer", FOOTER_RECT, FOOTER_TEXT,
            {"fontFamily": LABEL_FONT, "fontSize": "8pt",
             "color": TEXT}, len(page["visuals"]) + 1)
        write_json(visuals_dir / footer["name"] / "visual.json", footer)
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
