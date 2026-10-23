# NorthWindReports - Reporte Power BI (PBIP/PBIR)

Reporte nativo de Power BI sobre el modelo tabular `NorthWindOLAP`, en
formato PBIP/PBIR (proyecto, sin `.pbix`). Los bindings de campos, filtros
y semanticas de consulta viven en el contrato
[report_contract.py](report_contract.py); el generador
[build_report.py](build_report.py) solo agrega formato, posiciones y
metadatos de contenedor.

## Regenerar

```
python NorthWindBI/NorthWindReports/build_report.py
```

Opciones: `--ssas-server` (por defecto `localhost`), `--ssas-database`
(por defecto `NorthWindOLAP`), `--output` (por defecto esta carpeta).
La regeneracion es determinista: sobrescribe los archivos generados
conocidos, pero aborta sin escribir nada si encuentra directorios de
paginas o visuales que no espera (no borra trabajo ajeno).

## Como abrir

1. Desplegar y **procesar** el modelo `NorthWindOLAP` en SSAS primero (ver
   [../NorthWindOLAP/README.md](../NorthWindOLAP/README.md)); el proyecto
   llega con `DoNotProcess` por diseno.
2. Abrir `NorthWind.pbip` en Power BI Desktop moderno con soporte
   PBIP/PBIR.
3. El reporte referencia el modelo en vivo via
   `NorthWind.SemanticModel/modelReference.json` (conexion SSAS integrada
   `Integrated Security=SSPI`). No se publica a Fabric ni a Power BI
   Service y no se exporta data de origen al proyecto.

Estado de validacion: 32 pruebas offline aprobadas y 72 archivos validados
contra 15 documentos de esquemas publicos de Microsoft, sin errores.
La vista previa HTML se comprobo en escritorio y movil. Esto valida la
estructura, no sustituye la apertura/renderizado en Power BI Desktop ni
la ejecucion de DAX y el cuadre de importes con datos reales en SSAS.

## Reproducir en otro equipo

Para visualizar el dashboard en un ambiente propio (SQL Server + SSAS
Tabular 2022+ y Power BI Desktop con soporte PBIP):

1. **Cargar el DW**: desplegar `../NorthWindDW/NorthWindDW.sqlproj`
   (VS: clic derecho > Deploy) y ejecutar el ETL para llenarlo, o
   restaurar un backup de `NorthWindDW`.
2. **Generar el modelo apuntando a tu servidor**:
   `python ../NorthWindOLAP/build_model.py --sql-server TU-SERVIDOR --sql-database NorthWindDW`
3. **Permiso de lectura**: la cuenta de servicio de SSAS necesita login
   en SQL Server y `db_datareader` en `NorthWindDW` (script exacto en
   [../NorthWindOLAP/README.md](../NorthWindOLAP/README.md)).
4. **Desplegar el modelo**: VS > clic derecho en `NorthWindOLAP` >
   Deploy; o la via TMSL `createOrReplace` con `bin/NorthWind.asdatabase`
   desde una ventana XMLA de SSMS.
5. **Procesar**: SSMS > Process Database > Process Full, o TMSL
   `{"refresh":{"type":"full","objects":[{"database":"NorthWindOLAP"}]}}`.
6. **Apuntar el reporte a tu servidor** si no es `localhost`:
   `python build_report.py --ssas-server TU-SERVIDOR`
   (o editar `NorthWind.SemanticModel/modelReference.json` a mano).
7. Abrir `NorthWind.pbip` en Power BI Desktop con autenticacion Windows.

Si en cambio el dashboard consume **tu** servidor SSAS, los companeros
solo necesitan Power BI Desktop, el `modelReference.json` apuntando a tu
equipo, y permiso de lectura en el modelo (SSMS > servidor AS >
Properties > Security > agregar sus usuarios).

Validacion opcional de esquemas (requiere `jsonschema` + `referencing`
instalados y red solo hacia GitHub de Microsoft; no instala nada):

```
python NorthWindBI/NorthWindReports/validate_report_schemas.py
```

## Contenido

Cuatro paginas navegables por pestanas:

| Pagina | Titulo | Notas |
|---|---|---|
| `panorama` | Panorama de ventas | 5 KPI + tendencia, categorias, top clientes/productos, tabla por pais |
| `productos` | Productos y categorias | Drillthrough visible por `Producto` |
| `clientes` | Clientes y vendedores | Drillthrough visible por `Cliente` |
| `logistica` | Logistica: pedido a envio | Flete, dias pedido-envio, ventas por fecha de envio |

- Los visuales usan las **medidas SSAS heredadas** del modelo; no hay DAX
  copiado en el reporte.
- Slicers en modo lista desplegable con grupos de sincronizacion del
  contrato; la navegacion es por pestanas nativas (sin bookmarks).
- Para limpiar filtros usar el **borrador nativo del slicer** (icono de
  borrador); no existe marcador de "reset" fabricado.
- Los filtros temporales cubren fechas historicas del origen; no hay
  nocion de "hoy"/fecha actual.
- Sin simbolos de moneda (origen no la identifica), sin costos, margenes
  ni metas, y sin fecha real de entrega al cliente.

## Archivos generados

- `NorthWind.pbip` - proyecto raiz.
- `NorthWind.Report/` - `definition.pbir` (referencia por ruta al modelo),
  `definition/report.json` (tema + paquetes de recursos),
  `definition/version.json`, `definition/pages/pages.json`,
  `definition/pages/<pagina>/page.json`,
  `definition/pages/<pagina>/visuals/<visual>/visual.json`,
  `StaticResources/RegisteredResources/NorthWind.json` (tema).
- `NorthWind.SemanticModel/` - `definition.pbism` + `modelReference.json`
  (referencia en vivo a SSAS, no un modelo importado).
- `preview-layout.js` - datos de layout generados desde el contrato
  (nombres/titulos/tipos/rects; se regenera con `build_report.py`).
- [preview.html](preview.html) - vista previa estatica del diseno (sin
  datos, no es render de Power BI); se mantiene a mano y lee
  `preview-layout.js`.
