"""Offline regression checks; these do not claim to execute DAX in SSAS."""

import importlib.util
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BI = ROOT / "NorthWindBI"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODEL = load_module("build_model", BI / "NorthWindOLAP" / "build_model.py")
REPORT = load_module("report_contract", BI / "NorthWindReports" / "report_contract.py")


class ModelContractTests(unittest.TestCase):
    def setUp(self):
        self.database = MODEL.build_model()
        self.model = self.database["model"]
        self.tables = {t["name"]: t for t in self.model["tables"]}
        self.measures = {
            m["name"]: m for m in self.tables["Ventas"]["measures"]
        }

    def test_committed_model_matches_generator(self):
        path = BI / "NorthWindOLAP" / "NorthWind.bim"
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), self.database)

    def test_seven_tables_and_eight_relationships(self):
        self.assertEqual(set(self.tables), {
            "Ventas", "Calendario", "Clientes", "Productos", "Vendedores",
            "Proveedores", "Transportistas",
        })
        self.assertEqual(len(self.model["relationships"]), 8)

    def test_relationships_are_many_to_one_single_direction(self):
        for relation in self.model["relationships"]:
            self.assertEqual(relation["fromTable"], "Ventas")
            self.assertEqual(relation["fromCardinality"], "many")
            self.assertEqual(relation["toCardinality"], "one")
            self.assertEqual(relation["crossFilteringBehavior"], "oneDirection")
            for side in ("from", "to"):
                columns = {
                    c["name"] for c in self.tables[relation[side + "Table"]]["columns"]
                }
                self.assertIn(relation[side + "Column"], columns)

    def test_only_order_date_is_active(self):
        dates = {
            r["fromColumn"]: r["isActive"]
            for r in self.model["relationships"] if r["toTable"] == "Calendario"
        }
        self.assertEqual(dates, {
            "OrderDateKey": True, "ShippedDateKey": False, "RequiredDateKey": False,
        })
        self.assertIn("USERELATIONSHIP(Ventas[ShippedDateKey], Calendario[DateKey])",
                      self.measures["Ventas por Fecha de Envio"]["expression"])

    def test_cash_uses_fixed_decimal_and_no_invented_currency(self):
        cash = {"GrossAmount", "DiscountAmount", "NetAmount", "AllocatedFreight"}
        columns = {c["name"]: c for c in self.tables["Ventas"]["columns"]}
        for name in cash:
            self.assertEqual(columns[name]["dataType"], "decimal")
            self.assertTrue(columns[name]["isHidden"])
        for measure in self.measures.values():
            self.assertNotIn("$", measure["formatString"])
            self.assertNotIn("EUR", measure["formatString"])

    def test_measures_preserve_fact_grain(self):
        expected = {
            "Ventas Netas": "SUM(Ventas[NetAmount])",
            "Ventas Brutas": "SUM(Ventas[GrossAmount])",
            "Descuentos": "SUM(Ventas[DiscountAmount])",
            "Pedidos": "DISTINCTCOUNT(Ventas[OrderID])",
            "Ticket Promedio": "DIVIDE([Ventas Netas], [Pedidos])",
            "Tasa de Descuento": "DIVIDE([Descuentos], [Ventas Brutas])",
            "Flete Asignado": "SUM(Ventas[AllocatedFreight])",
            "Dias Promedio Hasta Envio":
                "AVERAGEX(VALUES(Ventas[OrderID]), "
                "CALCULATE(MAX(Ventas[DiasHastaEnvio])))",
        }
        for name, expression in expected.items():
            self.assertEqual(self.measures[name]["expression"], expression)
        self.assertNotRegex(MODEL.SOURCES["Ventas"], r"\[Freight\]|\[UnitPrice\]")
        self.assertNotIn("AVG(", MODEL.SOURCES["Ventas"])

    def test_unknown_dates_remain_but_not_as_year_1900(self):
        query = MODEL.SOURCES["Calendario"]
        self.assertIn("CASE WHEN [DateKey] <> -1 THEN [FullDate] END", query)
        self.assertIn("CASE WHEN [DateKey] <> -1 THEN [Year] END", query)
        self.assertNotIn("WHERE", query.upper())
        self.assertIn("f.[OrderDateKey] <> -1 AND f.[ShippedDateKey] <> -1",
                      MODEL.SOURCES["Ventas"])

    def test_geography_joins_are_separate_and_keep_unmatched_dimensions(self):
        for name in ("Clientes", "Vendedores", "Proveedores"):
            self.assertIn("LEFT JOIN [dbo].[DimGeography]", MODEL.SOURCES[name])
        self.assertNotIn("DimGeography", self.tables)

    def test_month_names_and_year_months_sort_chronologically(self):
        columns = {c["name"]: c for c in self.tables["Calendario"]["columns"]}
        self.assertEqual(columns["Mes"]["sortByColumn"], "MesNumero")
        self.assertEqual(columns["MesAnio"]["sortByColumn"], "OrdenMesAnio")
        self.assertIn("[Year] * 100 + [MonthOfYear]", MODEL.SOURCES["Calendario"])

    def test_queries_are_read_only_and_reference_existing_dw_tables(self):
        for query in MODEL.SOURCES.values():
            self.assertTrue(query.strip().upper().startswith("SELECT"))
            self.assertNotRegex(query.upper(), r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE)\b")
            for name in re.findall(r"\[dbo\]\.\[(\w+)\]", query):
                self.assertTrue((BI / "NorthWindDW/Schema/Tables" / f"{name}.sql").exists())

    def test_authentication_contains_no_credentials(self):
        source = self.model["dataSources"][0]
        self.assertIn("Integrated Security=SSPI", source["connectionString"])
        self.assertEqual(source["impersonationMode"], "impersonateServiceAccount")
        self.assertNotRegex(json.dumps(self.database).lower(),
                            r"password|user id=|username")

    def test_perspective_contains_all_measures_but_not_technical_columns(self):
        perspective = self.model["perspectives"][0]
        for table in perspective["tables"]:
            columns = {c["name"]: c for c in self.tables[table["name"]]["columns"]}
            for column in table.get("columns", []):
                self.assertFalse(columns[column["name"]].get("isHidden", False))
        sales = next(t for t in perspective["tables"] if t["name"] == "Ventas")
        self.assertEqual({m["name"] for m in sales["measures"]}, set(self.measures))


class ReportContractTests(unittest.TestCase):
    def setUp(self):
        self.pages = REPORT.pages()
        self.tables = {t["name"]: t for t in MODEL.build_model()["model"]["tables"]}

    def test_four_pages_in_expected_order(self):
        self.assertEqual([p["name"] for p in self.pages],
                         ["panorama", "productos", "clientes", "logistica"])

    def test_every_projection_binds_to_existing_model_field(self):
        for page in self.pages:
            for visual in page["visuals"]:
                query = visual["visual"]["query"]
                for role in query["queryState"].values():
                    for projection in role["projections"]:
                        kind, reference = next(iter(projection["field"].items()))
                        table = reference["Expression"]["SourceRef"]["Entity"]
                        collection = "measures" if kind == "Measure" else "columns"
                        names = {x["name"] for x in self.tables[table][collection]}
                        self.assertIn(reference["Property"], names)

    def test_visuals_fit_and_do_not_overlap(self):
        for page in self.pages:
            names = [v["name"] for v in page["visuals"]]
            self.assertEqual(len(names), len(set(names)))
            for i, visual in enumerate(page["visuals"]):
                x, y, width, height = visual["rect"]
                self.assertGreaterEqual(min(x, y), 0)
                self.assertLessEqual(x + width, page["width"])
                self.assertLessEqual(y + height, page["height"])
                for other in page["visuals"][i + 1:]:
                    ox, oy, ow, oh = other["rect"]
                    self.assertFalse(x < ox + ow and ox < x + width
                                     and y < oy + oh and oy < y + height)

    def test_top_n_has_deterministic_measure_then_label_order(self):
        for page in self.pages:
            for visual in page["visuals"]:
                for config in visual.get("filterConfig", {}).get("filters", []):
                    subquery = config["filter"]["From"][1]["Expression"]["Subquery"]["Query"]
                    self.assertIn(subquery["Top"], (5, 10))
                    self.assertEqual(subquery["OrderBy"][0]["Direction"], 2)
                    self.assertEqual(subquery["OrderBy"][1]["Direction"], 1)
                    self.assertIn("Measure", subquery["OrderBy"][0]["Expression"])

    def test_shipping_chart_does_not_mix_order_date_tooltips(self):
        page = next(p for p in self.pages if p["name"] == "logistica")
        chart = next(v for v in page["visuals"] if v["name"] == "logistica_trend")
        state = chart["visual"]["query"]["queryState"]
        self.assertNotIn("Tooltips", state)
        self.assertEqual(state["Y"]["projections"][0]["nativeQueryRef"],
                         "Ventas por Fecha de Envio")

    def test_ssas_live_connection_is_not_a_fabric_connection(self):
        files = REPORT.connection_files()
        definition = files["NorthWind.Report/definition.pbir"]
        self.assertEqual(definition["datasetReference"],
                         {"byPath": {"path": "../NorthWind.SemanticModel"}})
        reference = files["NorthWind.SemanticModel/modelReference.json"]
        self.assertEqual(reference["connectionType"],
                         "analysisServicesDatabaseLive")
        self.assertFalse(reference["isMultiDimentional"])
        self.assertIn("Initial Catalog=NorthWindOLAP", reference["connectionString"])

    def test_drillthrough_pages_keep_context(self):
        for name in ("productos", "clientes"):
            page = next(p for p in self.pages if p["name"] == name)
            self.assertEqual(page["pageBinding"]["type"], "Drillthrough")
            self.assertEqual(page["pageBinding"]["acceptsFilterContext"], "Default")
            self.assertEqual(
                page["pageBinding"]["parameters"][0]["boundFilter"],
                page["filterConfig"]["filters"][0]["name"],
            )


if __name__ == "__main__":
    unittest.main()
