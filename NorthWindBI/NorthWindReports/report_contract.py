"""Lead-authored field bindings and query semantics for the PBIR report."""

import copy


SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/"
DEFAULT_MEASURES = [
    "Ventas Netas", "Pedidos", "Ticket Promedio", "Unidades Vendidas", "Descuentos",
]


def field(table, name, measure=False, alias=None):
    source = {"Source": alias} if alias else {"Entity": table}
    return {
        "Measure" if measure else "Column": {
            "Expression": {"SourceRef": source}, "Property": name,
        }
    }


def projection(table, name, measure=False):
    return {
        "field": field(table, name, measure),
        "queryRef": f"{table}.{name}", "nativeQueryRef": name,
    }


def top_filter(table, name, measure, count):
    # A semijoin to an ordered subquery makes Top N follow the current context,
    # with label as a deterministic tie-breaker rather than a global DAX rank.
    dimension = field(table, name, alias="d")
    value = field("Ventas", measure, measure=True, alias="v")
    return {
        "filters": [{
            "name": f"top_{table}_{name}".replace(" ", "_"),
            "field": field(table, name), "type": "TopN",
            "filter": {
                "Version": 2,
                "From": [
                    {"Name": "d", "Entity": table, "Type": 0},
                    {"Name": "top", "Type": 2, "Expression": {
                        "Subquery": {"Query": {
                            "Version": 2,
                            "From": [
                                {"Name": "d", "Entity": table, "Type": 0},
                                {"Name": "v", "Entity": "Ventas", "Type": 0},
                            ],
                            "Select": [dimension],
                            "OrderBy": [
                                {"Direction": 2, "Expression": value},
                                {"Direction": 1, "Expression": dimension},
                            ],
                            "Top": count,
                        }},
                    }},
                ],
                "Where": [{"Condition": {"In": {
                    "Expressions": [dimension],
                    "Table": {"SourceRef": {"Source": "top"}},
                }}}],
            },
        }],
    }


def chart(name, title, kind, rect, group=None, measures=(), top=None):
    state = {}
    if group:
        state["Category"] = {"projections": [projection(*group)]}
    if measures:
        role = "Values" if kind == "tableEx" else "Data" if kind == "card" else "Y"
        state[role] = {
            "projections": [projection("Ventas", m, True) for m in measures]
        }
    if kind == "tableEx" and group:
        state["Values"]["projections"].insert(0, projection(*group))
        del state["Category"]
    if kind == "slicer":
        state = {"Values": {"projections": [projection(*group)]}}
    visual = {
        "visualType": kind, "query": {"queryState": state},
        "drillFilterOtherVisuals": True,
    }
    if group:
        time_axis = group[0] == "Calendario"
        visual["query"]["sortDefinition"] = {
            "sort": [{
                "field": field(*group) if time_axis or not measures
                else field("Ventas", measures[0], True),
                "direction": "Ascending" if time_axis or not measures
                else "Descending",
            }],
            "isDefaultSort": False,
        }
    if kind in ("barChart", "lineChart") and measures != ["Ventas por Fecha de Envio"]:
        visual["query"]["queryState"]["Tooltips"] = {
            "projections": [
                projection("Ventas", m, True)
                for m in ("Ventas Netas", "Unidades Vendidas", "Pedidos")
                if m not in measures
            ]
        }
    if kind == "slicer":
        visual["syncGroup"] = {
            "groupName": f"{group[0]}_{group[1]}",
            "fieldChanges": True, "filterChanges": True,
        }
    result = {
        "name": name, "title": title, "rect": rect, "visual": visual,
    }
    if top:
        result["filterConfig"] = top_filter(*group, measures[0], top)
    return result


def make_page(name, title, filters, cards, charts, drillthrough=None):
    visuals = []
    for i, (label, table, column) in enumerate(filters):
        visuals.append(chart(
            f"{name}_filter_{i}", label, "slicer",
            [32 + i * 348, 76, 332, 62], (table, column),
        ))
    for i, measure in enumerate(cards):
        visuals.append(chart(
            f"{name}_kpi_{i}", measure, "card",
            [32 + i * 278, 154, 264, 100], measures=[measure],
        ))
    visuals.extend(charts)
    result = {
        "name": name, "title": title, "width": 1440, "height": 810,
        "visuals": visuals,
    }
    if drillthrough:
        table, column = drillthrough
        filter_name = f"{name}_drill"
        result["pageBinding"] = {
            "name": f"{name}_binding", "type": "Drillthrough",
            "acceptsFilterContext": "Default",
            "parameters": [{
                "name": filter_name, "boundFilter": filter_name,
                "fieldExpr": field(table, column),
            }],
        }
        result["filterConfig"] = {"filters": [{
            "name": filter_name, "field": field(table, column),
            "type": "Categorical", "howCreated": "Drillthrough",
        }]}
        result["type"] = "Drillthrough"
    return result


def pages():
    period = ("Periodo (mes-anio)", "Calendario", "MesAnio")
    country = ("Pais del cliente", "Clientes", "Pais")
    category = ("Categoria", "Productos", "Categoria")
    seller = ("Vendedor", "Vendedores", "Vendedor")
    net = ["Ventas Netas"]
    return copy.deepcopy([
        make_page("panorama", "Panorama de ventas",
                  [period, country, category, seller], DEFAULT_MEASURES, [
            chart("panorama_trend", "Evolucion de ventas netas", "lineChart",
                  [32, 270, 840, 246], ("Calendario", "MesAnio"), net),
            chart("panorama_categories", "Ventas por categoria", "barChart",
                  [888, 270, 520, 246], ("Productos", "Categoria"), net),
            chart("panorama_clients", "Top 5 clientes por ventas netas", "barChart",
                  [32, 532, 440, 246], ("Clientes", "Cliente"), net, top=5),
            chart("panorama_products", "Top 5 productos por ventas netas",
                  "barChart", [488, 532, 440, 246],
                  ("Productos", "Producto"), net, top=5),
            chart("panorama_countries", "Resultados por pais del cliente",
                  "tableEx", [944, 532, 464, 246],
                  ("Clientes", "Pais"), ["Ventas Netas", "Pedidos",
                                        "Ticket Promedio"]),
        ]),
        make_page("productos", "Productos y categorias", [
            period, country, category, ("Producto", "Productos", "Producto"),
        ], ["Ventas Netas", "Unidades Vendidas", "Ventas Brutas", "Descuentos",
            "Tasa de Descuento"], [
            chart("productos_trend", "Evolucion de ventas netas", "lineChart",
                  [32, 270, 840, 246], ("Calendario", "MesAnio"), net),
            chart("productos_categories", "Unidades por categoria", "barChart",
                  [888, 270, 520, 246], ("Productos", "Categoria"),
                  ["Unidades Vendidas"]),
            chart("productos_detail", "Detalle por producto", "tableEx",
                  [32, 532, 840, 246], ("Productos", "Producto"),
                  ["Ventas Netas", "Unidades Vendidas", "Descuentos",
                   "Tasa de Descuento"]),
            chart("productos_suppliers", "Top 5 proveedores por ventas netas",
                  "barChart", [888, 532, 520, 246],
                  ("Proveedores", "Proveedor"), net, top=5),
        ], drillthrough=("Productos", "Producto")),
        make_page("clientes", "Clientes y vendedores", [
            period, country, ("Cliente", "Clientes", "Cliente"), seller,
        ], DEFAULT_MEASURES, [
            chart("clientes_ranking", "Top 10 clientes por ventas netas",
                  "barChart", [32, 270, 840, 246],
                  ("Clientes", "Cliente"), net, top=10),
            chart("clientes_sellers", "Ventas por vendedor", "barChart",
                  [888, 270, 520, 246], ("Vendedores", "Vendedor"), net),
            chart("clientes_detail", "Resultados por cliente", "tableEx",
                  [32, 532, 840, 246], ("Clientes", "Cliente"),
                  ["Ventas Netas", "Pedidos", "Ticket Promedio",
                   "Unidades Vendidas"]),
            chart("clientes_countries", "Ventas por pais del cliente", "barChart",
                  [888, 532, 520, 246], ("Clientes", "Pais"), net),
        ], drillthrough=("Clientes", "Cliente")),
        make_page("logistica", "Logistica: pedido a envio", [
            period, country, category,
            ("Transportista", "Transportistas", "Transportista"),
        ], ["Flete Asignado", "Pedidos Enviados", "Dias Promedio Hasta Envio",
            "Pedidos", "Ventas Netas"], [
            chart("logistica_days", "Dias entre pedido y envio", "barChart",
                  [32, 270, 840, 246], ("Transportistas", "Transportista"),
                  ["Dias Promedio Hasta Envio"]),
            chart("logistica_freight", "Flete asignado por transportista",
                  "barChart", [888, 270, 520, 246],
                  ("Transportistas", "Transportista"), ["Flete Asignado"]),
            chart("logistica_trend", "Ventas netas por fecha de envio",
                  "lineChart", [32, 532, 840, 246],
                  ("Calendario", "MesAnio"), ["Ventas por Fecha de Envio"]),
            chart("logistica_detail", "Resumen por transportista", "tableEx",
                  [888, 532, 520, 246], ("Transportistas", "Transportista"),
                  ["Pedidos Enviados", "Flete Asignado",
                   "Dias Promedio Hasta Envio"]),
        ]),
    ])


def connection_files(server="localhost", database="NorthWindOLAP"):
    """SSAS references must use modelReference, not Fabric-only byConnection."""
    return {
        "NorthWind.pbip": {
            "$schema": (
                "https://developer.microsoft.com/json-schemas/"
                "fabric/pbip/pbipProperties/1.0.0/schema.json"
            ),
            "version": "1.0",
            "artifacts": [{"report": {"path": "NorthWind.Report"}}],
            "settings": {"enableAutoRecovery": True},
        },
        "NorthWind.Report/definition.pbir": {
            "$schema": SCHEMA + "report/definitionProperties/2.0.0/schema.json",
            "version": "4.0",
            "datasetReference": {"byPath": {"path": "../NorthWind.SemanticModel"}},
        },
        "NorthWind.SemanticModel/definition.pbism": {
            "$schema": SCHEMA + "semanticModel/definitionProperties/1.0.0/schema.json",
            "version": "1.0", "settings": {"qnaEnabled": False},
        },
        "NorthWind.SemanticModel/modelReference.json": {
            "$schema": SCHEMA + "semanticModel/modelReference/2.0.0/schema.json",
            "connectionString": (
                f"Data Source={server};Initial Catalog={database};"
                "Cube=Model;Integrated Security=SSPI"
            ),
            "connectionType": "analysisServicesDatabaseLive",
            "isMultiDimentional": False,
        },
    }
