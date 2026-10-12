/*
Carga inicial de hechos de venta.
Requiere ejecutar antes 08_Cargar_Dimensiones_Inicial.sql.
Grano: una fila por línea de pedido (OrderID + ProductID).
El flete se guarda como FreightOrderAmount para trazabilidad, pero se repite por línea
y NO debe sumarse directamente en reportes; para análisis aditivo debe asignarse
proporcionalmente a las líneas durante ETL.
*/
USE NorthWindDW;
GO
SET XACT_ABORT ON;
BEGIN TRANSACTION;

INSERT dbo.FactSales
    (OrderID, OrderLineNumber, OrderDateKey, RequiredDateKey, ShippedDateKey,
     CustomerKey, ProductKey, EmployeeKey, ShipperKey, ShipToKey,
     Quantity, UnitPrice, DiscountRate, GrossAmount, DiscountAmount, NetAmount,
     FreightOrderAmount)
SELECT
    od.OrderID,
    od.ProductID,
    COALESCE(CONVERT(int,CONVERT(char(8),CONVERT(date,o.OrderDate),112)),0),
    COALESCE(CONVERT(int,CONVERT(char(8),CONVERT(date,o.RequiredDate),112)),0),
    COALESCE(CONVERT(int,CONVERT(char(8),CONVERT(date,o.ShippedDate),112)),0),
    dc.CustomerKey,
    dp.ProductKey,
    de.EmployeeKey,
    ds.ShipperKey,
    dst.ShipToKey,
    od.Quantity,
    CONVERT(decimal(19,4),od.UnitPrice),
    CONVERT(decimal(9,6),ISNULL(od.Discount,0)),
    CONVERT(decimal(19,4),od.Quantity * od.UnitPrice),
    CONVERT(decimal(19,4),od.Quantity * od.UnitPrice * ISNULL(od.Discount,0)),
    CONVERT(decimal(19,4),od.Quantity * od.UnitPrice * (1-ISNULL(od.Discount,0))),
    CONVERT(decimal(19,4),o.Freight)
FROM NorthWind.dbo.OrderDetails od
JOIN NorthWind.dbo.Orders o ON o.OrderID = od.OrderID
LEFT JOIN dbo.DimCustomer dc ON dc.CustomerID = o.CustomerID AND dc.IsCurrent = 1
LEFT JOIN dbo.DimProduct dp ON dp.ProductID = od.ProductID AND dp.IsCurrent = 1
LEFT JOIN dbo.DimEmployee de ON de.EmployeeID = o.EmployeeID AND de.IsCurrent = 1
LEFT JOIN dbo.DimShipper ds ON ds.ShipperID = o.ShipVia AND ds.IsCurrent = 1
LEFT JOIN dbo.DimShipTo dst
  ON ISNULL(dst.ShipName,N'') = ISNULL(o.ShipName,N'')
 AND ISNULL(dst.ShipAddress,N'') = ISNULL(o.ShipAddress,N'')
 AND ISNULL(dst.ShipCity,N'') = ISNULL(o.ShipCity,N'')
 AND ISNULL(dst.ShipRegion,N'') = ISNULL(o.ShipRegion,N'')
 AND ISNULL(dst.ShipPostalCode,N'') = ISNULL(o.ShipPostalCode,N'')
 AND ISNULL(dst.ShipCountry,N'') = ISNULL(o.ShipCountry,N'')
WHERE NOT EXISTS
(
    SELECT 1 FROM dbo.FactSales f
    WHERE f.OrderID = od.OrderID AND f.OrderLineNumber = od.ProductID
);

-- Verificación: las dimensiones requeridas deben haber encontrado su clave.
-- Si esta consulta devuelve filas, revisar claves nulas o datos fuente faltantes.
SELECT * FROM dbo.FactSales
WHERE CustomerKey IS NULL OR ProductKey IS NULL OR EmployeeKey IS NULL
   OR ShipperKey IS NULL OR ShipToKey IS NULL;

COMMIT TRANSACTION;
GO
