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

    def test_new_measures_have_exact_expressions(self):
        expected = {
            "Clientes Activos": "DISTINCTCOUNT(Ventas[CustomerKey])",
            "Precio Promedio":
                "DIVIDE([Ventas Brutas], [Unidades Vendidas])",
            "Ventas Año Anterior":
                "VAR UltimaVenta = CALCULATE(MAX(Ventas[OrderDateKey]), "
                "REMOVEFILTERS())\n"
                "RETURN\n"
                "    IF(HASONEVALUE(Calendario[MesAño]) && "
                "MIN(Calendario[DateKey]) <= UltimaVenta,\n"
                "        VAR FechasPrevias =\n"
                "            SELECTCOLUMNS(\n"
                "                FILTER(VALUES(Calendario[Fecha]), "
                "NOT ISBLANK(Calendario[Fecha])),\n"
                '                "Fecha", EDATE(Calendario[Fecha], -12))\n'
                "        RETURN\n"
                "            CALCULATE([Ventas Netas], "
                "REMOVEFILTERS(Calendario),\n"
                "                      TREATAS(FechasPrevias, "
                "Calendario[Fecha])))",
            "Crecimiento Interanual":
                "DIVIDE([Ventas Netas] - [Ventas Año Anterior], "
                "[Ventas Año Anterior])",
        }
        for name, expression in expected.items():
            self.assertEqual(self.measures[name]["expression"], expression)

    def test_pedido_and_discount_band_columns(self):
        columns = {c["name"]: c for c in self.tables["Ventas"]["columns"]}
        self.assertFalse(columns["Pedido"].get("isHidden", False))
        self.assertEqual(columns["Pedido"]["dataType"], "int64")
        self.assertEqual(columns["Pedido"]["formatString"], "0")
        self.assertEqual(columns["Pedido"]["sourceColumn"], "Pedido")
        query = MODEL.SOURCES["Ventas"]
        self.assertIn("f.[OrderID] AS [Pedido]", query)
        self.assertIn("CROSS APPLY", query)
        self.assertIn("N'Sin descuento'", query)
        self.assertIn("N'Más de 20%'", query)
        self.assertEqual(columns["Nivel de Descuento"]["sortByColumn"],
                         "OrdenDescuento")
        self.assertTrue(columns["OrdenDescuento"]["isHidden"])
        self.assertEqual(columns["OrdenDescuento"]["dataType"], "int64")

    def test_geography_columns_have_data_categories(self):
        for name in ("Clientes", "Vendedores", "Proveedores"):
            columns = {c["name"]: c for c in self.tables[name]["columns"]}
            self.assertEqual(columns["Pais"]["dataCategory"], "Country")
            self.assertEqual(columns["Region"]["dataCategory"],
                             "StateOrProvince")
            self.assertEqual(columns["Ciudad"]["dataCategory"], "City")

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
        self.assertEqual(columns["MesAño"]["sortByColumn"], "OrdenMesAño")
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


VISIBLE = ["resumen", "producto", "geografico", "detalle", "logistica"]
PAGE_ORDER = VISIBLE + ["transacciones"]


class ReportContractTests(unittest.TestCase):
    def setUp(self):
        self.pages = REPORT.pages()
        self.by_name = {p["name"]: p for p in self.pages}
        self.tables = {t["name"]: t for t in MODEL.build_model()["model"]["tables"]}
        self.bookmarks = REPORT.bookmarks()

    def test_six_pages_in_expected_order(self):
        self.assertEqual([p["name"] for p in self.pages], PAGE_ORDER)

    def test_every_projection_binds_to_existing_model_field(self):
        for page in self.pages:
            for visual in page["visuals"]:
                query = visual["visual"].get("query")
                if not query:
                    continue
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
                    if visual.get("swap_group") and \
                            visual.get("swap_group") == other.get("swap_group"):
                        continue
                    ox, oy, ow, oh = other["rect"]
                    self.assertFalse(x < ox + ow and ox < x + width
                                     and y < oy + oh and oy < y + height)

    def test_hidden_visuals_share_rect_with_visible_swap_partner(self):
        for page in self.pages:
            for visual in page["visuals"]:
                if not visual.get("hidden"):
                    continue
                partners = [v for v in page["visuals"]
                            if v is not visual
                            and not v.get("hidden")
                            and v.get("swap_group") == visual["swap_group"]
                            and v["rect"] == visual["rect"]]
                self.assertTrue(partners, f"{visual['name']} has no partner")

    def test_top_n_has_deterministic_measure_then_label_order(self):
        for page in self.pages:
            for visual in page["visuals"]:
                for config in visual.get("filterConfig", {}).get("filters", []):
                    subquery = config["filter"]["From"][1]["Expression"]["Subquery"]["Query"]
                    self.assertIn(subquery["Top"], (5, 10))
                    self.assertEqual(subquery["OrderBy"][0]["Direction"], 2)
                    self.assertEqual(subquery["OrderBy"][1]["Direction"], 1)
                    self.assertIn("Measure", subquery["OrderBy"][0]["Expression"])
                    alias = subquery["OrderBy"][0]["Expression"]["Measure"][
                        "Expression"]["SourceRef"]["Source"]
                    entities = {s["Name"]: s["Entity"]
                                for s in subquery["From"] if "Entity" in s}
                    self.assertEqual(entities[alias], "Ventas")

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
        self.assertEqual(
            {p["name"] for p in self.pages
             if p.get("type") == "Drillthrough"},
            {"producto", "transacciones"})
        for name in ("producto", "transacciones"):
            page = self.by_name[name]
            self.assertEqual(page["pageBinding"]["type"], "Drillthrough")
            self.assertEqual(page["pageBinding"]["acceptsFilterContext"], "Default")
            self.assertEqual(
                page["pageBinding"]["parameters"][0]["boundFilter"],
                page["filterConfig"]["filters"][0]["name"],
            )
        self.assertEqual(self.by_name["transacciones"].get("visibility"),
                         "HiddenInViewMode")

    def _actions(self, page):
        return [
            (v["name"], v["action"]["type"], v["action"].get("target"))
            for v in page["visuals"] if "action" in v
        ]

    def test_every_visible_page_navigates_to_all_five(self):
        for name in VISIBLE:
            targets = {target for _, kind, target in
                       self._actions(self.by_name[name])
                       if kind == "PageNavigation"}
            self.assertEqual(targets, set(VISIBLE), name)
        self.assertFalse([a for a in self._actions(self.by_name["transacciones"])
                          if a[1] == "PageNavigation"])

    def test_action_targets_are_valid(self):
        for page in self.pages:
            for _, kind, target in self._actions(page):
                if kind == "PageNavigation":
                    self.assertIn(target, VISIBLE)
                elif kind == "Drillthrough":
                    self.assertEqual(
                        self.by_name[target].get("type"), "Drillthrough")
                elif kind == "Bookmark":
                    self.assertIn(target, self.bookmarks["files"])
        backs = [page["name"] for page in self.pages
                 for _, kind, _ in self._actions(page) if kind == "Back"]
        self.assertEqual(backs, ["transacciones"])

    def test_story_buttons_follow_page_order(self):
        for i, name in enumerate(VISIBLE):
            actions = {n: t for n, kind, t in self._actions(self.by_name[name])
                       if n.endswith(("_prev", "_next"))}
            if i == 0:
                self.assertNotIn(f"{name}_prev", actions)
            else:
                self.assertEqual(actions[f"{name}_prev"],
                                 REPORT.STORY_BOOKMARKS[i - 1])
            if i == len(VISIBLE) - 1:
                self.assertNotIn(f"{name}_next", actions)
            else:
                self.assertEqual(actions[f"{name}_next"],
                                 REPORT.STORY_BOOKMARKS[i + 1])

    def test_bookmark_names_are_unique_and_indexed_once(self):
        files = self.bookmarks["files"]
        self.assertEqual(len(files), len(set(files)))
        indexed = [child for item in self.bookmarks["items"]
                   for child in item["children"]]
        self.assertEqual(sorted(indexed), sorted(files))
        self.assertEqual({item["name"] for item in self.bookmarks["items"]},
                         {"recorrido", "vista_tendencia"})

    def test_bookmark_state_references_existing_visuals(self):
        page_visuals = {p["name"]: {v["name"] for v in p["visuals"]}
                        for p in self.pages}
        for name, doc in self.bookmarks["files"].items():
            self.assertEqual(doc["name"], name)
            state = doc["explorationState"]
            self.assertIn(state["activeSection"], page_visuals)
            for section, body in state["sections"].items():
                self.assertIn(section, page_visuals)
                for visual in body.get("visualContainers", {}):
                    self.assertIn(visual, page_visuals[section])
            for target in doc["options"]["targetVisualNames"]:
                self.assertIn(target, page_visuals[state["activeSection"]])

    def test_story_suppress_data_and_toggles_invert(self):
        for name in REPORT.STORY_BOOKMARKS:
            options = self.bookmarks["files"][name]["options"]
            self.assertTrue(options["suppressData"])
            self.assertEqual(options["targetVisualNames"], [])
        ventas = self.bookmarks["files"]["vista_ventas"]
        pedidos = self.bookmarks["files"]["vista_pedidos"]
        self.assertEqual(ventas["options"]["targetVisualNames"],
                         pedidos["options"]["targetVisualNames"])
        a = ventas["explorationState"]["sections"]["resumen"][
            "visualContainers"]
        b = pedidos["explorationState"]["sections"]["resumen"][
            "visualContainers"]

        def hidden(containers, name):
            return containers[name]["singleVisual"].get(
                "display", {}).get("mode") == "hidden"

        for visual in ("resumen_trend", "resumen_trend_orders"):
            self.assertNotEqual(hidden(a, visual), hidden(b, visual))
        self.assertFalse(hidden(a, "resumen_trend"))
        self.assertTrue(hidden(a, "resumen_trend_orders"))


if __name__ == "__main__":
    unittest.main()
