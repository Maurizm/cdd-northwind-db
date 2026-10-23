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

Estado de validacion: 46 pruebas unitarias aprobadas y los archivos
validados contra documentos de esquemas publicos de Microsoft, sin
errores. Esto valida la estructura, no sustituye la apertura/renderizado
en Power BI Desktop ni el cuadre de importes contra el SSAS desplegado.

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

Seis paginas; las cinco primeras son visibles y se navegan con la barra
de botones superior de cada una (`PageNavigation`):

| Pagina | Titulo | Notas |
|---|---|---|
| `resumen` | Resumen ejecutivo | 5 KPI + tendencia mensual vs. ano anterior (alterna ventas/pedidos por marcadores), top productos, categorias y clientes |
| `producto` | Analisis por producto | Drillthrough por `Producto`; dispersion precio-ventas y analisis por nivel de descuento |
| `geografico` | Analisis geografico | Azure Maps por pais del cliente + matriz pais/ciudad |
| `detalle` | Detalle de ventas | Matriz expandible Ano -> Mes -> Cliente -> Pedido y boton drillthrough a `transacciones` |
| `logistica` | Logistica: pedido a envio | Flete, dias pedido-envio, ventas por fecha de envio |
| `transacciones` | Transacciones del pedido | Drillthrough por `Pedido`; `HiddenInViewMode` (solo se llega por drillthrough) |

Cada pagina visible lleva: encabezado `NORTHWIND / <titulo>`, barra de 5
botones de navegacion (la pagina actual marcada), 4 segmentaciones
sincronizadas (Ano, Periodo mes-ano, Pais del cliente, Categoria) en modo
desplegable, boton **Limpiar filtros** (accion `ClearAllSlicers`),
tarjetas KPI y una banda de historia con botones **Anterior/Siguiente**
que recorren los marcadores del grupo `recorrido`.

Marcadores (`definition/bookmarks/`): grupo `recorrido` ("Recorrido del
negocio", 5 puntos de historia, uno por pagina visible) y grupo
`vista_tendencia` (`vista_ventas`/`vista_pedidos`, que alternan la
visibilidad de `resumen_trend` y `resumen_trend_orders`; ambos comparten
posicion y el segundo esta oculto por defecto con `isHidden`).

- Los visuales usan las **medidas SSAS heredadas** del modelo; no hay DAX
  copiado en el reporte.
- Los filtros temporales cubren fechas historicas del origen; no hay
  nocion de "hoy"/fecha actual.
- Sin simbolos de moneda (origen no la identifica), sin costos, margenes
  ni metas, y sin fecha real de entrega al cliente.

### Notas de diseno

- **Sin Key Influencers ni Decomposition Tree**: estos visuales no son
  compatibles con conexiones en vivo a SSAS (documentacion oficial de
  Power BI), asi que `producto` analiza el descuento como driver con un
  grafico de columnas por `Ventas[Nivel de Descuento]` y un combinado
  unidades/ticket promedio.
- **Azure Maps** necesita internet y que el visual este habilitado en
  Power BI Desktop (Opciones > Seguridad) o a nivel de tenant. Si no esta
  disponible, el grafico de barras "Ventas netas por pais" junto al mapa
  sirve como alternativa.

## Archivos generados

- `NorthWind.pbip` - proyecto raiz.
- `NorthWind.Report/` - `definition.pbir` (referencia por ruta al modelo),
  `definition/report.json` (tema + paquetes de recursos),
  `definition/version.json`, `definition/pages/pages.json`,
  `definition/pages/<pagina>/page.json`,
  `definition/pages/<pagina>/visuals/<visual>/visual.json`,
  `definition/bookmarks/bookmarks.json` +
  `definition/bookmarks/<nombre>.bookmark.json`,
  `StaticResources/RegisteredResources/NorthWind.json` (tema).
- `NorthWind.SemanticModel/` - `definition.pbism` + `modelReference.json`
  (referencia en vivo a SSAS, no un modelo importado).
- `preview-layout.js` - datos de layout generados desde el contrato
  (nombres/titulos/tipos/rects; se regenera con `build_report.py`).
- [preview.html](preview.html) - vista previa estatica del diseno (sin
  datos, no es render de Power BI); se mantiene a mano y lee
  `preview-layout.js`.
