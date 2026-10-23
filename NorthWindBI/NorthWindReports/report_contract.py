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


def text(name, title, body, rect, panel=False, strong=True):
    """Narrative textbox; non-data visual, intentionally without a query."""
    return {
        "name": name, "title": title, "rect": rect,
        "text": {"title": title, "body": body, "panel": panel,
                 "strong": strong},
        "visual": {"visualType": "textbox"},
    }


def button(name, title, rect, target, appearance=None, tooltip=None):
    """Native page-navigation action button; no query by design."""
    entry = {
        "name": name, "title": title, "rect": rect,
        "action": {"type": "PageNavigation", "target": target},
        "visual": {"visualType": "actionButton"},
    }
    if appearance:
        entry["appearance"] = appearance
    if tooltip:
        entry["tooltip"] = tooltip
    return entry


def image(name, title, rect, resource, alt, target=None):
    """Native image visual over a packaged RegisteredResources PNG."""
    entry = {
        "name": name, "title": title, "rect": rect,
        "image": {"resource": resource, "alt": alt},
        "visual": {"visualType": "image"},
    }
    if target:
        entry["action"] = {"type": "PageNavigation", "target": target}
    return entry


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


def home_page():
    # Illustrated navigation menu: packaged PNG scenes, no data visuals.
    routes = [
        ("panorama", "Ventas", "home_sales.png", "#118DFF", "#0B6FD0",
         "Abrir resumen de ventas",
         "Ilustración de ventas: columnas ascendentes, línea de "
         "tendencia y lupa"),
        ("productos", "Productos", "home_products.png", "#C77810",
         "#9A5B0A", "Abrir productos y categorías",
         "Ilustración de productos: cajas apiladas y etiqueta de precio"),
        ("clientes", "Clientes", "home_customers.png", "#087F75",
         "#065F58", "Abrir clientes y vendedores",
         "Ilustración de clientes: tres personas conversando"),
        ("logistica", "Logística", "home_logistics.png", "#3656A3",
         "#26417C", "Abrir logística y envíos",
         "Ilustración de logística: furgoneta, paquete y ruta punteada"),
    ]
    visuals = [
        image("inicio_intro", "Un negocio. Cuatro formas de explorarlo.",
              [32, 80, 1376, 116], "home_hero.png",
              "Portada del menú: un negocio, cuatro formas de "
              "explorarlo; elige una sección y descubre qué cuenta"),
    ]
    for i, (target, label, resource, accent, hover, tip, alt) \
            in enumerate(routes):
        col, row = i % 2, i // 2
        x, y = 32 + col * 700, 220 + row * 268
        visuals.append(image(f"inicio_route_{target}",
                             f"0{i + 1} / {label}", [x, y, 676, 180],
                             resource, alt, target))
        visuals.append(button(f"inicio_open_{target}",
                              f"0{i + 1} / {label}",
                              [x, y + 180, 676, 60], target,
                              appearance={"accent": accent,
                                          "hover": hover},
                              tooltip=tip))
    visuals.append(text(
        "inicio_ayuda",
        "Power BI Desktop: Ctrl + clic para explorar. Vuelve con el "
        "botón Inicio.", None, [32, 744, 1376, 28], strong=False))
    return {
        "name": "inicio", "title": "Inicio",
        "width": 1440, "height": 810, "visuals": visuals,
    }


def pages():
    period = ("Período (Mes/Año)", "Calendario", "MesAño")
    country = ("País", "Clientes", "Pais")
    category = ("Categoría", "Productos", "Categoria")
    seller = ("Vendedor", "Vendedores", "Vendedor")
    net = ["Ventas Netas"]
    built = [
        make_page("panorama", "Dashboard de Ventas",
                  [period, country, category, seller], DEFAULT_MEASURES, [
            chart("panorama_trend", "Tendencia Mensual de Ventas", "lineChart",
                  [32, 270, 840, 246], ("Calendario", "MesAño"), net),
            chart("panorama_categories", "Ventas por Categoría", "barChart",
                  [888, 270, 520, 246], ("Productos", "Categoria"), net),
            chart("panorama_clients", "Top 5 Clientes", "barChart",
                  [32, 532, 440, 246], ("Clientes", "Cliente"), net, top=5),
            chart("panorama_products", "Top 5 Productos más Vendidos",
                  "barChart", [488, 532, 440, 246],
                  ("Productos", "Producto"), net, top=5),
            chart("panorama_countries", "Ventas y Pedidos por País",
                  "tableEx", [944, 532, 464, 246],
                  ("Clientes", "Pais"), ["Ventas Netas", "Pedidos",
                                        "Ticket Promedio"]),
        ]),
        make_page("productos", "Productos y Categorías", [
            period, country, category, ("Producto", "Productos", "Producto"),
        ], ["Ventas Netas", "Unidades Vendidas", "Ventas Brutas", "Descuentos",
            "Tasa de Descuento"], [
            chart("productos_trend", "Tendencia Mensual de Ventas", "lineChart",
                  [32, 270, 840, 246], ("Calendario", "MesAño"), net),
            chart("productos_categories", "Unidades Vendidas por Categoría", "barChart",
                  [888, 270, 520, 246], ("Productos", "Categoria"),
                  ["Unidades Vendidas"]),
            chart("productos_detail", "Detalle de Productos", "tableEx",
                  [32, 532, 840, 246], ("Productos", "Producto"),
                  ["Ventas Netas", "Unidades Vendidas", "Descuentos",
                   "Tasa de Descuento"]),
            chart("productos_suppliers", "Top 5 Proveedores",
                  "barChart", [888, 532, 520, 246],
                  ("Proveedores", "Proveedor"), net, top=5),
        ], drillthrough=("Productos", "Producto")),
        make_page("clientes", "Clientes y Vendedores", [
            period, country, ("Cliente", "Clientes", "Cliente"), seller,
        ], DEFAULT_MEASURES, [
            chart("clientes_ranking", "Top 10 Clientes",
                  "barChart", [32, 270, 840, 246],
                  ("Clientes", "Cliente"), net, top=10),
            chart("clientes_sellers", "Ventas por Vendedor", "barChart",
                  [888, 270, 520, 246], ("Vendedores", "Vendedor"), net),
            chart("clientes_detail", "Detalle de Clientes", "tableEx",
                  [32, 532, 840, 246], ("Clientes", "Cliente"),
                  ["Ventas Netas", "Pedidos", "Ticket Promedio",
                   "Unidades Vendidas"]),
            chart("clientes_countries", "Ventas por País", "barChart",
                  [888, 532, 520, 246], ("Clientes", "Pais"), net),
        ], drillthrough=("Clientes", "Cliente")),
        make_page("logistica", "Análisis de Logística y Envíos", [
            period, country, category,
            ("Transportista", "Transportistas", "Transportista"),
        ], ["Flete Asignado", "Pedidos Enviados", "Dias Promedio Hasta Envio",
            "Pedidos", "Ventas Netas"], [
            chart("logistica_days", "Días Promedio de Envío por Transportista", "barChart",
                  [32, 270, 840, 246], ("Transportistas", "Transportista"),
                  ["Dias Promedio Hasta Envio"]),
            chart("logistica_freight", "Costo de Flete por Transportista",
                  "barChart", [888, 270, 520, 246],
                  ("Transportistas", "Transportista"), ["Flete Asignado"]),
            chart("logistica_trend", "Ventas por Fecha de Envío",
                  "lineChart", [32, 532, 840, 246],
                  ("Calendario", "MesAño"), ["Ventas por Fecha de Envio"]),
            chart("logistica_detail", "Resumen por Transportista", "tableEx",
                  [888, 532, 520, 246], ("Transportistas", "Transportista"),
                  ["Pedidos Enviados", "Flete Asignado",
                   "Dias Promedio Hasta Envio"]),
        ]),
    ]
    for page in built:
        page["heading_rect"] = [32, 16, 1200, 44]
        page["visuals"].append(button(
            f"{page['name']}_nav_inicio", "Inicio",
            [1248, 16, 160, 44], "inicio"))
    return copy.deepcopy([home_page()] + built)


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
