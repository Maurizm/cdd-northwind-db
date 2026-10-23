"""Lead-authored field bindings and query semantics for the PBIR report.

Everything a visual must say about data -- which field goes in which role,
which measure populates a card, which slicers exist, which filter limits a
Top-N, the page navigation targets and the bookmarks -- lives here so the
renderer only adds layout and formatting.
"""

import copy

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/"

TOOLTIP_TRIO = ("Ventas Netas", "Unidades Vendidas", "Pedidos")

VISIBLE_PAGES = ["resumen", "producto", "geografico", "detalle", "logistica"]

NAV_LABELS = {
    "resumen": "Resumen", "producto": "Producto", "geografico": "Geográfico",
    "detalle": "Detalle", "logistica": "Logística",
}

STORY_BOOKMARKS = [
    "historia_1_resumen", "historia_2_producto", "historia_3_geografico",
    "historia_4_detalle", "historia_5_logistica",
]

STORY_DISPLAY = [
    "1. Cómo vamos", "2. Qué vendemos", "3. Dónde vendemos",
    "4. Quién y cuándo compra", "5. Cómo entregamos",
]

FILTERS = [
    ("Año", "Calendario", "Año"),
    ("Periodo (mes-año)", "Calendario", "MesAño"),
    ("País del cliente", "Clientes", "Pais"),
    ("Categoría", "Productos", "Categoria"),
]

CARTESIAN = (
    "barChart", "clusteredBarChart", "columnChart", "clusteredColumnChart",
    "lineChart", "lineClusteredColumnComboChart",
)


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


def lit(value):
    return {"expr": {"Literal": {"Value": value}}}


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


def chart(name, title, kind, rect, group=None, measures=(), top=None, *,
          series=None, x=None, y2=None, size=None, rows=(), columns=(),
          tooltips=None, hidden=False, swap_group=None, sort=None,
          objects=None, active_projections=False):
    state = {}
    if kind == "slicer":
        state["Values"] = {"projections": [projection(*group)]}
    else:
        if rows:
            state["Rows"] = {"projections": [projection(t, c) for t, c in rows]}
        if group:
            state["Category"] = {"projections": [projection(*group)]}
        if series:
            state["Series"] = {"projections": [projection(*series)]}
        if x:
            state["X"] = {"projections": [projection("Ventas", x, True)]}
        if columns:
            state["Values"] = {
                "projections": [projection(t, c) for t, c in columns]
            }
        if measures:
            role = ("Values" if kind in ("tableEx", "pivotTable")
                    else "Data" if kind == "card" else "Y")
            state.setdefault(role, {"projections": []})
            state[role]["projections"].extend(
                projection("Ventas", measure, True) for measure in measures)
        if y2:
            state["Y2"] = {"projections": [projection("Ventas", y2, True)]}
        if size:
            state["Size"] = {"projections": [projection("Ventas", size, True)]}
        if active_projections:
            for role in state.values():
                for item in role["projections"]:
                    item["active"] = True
    visual = {
        "visualType": kind,
        "query": {"queryState": state},
        "drillFilterOtherVisuals": True,
    }
    if objects:
        visual["objects"] = objects
    if group and kind in CARTESIAN:
        by_group = sort == "group" or (
            sort is None and (group[0] == "Calendario" or not measures))
        visual["query"]["sortDefinition"] = {
            "sort": [{
                "field": (field(*group) if by_group
                          else field("Ventas", measures[0], True)),
                "direction": "Ascending" if by_group else "Descending",
            }],
            "isDefaultSort": False,
        }
    if tooltips is None and kind in CARTESIAN + ("scatterChart",) \
            and list(measures) != ["Ventas por Fecha de Envio"]:
        tooltips = [m for m in TOOLTIP_TRIO if m not in measures]
    if tooltips:
        state["Tooltips"] = {"projections": [
            projection("Ventas", measure, True) for measure in tooltips]}
    if kind == "slicer":
        visual["syncGroup"] = {
            "groupName": f"{group[0]}_{group[1]}",
            "fieldChanges": True, "filterChanges": True,
        }
    result = {"name": name, "title": title, "rect": rect, "visual": visual}
    if top:
        result["filterConfig"] = top_filter(*group, measures[0], top)
    if hidden:
        result["hidden"] = True
    if swap_group:
        result["swap_group"] = swap_group
    return result


def button(name, label, rect, action_type, target=None, selected=False):
    action = {"type": action_type}
    if target:
        action["target"] = target
    return {
        "name": name, "title": label, "rect": rect,
        "visual": {"visualType": "actionButton"},
        "action": action, "selected": selected,
    }


def make_page(name, title, story, cards, charts, *, drillthrough=None,
              visibility=None, chrome=True):
    visuals = []
    if chrome:
        for i, target in enumerate(VISIBLE_PAGES):
            visuals.append(button(
                f"{name}_nav_{target}", NAV_LABELS[target],
                [624 + i * 156, 18, 146, 44], "PageNavigation", target,
                selected=(target == name)))
        for i, (label, table, column) in enumerate(FILTERS):
            visuals.append(chart(
                f"{name}_filter_{i}", label, "slicer",
                [32 + i * 276, 76, 260, 62], (table, column)))
        visuals.append(button(
            f"{name}_clear", "Limpiar filtros", [1136, 85, 272, 44],
            "ClearAllSlicers"))
    for i, measure in enumerate(cards):
        visuals.append(chart(
            f"{name}_kpi_{i}", measure, "card", [32 + i * 278, 154, 264, 100],
            measures=[measure]))
    visuals.extend(charts)
    if chrome:
        index = VISIBLE_PAGES.index(name)
        if index > 0:
            visuals.append(button(
                f"{name}_prev", "◀ Anterior", [1136, 766, 130, 40],
                "Bookmark", STORY_BOOKMARKS[index - 1]))
        if index < len(VISIBLE_PAGES) - 1:
            visuals.append(button(
                f"{name}_next", "Siguiente ▶", [1278, 766, 130, 40],
                "Bookmark", STORY_BOOKMARKS[index + 1]))
    result = {
        "name": name, "title": title, "story": story,
        "width": 1440, "height": 810,
        "visuals": visuals,
    }
    if visibility:
        result["visibility"] = visibility
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
    return [
        make_page("resumen", "Resumen ejecutivo",
                  "Cómo vamos: evolución mensual frente al año anterior y "
                  "quiénes concentran las ventas. Mayo de 1998 es un mes "
                  "parcial.",
                  ["Ventas Netas", "Pedidos", "Clientes Activos",
                   "Ticket Promedio", "Tasa de Descuento"],
                  [button("resumen_view_ventas", "Ver ventas",
                          [32, 270, 150, 40], "Bookmark", "vista_ventas"),
                   button("resumen_view_pedidos", "Ver pedidos",
                          [194, 270, 150, 40], "Bookmark", "vista_pedidos"),
                   chart("resumen_trend",
                         "Ventas netas mensuales vs. año anterior",
                         "lineChart", [32, 318, 880, 190],
                         ("Calendario", "MesAño"),
                         ["Ventas Netas", "Ventas Año Anterior"],
                         tooltips=["Crecimiento Interanual", "Pedidos"],
                         swap_group="resumen_trend"),
                   chart("resumen_trend_orders",
                         "Pedidos y clientes activos por mes",
                         "clusteredColumnChart", [32, 318, 880, 190],
                         ("Calendario", "MesAño"),
                         ["Pedidos", "Clientes Activos"],
                         hidden=True, swap_group="resumen_trend"),
                   chart("resumen_products",
                         "Top 5 productos por ventas netas",
                         "barChart", [928, 270, 480, 238],
                         ("Productos", "Producto"), ["Ventas Netas"], top=5),
                   chart("resumen_categories",
                         "Ventas netas por categoría",
                         "barChart", [32, 522, 688, 236],
                         ("Productos", "Categoria"), ["Ventas Netas"]),
                   chart("resumen_clients",
                         "Top 5 clientes por ventas netas",
                         "barChart", [736, 522, 672, 236],
                         ("Clientes", "Cliente"), ["Ventas Netas"], top=5)]),
        make_page("producto", "Análisis por producto",
                  "Qué vendemos: precio vs. volumen por producto y cómo "
                  "responde la venta a cada nivel de descuento.",
                  ["Ventas Netas", "Unidades Vendidas", "Precio Promedio",
                   "Descuentos", "Tasa de Descuento"],
                  [chart("producto_categories",
                         "Ventas netas por categoría",
                         "barChart", [32, 270, 560, 236],
                         ("Productos", "Categoria"), ["Ventas Netas"]),
                   chart("producto_scatter",
                         "Precio promedio vs. ventas netas por producto",
                         "scatterChart", [608, 270, 800, 236],
                         ("Productos", "Producto"), ["Ventas Netas"],
                         series=("Productos", "Categoria"),
                         x="Precio Promedio", size="Unidades Vendidas"),
                   chart("producto_discount",
                         "Influencia del descuento en las ventas netas",
                         "clusteredColumnChart", [32, 522, 456, 236],
                         ("Ventas", "Nivel de Descuento"), ["Ventas Netas"],
                         tooltips=["Unidades Vendidas", "Pedidos",
                                   "Ticket Promedio"],
                         sort="group"),
                   chart("producto_discount_combo",
                         "Unidades y ticket promedio por nivel de descuento",
                         "lineClusteredColumnComboChart", [504, 522, 456, 236],
                         ("Ventas", "Nivel de Descuento"),
                         ["Unidades Vendidas"], y2="Ticket Promedio",
                         sort="group"),
                   chart("producto_detail", "Detalle por producto",
                         "tableEx", [976, 522, 432, 236],
                         columns=[("Productos", "Producto")],
                         measures=["Ventas Netas", "Unidades Vendidas",
                                   "Precio Promedio", "Tasa de Descuento"])],
                  drillthrough=("Productos", "Producto")),
        make_page("geografico", "Análisis geográfico",
                  "Dónde vendemos: tamaño de la burbuja = ventas netas; "
                  "seleccione un país para filtrar el detalle por ciudad.",
                  ["Ventas Netas", "Clientes Activos", "Pedidos",
                   "Ticket Promedio", "Flete Asignado"],
                  [chart("geografico_map",
                         "Ventas netas por país del cliente",
                         "azureMap", [32, 270, 880, 488],
                         ("Clientes", "Pais"), size="Ventas Netas",
                         tooltips=["Pedidos", "Clientes Activos",
                                   "Ticket Promedio"],
                         objects={"bubbleLayer": [{"properties": {
                             "show": lit("true"),
                             "sizeByValue": lit("true")}}]},
                         active_projections=True),
                   chart("geografico_countries",
                         "Ventas netas por país",
                         "barChart", [928, 270, 480, 236],
                         ("Clientes", "Pais"), ["Ventas Netas"]),
                   chart("geografico_cities",
                         "Detalle por país y ciudad",
                         "pivotTable", [928, 522, 480, 236],
                         rows=[("Clientes", "Pais"), ("Clientes", "Ciudad")],
                         measures=["Ventas Netas", "Clientes Activos",
                                   "Pedidos"])]),
        make_page("detalle", "Detalle de ventas",
                  "Quién y cuándo compra: use + en la matriz para bajar "
                  "Año → Mes → Cliente → Pedido; seleccione un pedido y "
                  "pulse Ver líneas.",
                  ["Ventas Brutas", "Descuentos", "Ventas Netas",
                   "Unidades Vendidas", "Pedidos"],
                  [button("detalle_drill", "Ver líneas del pedido ▶",
                          [32, 270, 300, 40], "Drillthrough",
                          "transacciones"),
                   chart("detalle_matrix",
                         "Ventas por año, mes, cliente y pedido",
                         "pivotTable", [32, 318, 1376, 440],
                         rows=[("Calendario", "Año"),
                               ("Calendario", "Mes"),
                               ("Clientes", "Cliente"),
                               ("Ventas", "Pedido")],
                         measures=["Ventas Brutas", "Descuentos",
                                   "Ventas Netas", "Unidades Vendidas",
                                   "Pedidos"],
                         objects={"rowHeaders": [{"properties": {
                             "showExpandCollapseButtons": lit("true")}}]})]),
        make_page("logistica", "Logística: pedido a envío",
                  "Cómo entregamos: días pedido-envío y flete por "
                  "transportista.",
                  ["Flete Asignado", "Pedidos Enviados",
                   "Dias Promedio Hasta Envio", "Pedidos", "Ventas Netas"],
                  [chart("logistica_days", "Días entre pedido y envío",
                         "barChart", [32, 270, 880, 236],
                         ("Transportistas", "Transportista"),
                         ["Dias Promedio Hasta Envio"]),
                   chart("logistica_freight", "Flete asignado por "
                                              "transportista",
                         "barChart", [928, 270, 480, 236],
                         ("Transportistas", "Transportista"),
                         ["Flete Asignado"]),
                   chart("logistica_trend", "Ventas netas por fecha de envío",
                         "lineChart", [32, 522, 880, 236],
                         ("Calendario", "MesAño"),
                         ["Ventas por Fecha de Envio"]),
                   chart("logistica_detail", "Resumen por transportista",
                         "tableEx", [928, 522, 480, 236],
                         columns=[("Transportistas", "Transportista")],
                         measures=["Pedidos Enviados", "Flete Asignado",
                                   "Dias Promedio Hasta Envio"])]),
        make_page("transacciones", "Transacciones del pedido",
                  "Líneas del pedido seleccionado: producto, cantidad, "
                  "precio y descuento.",
                  ["Ventas Netas", "Unidades Vendidas", "Descuentos",
                   "Flete Asignado"],
                  [button("transacciones_back", "◀ Volver",
                          [32, 270, 150, 40], "Back"),
                   chart("transacciones_lines", "Líneas del pedido",
                         "tableEx", [32, 318, 1376, 440],
                         columns=[("Ventas", "Pedido"),
                                  ("Calendario", "Fecha"),
                                  ("Clientes", "Cliente"),
                                  ("Vendedores", "Vendedor"),
                                  ("Productos", "Producto"),
                                  ("Ventas", "Nivel de Descuento")],
                         measures=["Unidades Vendidas", "Precio Promedio",
                                   "Ventas Brutas", "Descuentos",
                                   "Ventas Netas"])],
                  drillthrough=("Ventas", "Pedido"),
                  visibility="HiddenInViewMode", chrome=False),
    ]


def _container(hidden=False):
    state = {"singleVisual": {}}
    if hidden:
        state["singleVisual"]["display"] = {"mode": "hidden"}
    return state


def bookmarks():
    """Bookmark index groups plus the per-bookmark documents."""
    files = {}
    for i, page in enumerate(VISIBLE_PAGES):
        name = STORY_BOOKMARKS[i]
        files[name] = {
            "name": name,
            "displayName": STORY_DISPLAY[i],
            "options": {
                "targetVisualNames": [],
                "suppressData": True,
                "suppressDisplay": True,
                "suppressActiveSection": False,
                "applyOnlyToTargetVisuals": False,
            },
            "explorationState": {
                "version": "1.3",
                "activeSection": page,
                "sections": {page: {"visualContainers": {}}},
            },
        }
    trend, orders = "resumen_trend", "resumen_trend_orders"
    files["vista_ventas"] = {
        "name": "vista_ventas",
        "displayName": "Tendencia: ventas",
        "options": {
            "targetVisualNames": [trend, orders],
            "suppressData": True,
            "suppressDisplay": False,
            "suppressActiveSection": True,
            "applyOnlyToTargetVisuals": False,
        },
        "explorationState": {
            "version": "1.3",
            "activeSection": "resumen",
            "sections": {"resumen": {"visualContainers": {
                trend: _container(),
                orders: _container(hidden=True),
            }}},
        },
    }
    files["vista_pedidos"] = {
        "name": "vista_pedidos",
        "displayName": "Tendencia: pedidos",
        "options": {
            "targetVisualNames": [trend, orders],
            "suppressData": True,
            "suppressDisplay": False,
            "suppressActiveSection": True,
            "applyOnlyToTargetVisuals": False,
        },
        "explorationState": {
            "version": "1.3",
            "activeSection": "resumen",
            "sections": {"resumen": {"visualContainers": {
                trend: _container(hidden=True),
                orders: _container(),
            }}},
        },
    }
    return {
        "items": [
            {"name": "recorrido", "displayName": "Recorrido del negocio",
             "children": STORY_BOOKMARKS},
            {"name": "vista_tendencia", "displayName": "Vista de tendencia",
             "children": ["vista_ventas", "vista_pedidos"]},
        ],
        "files": files,
    }


def connection_files(server="localhost", database="NorthWindOLAP"):
    """Live SSAS connection payload; the local model is never imported."""
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
