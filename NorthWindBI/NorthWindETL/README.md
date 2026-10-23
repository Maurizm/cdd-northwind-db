# NorthWindETL — Guía de pruebas manuales

Paquetes SSIS que cargan `NorthWindDW` de forma incremental usando
`rowversion` en `NorthWindOLTP`. El paquete `FactSales.dtsx` carga la tabla
de hechos `[dbo].[FactSales]`; los cinco paquetes `Dim*.dtsx` cargan las
dimensiones. Todos comparten el parámetro de proyecto
`$Project::ServerName` (valor por defecto `localhost`).

## Prerequisitos

- SQL Server con `NorthWindOLTP` y `NorthWindDW` desplegadas y cargadas
  (postdeployment `Script.PostDeployment.sql` → scripts `00`–`04`).
- `dtexec` (viene con SQL Server, p. ej.
  `C:\Program Files\Microsoft SQL Server\170\DTS\Binn\DTExec.exe`) o
  Visual Studio con la extensión **SQL Server Integration Services Projects**.
- Para el job: **SQL Server Agent** en ejecución.
- Para `/ISSERVER`: catálogo **SSISDB** creado en la instancia
  (clic derecho en *Integration Services Catalogs* → *Create Catalog* en SSMS).
- Alternativa sin SSISDB: cambiar los pasos del job a subsistema
  `CmdExec` con `dtexec /F "ruta\Paquete.dtsx"`.

## Despliegue en SSISDB

1. Abrir `NorthWindBI.slnx` en Visual Studio, compilar
   `NorthWindETL` (genera `bin\NorthWindETL.ispac`).
2. En SSMS: *Integration Services Catalogs → SSISDB → clic derecho →
   Create Folder* → nombre `NorthWind`.
3. Clic derecho en `SSISDB\NorthWind` → *Deploy Project* → seleccionar
   `bin\NorthWindETL.ispac` → destino `SSISDB\NorthWind\NorthWindETL`.
4. Verificar el parámetro `ServerName` del proyecto en SSISDB
   (debe quedar `localhost` o el servidor deseado).

## Ejecución manual

Desde Visual Studio (F5 dentro del proyecto) o desde línea de comandos:

```bat
:: Los paquetes Dim* primero, FactSales al final
dtexec /F "C:\ruta\al\repo\NorthWindBI\NorthWindETL\DimCustomer.dtsx"
dtexec /F "C:\ruta\al\repo\NorthWindBI\NorthWindETL\FactSales.dtsx"
```

> **Nota (`$Project::ServerName`)**: al ejecutar un `.dtsx` suelto con
> `dtexec /F`, el parámetro de proyecto no existe y se registran errores de
> evaluación `0xC00470A6`/`0xC0017003` en los connection managers (SQL
> Server usa el `Data Source=localhost` embebido y los paquetes terminan
> igual). El resumen sale como `DTSER_FAILURE` solo porque el conteo de
> errores supera `MaximumErrorCount=1`; para ejecuciones sueltas puede
> elevarse:
>
> ```bat
> dtexec /F "...\FactSales.dtsx" /Set "\Package.Properties[MaximumErrorCount]";999
> ```
>
> En SSDT o SSISDB el parámetro sí se resuelve y no aparecen esos errores.

## Verificación de resultados

```sql
-- Filas procesadas en la corrida actual (staging queda con las
-- filas actualizadas de la última ejecución, no se trunca al final)
SELECT COUNT(*) AS StagingSales FROM NorthWindDW.staging.sales;

-- Hechos y totales
SELECT COUNT(*) AS FactCount,
       SUM(NetAmount) AS SumNet, SUM(GrossAmount) AS SumGross,
       SUM(Freight) AS SumFreight, SUM(AllocatedFreight) AS SumAlloc
FROM NorthWindDW.dbo.FactSales;

-- Marca de agua por tabla
SELECT TableName, LastRowVersion FROM NorthWindDW.dbo.PackageConfig;

-- Fórmulas puntuales
SELECT TOP 5 OrderID, OrderLineNum, Quantity, UnitPrice,
       GrossAmount, Quantity * UnitPrice AS Esperado
FROM NorthWindDW.dbo.FactSales
WHERE GrossAmount <> CONVERT(MONEY, Quantity * UnitPrice);  -- debe devolver 0 filas

SELECT COUNT(*) AS NetWrong
FROM NorthWindDW.dbo.FactSales
WHERE NetAmount <> CONVERT(MONEY, Quantity * UnitPrice * (1 - Discount));  -- 0

-- Miembros desconocidos (-1) en llaves de dimensión
SELECT
  SUM(CASE WHEN CustomerKey = -1 THEN 1 ELSE 0 END) AS SinCliente,
  SUM(CASE WHEN EmployeeKey = -1 THEN 1 ELSE 0 END) AS SinEmpleado,
  SUM(CASE WHEN ProductKey  = -1 THEN 1 ELSE 0 END) AS SinProducto,
  SUM(CASE WHEN SupplierKey = -1 THEN 1 ELSE 0 END) AS SinProveedor,
  SUM(CASE WHEN ShipperKey  = -1 THEN 1 ELSE 0 END) AS SinTransportista
FROM NorthWindDW.dbo.FactSales;
```

## Prueba incremental (insert + update)

```sql
-- 1) Insertar un pedido de prueba y una línea
INSERT INTO NorthWindOLTP.dbo.Orders
  (CustomerID, EmployeeID, OrderDate, RequiredDate, ShipVia, Freight)
VALUES ('VINET', 5, '1998-01-05', '1998-02-05', 3, 99.99);
DECLARE @oid INT = SCOPE_IDENTITY();
INSERT INTO NorthWindOLTP.dbo.OrderDetails
  (OrderID, ProductID, UnitPrice, Quantity, Discount)
VALUES (@oid, 11, 14.00, 10, 0);

-- 2) Ejecutar FactSales → la línea nueva entra por la ruta
--    "Lookup No Match" → inserción directa en FactSales
SELECT * FROM NorthWindDW.dbo.FactSales WHERE OrderID = @oid;  -- 1 fila

-- 3) Actualizar la línea en OLTP y volver a ejecutar FactSales
UPDATE NorthWindOLTP.dbo.OrderDetails SET Quantity = 20 WHERE OrderID = @oid;
-- segunda ejecución → la fila va a staging.sales y DW_MergeFactSales
-- actualiza el hecho existente (Quantity = 20, NetAmount = 280)

-- 4) Limpieza y re-ejecución para devolver todo a su estado
DELETE FROM NorthWindOLTP.dbo.OrderDetails WHERE OrderID = @oid;
DELETE FROM NorthWindOLTP.dbo.Orders WHERE OrderID = @oid;
DELETE FROM NorthWindDW.dbo.FactSales WHERE OrderID = @oid;
-- o re-ejecutar los scripts postdeployment 00–03 para reconstruir el DW
```

## Idempotencia

- Ejecutar `FactSales.dtsx` dos veces seguidas: la segunda extracción
  devuelve 0 filas (`LastRowVersion` ya quedó en el DBTS vigente),
  `staging.sales` termina vacía y los totales de `FactSales` no cambian.
- La clave de mezcla es `(OrderID, OrderLineNum)`, por lo que repetir la
  corrida nunca duplica hechos.

## Job de SQL Server Agent

`NorthWindJob.sql` crea el job **NorthWindJob** con un paso por cada
`.dtsx` del proyecto (dimensiones 1–5, `FactSales` paso 6). Cada paso
usa el subsistema `SSIS` con `/ISSERVER` contra
`SSISDB\NorthWind\NorthWindETL`.

1. Desplegar el proyecto en SSISDB (ver arriba) y ejecutar
   `NorthWindJob.sql` en SSMS.
2. Arrancar manualmente:

   ```sql
   EXEC msdb.dbo.sp_start_job 'NorthWindJob';
   EXEC msdb.dbo.sp_help_jobhistory @job_name = 'NorthWindJob';
   SELECT * FROM msdb.dbo.sysjobhistory
   WHERE job_id = (SELECT job_id FROM msdb.dbo.sysjobs WHERE name='NorthWindJob');
   ```

3. Programación: diaria a las **02:00** (se puede deshabilitar el
   schedule desde SSMS → Jobs → NorthWindJob → Schedules).

## Recuperación ante fallos

- `@on_fail_action=2`: si un paso falla, el job se detiene con error
  (no continúa con los siguientes).
- Para reanudar: arreglar la causa y arrancar el job desde el paso
  fallido en SSMS (*Start Job at Step…*), o re-ejecutar el job completo.
- Los paquetes son re-ejecutables: `Clean-up staging` trunca el área
  de trabajo al inicio de cada corrida y la fusión usa
  `(OrderID, OrderLineNum)`.

## Estructura del paquete FactSales

| Paso | Componente | Acción |
|------|-----------|--------|
| 1 | `Get Database DBTS` | `GetDatabaseRowVersion` → `User::dbts` (OLTP) |
| 2 | `Get Table RowVersion` | `GetLastPackageRowVersion 'Orders'` → `User::lastRowVersion` (DW) |
| 3 | `Clean-up staging` | `TRUNCATE staging.sales` |
| 4 | `Load Sales` | Data flow descrito abajo |
| 5 | `Sync Fact Sales` | `DW_MergeFactSales` (UPDATE por OrderID+OrderLineNum) |
| 6 | `Update config` | `UpdateLastPackageRowVersion 'Orders', @User::dbts` |

Data flow `Load Sales`:

```
Get rows from Orders (sproc, @startRow=?→lastRowVersion, @endRow=?→dbts)
 → Lookup Customer → Lookup Employee → Lookup Product → Lookup Supplier
 → Lookup Shipper (claves -1 vía ISNULL en el derivado)
 → Calculate Amounts and Keys (Gross/Discount/Net/AllocatedFreight)
 → Lookup Sales (FactSales por OrderID+OrderLineNum)
     ├─ Match    → Load staging sales → DW_MergeFactSales (UPDATE)
     └─ No Match → Load Fact Sales    → INSERT directo
```
