# NorthWindOLAP - Modelo tabular SSAS

Proyecto de modelo semántico tabular (Analysis Services) sobre el data
warehouse `NorthWindDW`. Este proyecto solo contiene la definición del
modelo; el tablero de Power BI se genera en formato PBIP/PBIR desde
`../NorthWindReports` (ver [NorthWindReports/README.md](../NorthWindReports/README.md)).

## Fuente de verdad

La fuente de verdad del modelo es el generador `build_model.py`. El archivo
`NorthWind.bim` es un artefacto generado; no se edita a mano.

Generar el modelo:

```
python NorthWindBI/NorthWindOLAP/build_model.py
```

Opciones: `--sql-server` (por defecto `localhost`) y `--sql-database`
(por defecto `NorthWindDW`) ajustan la cadena de conexión embebida;
`--output` cambia la ruta de salida del `.bim`. Generar no conecta a SQL
Server ni a SSAS.

## Estructura del modelo

Siete tablas: `Ventas` (hechos) más las dimensiones `Calendario`,
`Clientes`, `Productos`, `Vendedores`, `Proveedores` y `Transportistas`.

- Grano de `Ventas`: una fila por línea de pedido (`SalesKey`; `OrderID` +
  `OrderLineNum` se conservan ocultas para conteo de pedidos).
- Geografía integrada: `DimGeography` se fusiona vía LEFT JOIN dentro de
  las dimensiones relevantes (`Clientes`, `Vendedores`, `Proveedores`) como
  columnas `Pais`/`Region`/`Ciudad`. No existe tabla de geografía propia y
  el DW no se modifica.
- Relaciones: una activa `Ventas[OrderDateKey] -> Calendario[DateKey]` y
  dos inactivas sobre `ShippedDateKey` y `RequiredDateKey`. Las medidas del
  grupo `Fechas` usan `USERELATIONSHIP` para activar las inactivas bajo
  demanda.
- Medidas: todas viven en `Ventas` y se heredan en el tablero; no hace
  falta copiar fórmulas DAX a reportes. Carpetas `Importes`, `Actividad`,
  `Logistica`, `Fechas`.
- Moneda: los importes usan formato numérico `#,0.00`; el origen no
  identifica moneda, por lo que ninguna medida asume una divisa.
- Entregas: no existe fecha real de entrega al cliente en el DW.
  `DiasHastaEnvio` mide pedido -> envío, no entrega.
- Conteos: `Pedidos` es `DISTINCTCOUNT(Ventas[OrderID])` (no aditivo entre
  productos/categorías) y `Dias Promedio Hasta Envio` se pondera por pedido
  (`AVERAGEX(VALUES(Ventas[OrderID]), ...)`), no por línea.

## Fecha desconocida (-1)

La fila desconocida `DateKey = -1` se conserva para que los pedidos sin
fecha sigan contando en los totales, pero `Fecha` y `Año` se proyectan como
NULL para evitar un falso grupo "1900". `Calendario` no está marcada como
tabla de fechas continua para DAX (sin Mark as Date Table), así que las
funciones de inteligencia de tiempo no deben asumir continuidad.

## Conexión al origen

- Tipo `provider` con `Provider=MSOLEDBSQL` (requiere el proveedor OLE DB
  para SQL Server instalado donde se procese el modelo).
- Autenticación integrada con `impersonateServiceAccount`: el procesamiento
  usa la cuenta de servicio de SSAS, que necesita `SELECT` sobre
  `NorthWindDW`. No se usa `sa` ni contraseñas en el modelo.

  En un SSAS cuya cuenta de servicio es `NT SERVICE\MSSQLServerOLAPService`
  el permiso se concede así:

  ```sql
  CREATE LOGIN [NT SERVICE\MSSQLServerOLAPService] FROM WINDOWS;
  USE NorthWindDW;
  CREATE USER [NT SERVICE\MSSQLServerOLAPService]
      FOR LOGIN [NT SERVICE\MSSQLServerOLAPService];
  ALTER ROLE db_datareader ADD MEMBER [NT SERVICE\MSSQLServerOLAPService];
  ```

## Requisitos y despliegue

- `compatibilityLevel` 1600: requiere SQL Server Analysis Services 2022 o
  un servidor tabular más reciente compatible (este host con SQL Server
  2025 es compatible).
- El `.smproj` trae `DeploymentOptionProcessing = DoNotProcess`: después de
  implementar hay que procesar el modelo deliberadamente (SSMS/XMLA `Process
  Full` o similar); los datos no aparecen solos.
- Compilar solo `NorthWindOLAP`. No desplegar la solución completa: el
  script postdeploy existente del proyecto `NorthWindDW` limpia y recarga
  el DW (la compilación en sí no lo ejecuta).
- Si el Deploy de Visual Studio falla con "Failed to create the ADOMD
  Connection ... database does not exist", la alternativa es enviar el
  `bin\NorthWind.asdatabase` compilado como TMSL `createOrReplace`
  (TOM `Server.Execute`, SSMS o `Invoke-ASCmd`) y luego procesar con
  `{"refresh":{"type":"full","objects":[{"database":"NorthWindOLAP"}]}}`.
- Verificado end-to-end: el modelo se desplegó y procesó en el SSAS local
  con 2.155 filas en `Ventas` y `[Ventas Netas]` = 1.265.793,04.
