"""Build the versioned SSAS model without connecting to SQL Server or SSAS."""

import argparse
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
NUMBER = "#,0"
AMOUNT = "#,0.00"

# Explicit projections keep technical/PII columns out of the analytical model.
SOURCES = {
    "Calendario": """
SELECT [DateKey],
       CASE WHEN [DateKey] <> -1 THEN [FullDate] END AS [Fecha],
       CASE WHEN [DateKey] <> -1 THEN [Year] END AS [Ano],
       [QuarterName] AS [Trimestre], [Quarter] AS [TrimestreNumero],
       [MonthName] AS [Mes], [MonthOfYear] AS [MesNumero],
       CASE WHEN [DateKey] = -1 THEN N'Desconocido'
            ELSE CONVERT(NVARCHAR(7), [FullDate], 126) END AS [MesAnio],
       CASE WHEN [DateKey] = -1 THEN 0
            ELSE [Year] * 100 + [MonthOfYear] END AS [OrdenMesAnio]
FROM [dbo].[DimDate]
""",
    "Clientes": """
SELECT c.[CustomerKey], c.[CompanyName] AS [Cliente],
       g.[Country] AS [Pais], g.[Region] AS [Region], g.[City] AS [Ciudad]
FROM [dbo].[DimCustomer] c
LEFT JOIN [dbo].[DimGeography] g ON c.[GeographyKey] = g.[GeographyKey]
""",
    "Productos": """
SELECT [ProductKey], [ProductName] AS [Producto],
       [CategoryName] AS [Categoria], [ProductStatus] AS [Estado]
FROM [dbo].[DimProduct]
""",
    "Vendedores": """
SELECT e.[EmployeeKey], e.[FullName] AS [Vendedor], e.[Title] AS [Cargo],
       e.[ManagerName] AS [Supervisor], g.[Country] AS [Pais],
       g.[Region] AS [Region], g.[City] AS [Ciudad]
FROM [dbo].[DimEmployee] e
LEFT JOIN [dbo].[DimGeography] g ON e.[GeographyKey] = g.[GeographyKey]
""",
    "Proveedores": """
SELECT s.[SupplierKey], s.[CompanyName] AS [Proveedor],
       g.[Country] AS [Pais], g.[Region] AS [Region], g.[City] AS [Ciudad]
FROM [dbo].[DimSupplier] s
LEFT JOIN [dbo].[DimGeography] g ON s.[GeographyKey] = g.[GeographyKey]
""",
    "Transportistas": """
SELECT [ShipperKey], [CompanyName] AS [Transportista]
FROM [dbo].[DimShipper]
""",
    "Ventas": """
SELECT f.[SalesKey], f.[OrderID], f.[OrderLineNum],
       f.[OrderDateKey], f.[ShippedDateKey], f.[RequiredDateKey],
       f.[CustomerKey], f.[EmployeeKey], f.[ProductKey],
       f.[SupplierKey], f.[ShipperKey], f.[Quantity],
       f.[GrossAmount], f.[DiscountAmount], f.[NetAmount], f.[AllocatedFreight],
       CASE WHEN f.[OrderDateKey] <> -1 AND f.[ShippedDateKey] <> -1
            THEN DATEDIFF(DAY, od.[FullDate], sd.[FullDate]) END
            AS [DiasHastaEnvio]
FROM [dbo].[FactSales] f
LEFT JOIN [dbo].[DimDate] od ON f.[OrderDateKey] = od.[DateKey]
LEFT JOIN [dbo].[DimDate] sd ON f.[ShippedDateKey] = sd.[DateKey]
""",
}

MEASURES = [
    ("Ventas Brutas", "SUM(Ventas[GrossAmount])", AMOUNT, "Importes",
     "Importe antes de descuentos; la moneda no esta identificada en el origen."),
    ("Descuentos", "SUM(Ventas[DiscountAmount])", AMOUNT, "Importes",
     "Importe de descuentos concedidos, no porcentaje."),
    ("Ventas Netas", "SUM(Ventas[NetAmount])", AMOUNT, "Importes",
     "Importe despues de descuentos, sin agregar flete."),
    ("Unidades Vendidas", "SUM(Ventas[Quantity])", NUMBER, "Actividad",
     "Unidades de las lineas de pedido en el contexto seleccionado."),
    ("Pedidos", "DISTINCTCOUNT(Ventas[OrderID])", NUMBER, "Actividad",
     "Pedidos distintos. No es aditivo entre productos o categorias."),
    ("Ticket Promedio", "DIVIDE([Ventas Netas], [Pedidos])", AMOUNT, "Importes",
     "Ventas netas por pedido dentro del contexto seleccionado."),
    ("Tasa de Descuento", "DIVIDE([Descuentos], [Ventas Brutas])",
     "0.0%", "Importes", "Descuento efectivo ponderado por importe bruto."),
    ("Flete Asignado", "SUM(Ventas[AllocatedFreight])", AMOUNT, "Logistica",
     "Flete distribuido entre lineas por el ETL; puede tener redondeo monetario."),
    ("Pedidos Enviados",
     "CALCULATE([Pedidos], KEEPFILTERS(Ventas[ShippedDateKey] <> -1))",
     NUMBER, "Logistica", "Pedidos con fecha de envio conocida."),
    ("Dias Promedio Hasta Envio",
     "AVERAGEX(VALUES(Ventas[OrderID]), "
     "CALCULATE(MAX(Ventas[DiasHastaEnvio])))",
     "0.0", "Logistica",
     "Dias pedido-envio, ponderados por pedido, no por linea. "
     "No mide entrega al cliente; omite fechas desconocidas."),
    ("Ventas por Fecha de Envio",
     "CALCULATE([Ventas Netas], "
     "USERELATIONSHIP(Ventas[ShippedDateKey], Calendario[DateKey]))",
     AMOUNT, "Fechas", "Ventas netas agrupadas por fecha de envio."),
    ("Ventas por Fecha Requerida",
     "CALCULATE([Ventas Netas], "
     "USERELATIONSHIP(Ventas[RequiredDateKey], Calendario[DateKey]))",
     AMOUNT, "Fechas", "Ventas netas agrupadas por fecha requerida."),
]


def column(name, data_type="string", *, hidden=False, key=False, sort=None):
    result = {
        "name": name, "dataType": data_type, "sourceColumn": name,
        "summarizeBy": "none",
    }
    if hidden:
        result["isHidden"] = True
    if key:
        result["isKey"] = True
    if sort:
        result["sortByColumn"] = sort
    if data_type == "decimal":
        result["formatString"] = AMOUNT
    if data_type == "dateTime":
        result["formatString"] = "yyyy-MM-dd"
    return result


def hierarchy(name, columns):
    return {
        "name": name,
        "levels": [
            {"name": name, "ordinal": i, "column": name}
            for i, name in enumerate(columns)
        ],
    }


def table(name, columns, hierarchies=()):
    result = {
        "name": name,
        "columns": columns,
        "partitions": [{
            "name": name, "mode": "import",
            "source": {
                "type": "query", "dataSource": "NorthWindDW",
                "query": SOURCES[name].strip(),
            },
        }],
    }
    if hierarchies:
        result["hierarchies"] = list(hierarchies)
    return result


def build_model(server="localhost", database="NorthWindDW"):
    def key(name):
        return column(name, "int64", hidden=True, key=True)

    def geography():
        return [column(name) for name in ("Pais", "Region", "Ciudad")]

    tables = [
        table("Calendario", [
            key("DateKey"), column("Fecha", "dateTime"),
            column("Ano", "int64"),
            column("Trimestre", sort="TrimestreNumero"),
            column("TrimestreNumero", "int64", hidden=True),
            column("Mes", sort="MesNumero"),
            column("MesNumero", "int64", hidden=True),
            column("MesAnio", sort="OrdenMesAnio"),
            column("OrdenMesAnio", "int64", hidden=True),
        ], [hierarchy("Calendario", ["Ano", "Trimestre", "Mes", "Fecha"])]),
        table("Clientes", [key("CustomerKey"), column("Cliente"), *geography()],
              [hierarchy("Ubicacion del Cliente",
                         ["Pais", "Region", "Ciudad", "Cliente"])]),
        table("Productos", [key("ProductKey"), column("Producto"),
                            column("Categoria"), column("Estado")],
              [hierarchy("Catalogo", ["Categoria", "Producto"])]),
        table("Vendedores", [key("EmployeeKey"), column("Vendedor"),
                             column("Cargo"), column("Supervisor"), *geography()]),
        table("Proveedores", [key("SupplierKey"), column("Proveedor"),
                              *geography()]),
        table("Transportistas", [key("ShipperKey"), column("Transportista")]),
        table("Ventas", [
            key("SalesKey"),
            *[column(name, "int64", hidden=True) for name in (
                "OrderID", "OrderLineNum", "OrderDateKey", "ShippedDateKey",
                "RequiredDateKey", "CustomerKey", "EmployeeKey", "ProductKey",
                "SupplierKey", "ShipperKey", "Quantity", "DiasHastaEnvio",
            )],
            *[column(name, "decimal", hidden=True) for name in (
                "GrossAmount", "DiscountAmount", "NetAmount", "AllocatedFreight",
            )],
        ]),
    ]
    tables[-1]["measures"] = [
        {"name": name, "expression": expression, "formatString": fmt,
         "displayFolder": folder, "description": description}
        for name, expression, fmt, folder, description in MEASURES
    ]
    relationships = []
    for dimension, foreign_key, active in [
        ("Calendario", "OrderDateKey", True),
        ("Calendario", "ShippedDateKey", False),
        ("Calendario", "RequiredDateKey", False),
        ("Clientes", "CustomerKey", True),
        ("Productos", "ProductKey", True),
        ("Vendedores", "EmployeeKey", True),
        ("Proveedores", "SupplierKey", True),
        ("Transportistas", "ShipperKey", True),
    ]:
        relationships.append({
            "name": f"Ventas_{foreign_key}",
            "fromTable": "Ventas", "fromColumn": foreign_key,
            "fromCardinality": "many",
            "toTable": dimension,
            "toColumn": "DateKey" if dimension == "Calendario" else foreign_key,
            "toCardinality": "one", "isActive": active,
            "crossFilteringBehavior": "oneDirection",
        })
    return {
        "name": "NorthWindOLAP", "id": "NorthWindOLAP",
        "compatibilityLevel": 1600,
        "model": {
            "culture": "es-ES",
            "dataSources": [{
                "name": "NorthWindDW", "type": "provider",
                "connectionString": (
                    f"Provider=MSOLEDBSQL;Data Source={server};"
                    f"Initial Catalog={database};Integrated Security=SSPI;"
                    "Persist Security Info=False"
                ),
                "impersonationMode": "impersonateServiceAccount",
            }],
            "tables": tables, "relationships": relationships,
            "perspectives": [{
                "name": "Ventas",
                "tables": [
                    {"name": t["name"],
                     "columns": [{"name": c["name"]} for c in t["columns"]
                                 if not c.get("isHidden")],
                     **({"hierarchies": [{"name": h["name"]}
                                         for h in t["hierarchies"]]}
                        if t.get("hierarchies") else {}),
                     **({"measures": [{"name": m["name"]}
                                      for m in t["measures"]]}
                        if t.get("measures") else {})}
                    for t in tables
                ],
            }],
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-server", default="localhost")
    parser.add_argument("--sql-database", default="NorthWindDW")
    parser.add_argument("--output", type=Path, default=HERE / "NorthWind.bim")
    args = parser.parse_args()
    model = build_model(args.sql_server, args.sql_database)
    args.output.write_text(
        json.dumps(model, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Generated {args.output}")
