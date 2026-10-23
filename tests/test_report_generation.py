"""Generator mechanics only; contract semantics are not re-verified here."""

import importlib.util
import json
import sys
import tempfile
import unittest
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
SOURCES = {
    "slicer", "barChart", "clusteredBarChart", "columnChart",
    "clusteredColumnChart", "lineChart", "lineClusteredColumnComboChart",
    "tableEx", "pivotTable", "scatterChart", "azureMap",
}
TARGETS = (SOURCES - {"slicer"}) | {"card"}


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
        self.assertEqual(BUILD.FILTERING_SOURCES, SOURCES)
        self.assertEqual(BUILD.FILTERING_TARGETS, TARGETS)
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

    def test_unexpected_visual_dir_aborts_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stray = (root / "NorthWind.Report" / "definition" / "pages"
                     / "resumen" / "visuals" / "user_visual")
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
                    self.assertEqual(gv.get("h", False),
                                     bool(entry.get("hidden")))

    def test_bookmarks_written_with_matching_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BUILD.build("localhost", "NorthWindOLAP", root)
            expected = CONTRACT.bookmarks()
            bookmarks_dir = (root / "NorthWind.Report" / "definition"
                             / "bookmarks")
            index = read_json(bookmarks_dir / "bookmarks.json")
            self.assertTrue(index["$schema"].endswith(
                "/bookmarksMetadata/1.0.0/schema.json"))
            indexed = [child for item in index["items"]
                       for child in item["children"]]
            self.assertEqual(sorted(indexed), sorted(expected["files"]))
            for name, payload in expected["files"].items():
                doc = read_json(bookmarks_dir / f"{name}.bookmark.json")
                self.assertEqual(doc["name"], name)
                self.assertTrue(doc["$schema"].endswith(
                    "/bookmark/2.1.0/schema.json"))
                self.assertEqual(doc["options"], payload["options"])
                self.assertEqual(doc["explorationState"],
                                 payload["explorationState"])

    def test_action_button_renders_visual_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BUILD.build("localhost", "NorthWindOLAP", root)
            doc = visual_doc(root, "resumen", "resumen_nav_producto")
            self.assertEqual(doc["visual"]["visualType"], "actionButton")
            self.assertIn("objects", doc["visual"])
            link = doc["visual"]["visualContainerObjects"]["visualLink"][
                0]["properties"]
            self.assertEqual(link["type"]["expr"]["Literal"]["Value"],
                             "'PageNavigation'")
            self.assertEqual(
                link["navigationSection"]["expr"]["Literal"]["Value"],
                "'producto'")
            back = visual_doc(root, "transacciones", "transacciones_back")
            props = back["visual"]["visualContainerObjects"]["visualLink"][
                0]["properties"]
            self.assertEqual(props["type"]["expr"]["Literal"]["Value"],
                             "'Back'")
            self.assertNotIn("navigationSection", props)

    def test_hidden_visual_and_hidden_page_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BUILD.build("localhost", "NorthWindOLAP", root)
            doc = visual_doc(root, "resumen", "resumen_trend_orders")
            self.assertTrue(doc["isHidden"])
            self.assertNotIn(
                "isHidden", visual_doc(root, "resumen", "resumen_trend"))
            page = read_json(root / "NorthWind.Report" / "definition"
                             / "pages" / "transacciones" / "page.json")
            self.assertEqual(page["visibility"], "HiddenInViewMode")
            resumen = read_json(root / "NorthWind.Report" / "definition"
                                / "pages" / "resumen" / "page.json")
            self.assertNotIn("visibility", resumen)

    def test_story_textbox_carries_page_story(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            BUILD.build("localhost", "NorthWindOLAP", root)
            for page in PAGES:
                doc = visual_doc(
                    root, page["name"], f"{page['name']}_story")
                value = doc["visual"]["objects"]["general"][0][
                    "properties"]["paragraphs"][0]["textRuns"][0]["value"]
                self.assertEqual(value,
                                 page["story"] + BUILD.STORY_SUFFIX)


if __name__ == "__main__":
    unittest.main()
