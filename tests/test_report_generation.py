"""Generator mechanics only; contract semantics are not re-verified here."""

import importlib.util
import json
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "NorthWindBI" / "NorthWindReports"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTRACT = load_module("report_contract", REPORTS / "report_contract.py")
sys.modules.setdefault("report_contract", CONTRACT)
BUILD = load_module("build_report", REPORTS / "build_report.py")
PAGES = CONTRACT.pages()
SOURCES = {"slicer", "barChart", "lineChart", "tableEx"}
TARGETS = {"card", "barChart", "lineChart", "tableEx"}


def snapshot(root):
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def visual_doc(root, page_name, visual_name):
    return read_json(
        root / "NorthWind.Report" / "definition" / "pages" / page_name
        / "visuals" / visual_name / "visual.json"
    )


class ReportGenerationTests(unittest.TestCase):
    def test_deterministic_rebuild(self):
        with tempfile.TemporaryDirectory() as a, \
                tempfile.TemporaryDirectory() as b:
            BUILD.build("localhost", "NorthWindOLAP", Path(a))
            BUILD.build("localhost", "NorthWindOLAP", Path(b))
            self.assertEqual(snapshot(Path(a)), snapshot(Path(b)))

    def test_active_page_is_inicio(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BUILD.build("localhost", "NorthWindOLAP", root)
            doc = read_json(
                root / "NorthWind.Report" / "definition" / "pages"
                / "pages.json")
            self.assertEqual(doc["activePageName"], "inicio")
            self.assertEqual(doc["pageOrder"],
                             ["inicio", "panorama", "productos",
                              "clientes", "logistica"])

    def test_button_visual_link_and_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BUILD.build("localhost", "NorthWindOLAP", root)
            for page in PAGES:
                for entry in page["visuals"]:
                    if entry["visual"]["visualType"] != "actionButton":
                        continue
                    doc = visual_doc(root, page["name"], entry["name"])
                    link = doc["visual"]["visualContainerObjects"][
                        "visualLink"][0]["properties"]
                    self.assertEqual(
                        link["show"]["expr"]["Literal"]["Value"], "true")
                    self.assertEqual(
                        link["type"]["expr"]["Literal"]["Value"],
                        "'PageNavigation'")
                    self.assertEqual(
                        link["navigationSection"]["expr"]["Literal"]["Value"],
                        f"'{entry['action']['target']}'")
                    text = doc["visual"]["objects"]["text"][1]
                    self.assertEqual(text["selector"], {"id": "default"})
                    self.assertEqual(
                        text["properties"]["text"]["expr"]["Literal"]["Value"],
                        f"'{entry['title']}'")
                    icon = doc["visual"]["objects"]["icon"][1]
                    if "appearance" in entry:
                        color = icon["properties"]["lineColor"]["solid"][
                            "color"]["expr"]["Literal"]["Value"]
                        self.assertEqual(color, "'#FFFFFF'")
                    else:
                        self.assertNotIn("lineColor", icon["properties"])

    def test_text_visuals_render_title_and_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BUILD.build("localhost", "NorthWindOLAP", root)
            for page in PAGES:
                for entry in page["visuals"]:
                    if entry["visual"]["visualType"] != "textbox":
                        continue
                    doc = visual_doc(root, page["name"], entry["name"])
                    paragraphs = doc["visual"]["objects"]["general"][0][
                        "properties"]["paragraphs"]
                    self.assertEqual(paragraphs[0]["textRuns"][0]["value"],
                                     entry["text"]["title"])
                    if entry["text"]["body"]:
                        self.assertEqual(
                            paragraphs[1]["textRuns"][0]["value"],
                            entry["text"]["body"])
                    else:
                        self.assertEqual(len(paragraphs), 1)

    def test_tracked_tree_matches_fresh_build(self):
        tracked = [
            "NorthWind.Report/definition/pages/pages.json",
            "NorthWind.Report/definition/report.json",
            "NorthWind.Report/definition/pages/inicio/page.json",
            "NorthWind.Report/definition/pages/panorama/visuals/"
            "panorama_nav_inicio/visual.json",
            "NorthWind.Report/definition/pages/panorama/visuals/"
            "panorama_trend/visual.json",
            "NorthWind.Report/definition/pages/panorama/visuals/"
            "panorama_filter_0/visual.json",
            "NorthWind.Report/definition/pages/logistica/visuals/"
            "logistica_trend/visual.json",
        ]
        home_dir = ("NorthWind.Report/definition/pages/inicio/visuals")
        tracked += [
            f"{home_dir}/{d.name}/visual.json"
            for d in sorted(
                (REPORTS / home_dir).iterdir()) if d.is_dir()]
        tracked += [
            f"NorthWind.Report/StaticResources/RegisteredResources/"
            f"{p.name}"
            for p in sorted((REPORTS / "NorthWind.Report"
                             / "StaticResources"
                             / "RegisteredResources").glob("*.png"))]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BUILD.build("localhost", "NorthWindOLAP", root)
            for rel in tracked:
                self.assertEqual(
                    (root / rel).read_bytes(),
                    (REPORTS / rel).read_bytes(), rel)

    def test_no_stale_home_visuals_on_disk(self):
        visuals = REPORTS / ("NorthWind.Report/definition/pages/inicio"
                             "/visuals")
        for stale in ("inicio_kpi_0", "inicio_kpi_1", "inicio_kpi_2",
                      "inicio_explora"):
            self.assertFalse((visuals / stale).exists(), stale)
        expected = {v["name"] for v in PAGES[0]["visuals"]}
        expected |= {"inicio_heading", "inicio_footer"}
        self.assertEqual({d.name for d in visuals.iterdir() if d.is_dir()},
                         expected)

    def test_report_json_lives_in_definition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BUILD.build("localhost", "NorthWindOLAP", root)
            self.assertFalse(
                (root / "NorthWind.Report" / "report.json").exists())
            doc = read_json(
                root / "NorthWind.Report" / "definition" / "report.json")
            self.assertTrue(
                doc["$schema"].endswith("/report/2.0.0/schema.json"))

    def test_connection_files_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BUILD.build("db-host", "NorthWindOLAP", root)
            for rel, expected in CONTRACT.connection_files(
                    "db-host", "NorthWindOLAP").items():
                self.assertEqual(read_json(root / rel), expected)

    def test_visual_envelope_preserves_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BUILD.build("localhost", "NorthWindOLAP", root)
            for page in PAGES:
                for entry in page["visuals"]:
                    doc = visual_doc(root, page["name"], entry["name"])
                    self.assertNotIn("visualContainerObjects", doc)
                    self.assertNotIn("visualInteractions", doc)
                    self.assertIn(
                        "visualContainerObjects", doc["visual"])
                    for key in ("visualType", "query",
                                "drillFilterOtherVisuals", "syncGroup"):
                        if key in entry["visual"]:
                            self.assertEqual(
                                doc["visual"][key], entry["visual"][key])
                    if "filterConfig" in entry:
                        self.assertEqual(
                            doc["filterConfig"], entry["filterConfig"])
            doc = visual_doc(root, PAGES[0]["name"],
                             f"{PAGES[0]['name']}_heading")
            paragraphs = doc["visual"]["objects"]["general"][0][
                "properties"]["paragraphs"]
            self.assertEqual(
                paragraphs[0]["textRuns"][0]["value"],
                f"NORTHWIND / {PAGES[0]['title']}")

    def test_page_interactions_reference_known_visuals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BUILD.build("localhost", "NorthWindOLAP", root)
            for page in PAGES:
                doc = read_json(
                    root / "NorthWind.Report" / "definition" / "pages"
                    / page["name"] / "page.json")
                kinds = {v["name"]: v["visual"]["visualType"]
                         for v in page["visuals"]}
                for link in doc["visualInteractions"]:
                    self.assertEqual(link["type"], "DataFilter")
                    self.assertIn(link["source"], kinds)
                    self.assertIn(link["target"], kinds)
                    self.assertIn(kinds[link["source"]], SOURCES)
                    self.assertIn(kinds[link["target"]], TARGETS)
                    self.assertNotEqual(link["source"], link["target"])

    def test_image_resources_packaged_and_referenced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BUILD.build("localhost", "NorthWindOLAP", root)
            static = (root / "NorthWind.Report" / "StaticResources"
                      / "RegisteredResources")
            expected_pngs = {"home_hero.png", "home_sales.png",
                             "home_products.png", "home_customers.png",
                             "home_logistics.png"}
            packaged = {p.name for p in static.glob("*.png")}
            self.assertEqual(packaged, expected_pngs)
            for name in expected_pngs:
                data = (static / name).read_bytes()
                self.assertEqual(
                    data, (REPORTS / "assets" / "home" / name).read_bytes())
                self.assertEqual(data[:8].hex(), "89504e470d0a1a0a")
                width, height = struct.unpack(">II", data[16:24])
                self.assertEqual(
                    (width, height),
                    (2752, 232) if name == "home_hero.png"
                    else (1352, 360), name)
            report = read_json(
                root / "NorthWind.Report" / "definition" / "report.json")
            items = report["resourcePackages"][0]["items"]
            images = [i for i in items if i["type"] == "Image"]
            self.assertEqual(sorted(i["name"] for i in images),
                             sorted(expected_pngs))
            for item in images:
                self.assertEqual(item["path"], item["name"])
            for entry in PAGES[0]["visuals"]:
                if entry["visual"]["visualType"] != "image":
                    continue
                doc = visual_doc(root, "inicio", entry["name"])
                self.assertNotIn("query", doc["visual"])
                url = doc["visual"]["objects"]["general"][0][
                    "properties"]["imageUrl"]["expr"]["ResourcePackageItem"]
                self.assertEqual(url["PackageName"], "RegisteredResources")
                self.assertEqual(url["PackageType"], 1)
                self.assertEqual(url["ItemName"],
                                 entry["image"]["resource"])
                scaling = doc["visual"]["objects"]["imageScaling"][0][
                    "properties"]["imageScalingType"]
                self.assertEqual(scaling["expr"]["Literal"]["Value"],
                                 "'Normal'")
                vco = doc["visual"]["visualContainerObjects"]
                alt = vco["general"][0]["properties"]["altText"]
                self.assertEqual(alt["expr"]["Literal"]["Value"],
                                 f"'{entry['image']['alt']}'")
                if "action" in entry:
                    link = vco["visualLink"][0]["properties"]
                    self.assertEqual(
                        link["navigationSection"]["expr"]
                        ["Literal"]["Value"],
                        f"'{entry['action']['target']}'")
                else:
                    self.assertNotIn("visualLink", vco)

    def test_missing_image_asset_aborts_before_writes(self):
        original = BUILD.pages
        try:
            BUILD.pages = lambda: [{
                "name": "inicio", "title": "Inicio", "width": 1440,
                "height": 810,
                "visuals": [{
                    "name": "inicio_intro", "title": "t",
                    "rect": [0, 0, 10, 10],
                    "image": {"resource": "no_such.png", "alt": "x"},
                    "visual": {"visualType": "image"}}],
            }]
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with self.assertRaises(SystemExit):
                    BUILD.build("localhost", "NorthWindOLAP", root)
                self.assertEqual(list(root.rglob("*")), [])
        finally:
            BUILD.pages = original

    def test_svg_sources_are_self_contained(self):
        for svg in (REPORTS / "assets" / "home").glob("*.svg"):
            tree = ET.parse(svg)
            text = svg.read_text(encoding="utf-8")
            for external in ("<script", "xlink:href", " href=",
                             "url(", "@import", "<image"):
                self.assertNotIn(external, text, svg.name)
            for element in tree.iter():
                tag = element.tag.split("}")[-1]
                self.assertNotIn(tag, {"script", "foreignObject",
                                       "iframe", "image"})

    def test_unexpected_visual_dir_aborts_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stray = (root / "NorthWind.Report" / "definition" / "pages"
                     / "panorama" / "visuals" / "user_visual")
            stray.mkdir(parents=True)
            (stray / "visual.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(SystemExit):
                BUILD.build("localhost", "NorthWindOLAP", root)
            self.assertTrue((stray / "visual.json").exists())
            self.assertFalse(
                (root / "NorthWind.Report" / "definition"
                 / "version.json").exists())

    def test_unexpected_page_dir_aborts_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stray = (root / "NorthWind.Report" / "definition" / "pages"
                     / "user_page")
            stray.mkdir(parents=True)
            (stray / "page.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(SystemExit):
                BUILD.build("localhost", "NorthWindOLAP", root)
            self.assertTrue((stray / "page.json").exists())
            self.assertFalse(
                (root / "NorthWind.Report" / "definition"
                 / "version.json").exists())

    def test_preview_layout_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BUILD.build("localhost", "NorthWindOLAP", root)
            text = (root / "preview-layout.js").read_text(encoding="utf-8")
            self.assertIn("const PAGES = ", text)
            data = json.loads(
                text.split("const PAGES = ", 1)[1].strip().rstrip(";"))
            self.assertEqual([p["name"] for p in data],
                             [p["name"] for p in PAGES])
            for got, page in zip(data, PAGES):
                self.assertEqual(got["title"], page["title"])
                self.assertEqual(
                    [v["name"] for v in got["visuals"]],
                    [v["name"] for v in page["visuals"]])
                for gv, entry in zip(got["visuals"], page["visuals"]):
                    self.assertEqual(gv["title"], entry["title"])
                    self.assertEqual(
                        gv["t"], entry["visual"]["visualType"])
                    self.assertEqual(gv["r"], entry["rect"])
                    self.assertEqual(gv["action"], entry.get("action"))
                    self.assertEqual(gv["text"], entry.get("text"))
                    self.assertEqual(gv["image"], entry.get("image"))
                    self.assertEqual(gv["appearance"],
                                     entry.get("appearance"))
            self.assertEqual(
                data[0]["hr"], PAGES[0].get("heading_rect", [32, 16, 1376, 44]))


if __name__ == "__main__":
    unittest.main()
