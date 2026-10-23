"""Mechanics of the optional schema validator; no network, no third-party."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = (
    ROOT / "NorthWindBI" / "NorthWindReports" / "validate_report_schemas.py"
)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VAL = load_module("validate_report_schemas", VALIDATOR)


class SchemaUrlTests(unittest.TestCase):
    def test_canonical_uri_maps_to_raw_github(self):
        uri = (
            "https://developer.microsoft.com/json-schemas/"
            "fabric/item/report/definition/report/2.0.0/schema.json"
        )
        self.assertEqual(
            VAL.schema_url(uri),
            "https://raw.githubusercontent.com/microsoft/json-schemas/"
            "main/fabric/item/report/definition/report/2.0.0/schema.json",
        )

    def test_embedded_typo_remapped(self):
        uri = (
            "https://developer.microsoft.com/json-schemas/"
            "x/1.0.0/schema.embedded.json"
        )
        self.assertTrue(
            VAL.schema_url(uri).endswith("/schema-embedded.json"))

    def test_rejects_non_microsoft_host(self):
        with self.assertRaises(ValueError):
            VAL.schema_url("https://example.com/schema.json")
        with self.assertRaises(ValueError):
            VAL.schema_url("https://developer.microsoft.com.evil/x")


class CollectInstancesTests(unittest.TestCase):
    def test_collects_valid_and_flags_bad(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ok.json").write_text(
                json.dumps({"$schema": VAL.PREFIX + "s/1.0.0/schema.json"}),
                encoding="utf-8")
            (root / "theme.json").write_text(  # no $schema: skipped, fine
                json.dumps({"name": "NorthWind"}), encoding="utf-8")
            (root / "broken.json").write_text("{not json", encoding="utf-8")
            (root / "alien.pbip").write_text(
                json.dumps({"$schema": "https://evil.example/x"}),
                encoding="utf-8")
            instances, problems = VAL.collect_instances(root)
            self.assertEqual([p.name for p, _, _ in instances], ["ok.json"])
            self.assertEqual({p.name for p, _ in problems},
                             {"broken.json", "alien.pbip"})

    def test_missing_report_root_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                VAL.main(["--report-root", str(Path(tmp) / "missing")])


if __name__ == "__main__":
    unittest.main()
