/*
Plantilla conceptual para cambio SCD tipo 2 en DimCustomer.
En producción, ejecutar como parte de un ETL controlado y comparar todos los atributos
que se decida historizar. No ejecutar junto con la carga inicial sin adaptar la fuente.
*/
USE NorthWindDW;
GO
DECLARE @CustomerID nchar(5) = N'ALFKI';
DECLARE @Now datetime2(0) = SYSUTCDATETIME();

-- 1. Cerrar versión anterior cuando se detecta un cambio real en atributos historizados.
-- Sustituir el filtro de ejemplo por la comparación completa de atributos.
UPDATE d
SET d.ValidTo = @Now,
    d.IsCurrent = 0
FROM dbo.DimCustomer d
JOIN NorthWind.dbo.Customers s ON s.CustomerID = d.CustomerID
WHERE d.CustomerID = @CustomerID
  AND d.IsCurrent = 1
  AND (
       ISNULL(d.CompanyName,N'') <> ISNULL(s.CompanyName,N'')
    OR ISNULL(d.City,N'') <> ISNULL(s.City,N'')
    OR ISNULL(d.Country,N'') <> ISNULL(s.Country,N'')
  );

-- 2. Insertar nueva versión si no existe una versión actual equivalente.
INSERT dbo.DimCustomer
    (CustomerID, CompanyName, ContactName, ContactTitle, Address, City, Region,
     PostalCode, Country, Phone, Fax, ValidFrom, ValidTo, IsCurrent)
SELECT s.CustomerID, s.CompanyName, s.ContactName, s.ContactTitle, s.Address,
       s.City, s.Region, s.PostalCode, s.Country, s.Phone, s.Fax,
       @Now, CONVERT(datetime2(0),'99991231'), 1
FROM NorthWind.dbo.Customers s
WHERE s.CustomerID = @CustomerID
  AND NOT EXISTS
      (SELECT 1 FROM dbo.DimCustomer d
       WHERE d.CustomerID = s.CustomerID AND d.IsCurrent = 1);
GO
