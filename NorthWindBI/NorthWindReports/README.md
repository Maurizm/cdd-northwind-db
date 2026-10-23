# NorthWindReports - Reporte Power BI (PBIP/PBIR)

Reporte nativo de Power BI sobre el modelo tabular `NorthWindOLAP`, en
formato PBIP/PBIR (proyecto, sin `.pbix`). Los bindings de campos, filtros
y semánticas de consulta viven en el contrato
[report_contract.py](report_contract.py); el generador
[build_report.py](build_report.py) solo agrega formato, posiciones y
metadatos de contenedor.

## Regenerar

```
python NorthWindBI/NorthWindReports/build_report.py
```

Opciones: `--ssas-server` (por defecto `localhost`), `--ssas-database`
(por defecto `NorthWindOLAP`), `--output` (por defecto esta carpeta).
La regeneración es determinista: sobrescribe los archivos generados
conocidos, pero aborta sin escribir nada si encuentra directorios de
páginas o visuales que no espera (no borra trabajo ajeno).

## Cómo abrir

1. Desplegar y **procesar** el modelo `NorthWindOLAP` en SSAS primero (ver
   [../NorthWindOLAP/README.md](../NorthWindOLAP/README.md)); el proyecto
   llega con `DoNotProcess` por diseño.
2. Abrir `NorthWind.pbip` en Power BI Desktop moderno con soporte
   PBIP/PBIR.
3. El reporte referencia el modelo en vivo vía
   `NorthWind.SemanticModel/modelReference.json` (conexión SSAS integrada
   `Integrated Security=SSPI`). No se publica a Fabric ni a Power BI
   Service y no se exporta data de origen al proyecto.

Estado de validación: 64 pruebas offline aprobadas (contrato, mecánica
del generador y ETL). La validación de esquemas de Microsoft no se
re-ejecutó en este cambio por requerir red, y el reporte no se abrió en
Power BI Desktop para verificación de render.
Esto valida la estructura, no sustituye la apertura/renderizado en
Power BI Desktop ni la ejecución de DAX y el cuadre de importes con
datos reales en SSAS.

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
   Deploy; o la vía TMSL `createOrReplace` con `bin/NorthWind.asdatabase`
   desde una ventana XMLA de SSMS.
5. **Procesar**: SSMS > Process Database > Process Full, o TMSL
   `{"refresh":{"type":"full","objects":[{"database":"NorthWindOLAP"}]}}`.
6. **Apuntar el reporte a tu servidor** si no es `localhost`:
   `python build_report.py --ssas-server TU-SERVIDOR`
   (o editar `NorthWind.SemanticModel/modelReference.json` a mano).
7. Abrir `NorthWind.pbip` en Power BI Desktop con autenticación Windows.

Si en cambio el dashboard consume **tu** servidor SSAS, los compañeros
solo necesitan Power BI Desktop, el `modelReference.json` apuntando a tu
equipo, y permiso de lectura en el modelo (SSMS > servidor AS >
Properties > Security > agregar sus usuarios).

Validación opcional de esquemas (requiere `jsonschema` + `referencing`
instalados y red solo hacia GitHub de Microsoft; no instala nada):

```
python NorthWindBI/NorthWindReports/validate_report_schemas.py
```

## Contenido

Cinco páginas navegables por pestañas; `inicio` es la página activa al
abrir:

| Página | Título | Notas |
|---|---|---|
| `inicio` | Inicio | Menú visual: ilustración de portada + 4 tarjetas ilustradas con botón de navegación; sin KPI ni slicers |
| `panorama` | Dashboard de Ventas | 5 KPI + tendencia, categorías, top clientes/productos, tabla por país |
| `productos` | Productos y Categorías | Drillthrough visible por `Producto` |
| `clientes` | Clientes y Vendedores | Drillthrough visible por `Cliente` |
| `logistica` | Análisis de Logística y Envíos | Flete, días pedido-envío, ventas por fecha de envío |

- Los visuales usan las **medidas SSAS heredadas** del modelo; no hay DAX
  copiado en el reporte.
- Inicio es un **menú ilustrado**: cada tarjeta navega haciendo clic en
  la **imagen o en el botón** (ambos llevan `visualLink`
  PageNavigation); cada sección tiene un botón `Inicio` junto al
  encabezado para volver. En el **modo de edición** de Power BI Desktop
  los enlaces se activan con **Ctrl+clic**; en modo lectura basta un
  clic normal. La alternativa sin botones es la fila de pestañas nativa.
- Las ilustraciones son **originales y locales**: fuentes SVG editables
  en `assets/home/` y PNG empaquetados en
  `NorthWind.Report/StaticResources/RegisteredResources/`; no requieren
  red ni recursos externos (los PNG se regeneran con Chrome headless
  sobre el SVG si se edita el arte).
- Inicio no lleva slicers ni visuales de datos; los slicers de las
  secciones conservan su estado al navegar (volver a Inicio no
  restablece filtros).
- Slicers en modo lista desplegable con grupos de sincronización del
  contrato; para limpiar filtros usar el **borrador nativo del slicer**
  (icono de borrador); no existe marcador de "reset" fabricado.
- Los filtros temporales cubren fechas históricas del origen; no hay
  noción de "hoy"/fecha actual.
- Sin símbolos de moneda (origen no la identifica), sin costos, márgenes
  ni metas, y sin fecha real de entrega al cliente.

Prueba de humo sugerida en Power BI Desktop: abrir `NorthWind.pbip`
(cae en `Inicio`), visitar las cuatro secciones con los botones
(Ctrl+clic en edición), volver con el botón `Inicio` de cada página y
confirmar que datos, slicers y drillthrough siguen funcionando igual.

## Solución de problemas

- **Nombres de campos**: el contrato debe usar los mismos nombres
  semánticos que el modelo desplegado. Las columnas de `Calendario` se
  llaman `Año`, `MesAño` y `OrdenMesAño` (con ñ); si el modelo cambia,
  regenerar el reporte con `build_report.py` antes de reabrirlo.
- **Un visual muestra "Corregir esto"/"Fix this"**: suele significar que
  el reporte referencia un campo que no existe en el modelo cargado.
  Cierra y vuelve a abrir el `.pbip` actualizado (no guardes un Desktop
  con archivos viejos sobre los generados) y verifica los filtros.
- **Tendencia con un solo punto**: las tendencias agrupan por mes; con
  un solo mes seleccionado en el slicer o por filtro cruzado de otro
  visual, un punto es el comportamiento correcto. Quita la marca
  seleccionada haciendo clic en el área vacía del gráfico o con el
  borrador del slicer.
- **Los filtros persisten al navegar**: volver a `Inicio` no restablece
  slicers ni selecciones.
- Si un error persiste, usa **"Ver detalles"** en el visual afectado y
  reporta el mensaje exacto; no todos los casos fueron reproducidos.

## Archivos generados

- `NorthWind.pbip` - proyecto raíz.
- `NorthWind.Report/` - `definition.pbir` (referencia por ruta al modelo),
  `definition/report.json` (tema + paquetes de recursos),
  `definition/version.json`, `definition/pages/pages.json`,
  `definition/pages/<pagina>/page.json`,
  `definition/pages/<pagina>/visuals/<visual>/visual.json`,
  `StaticResources/RegisteredResources/NorthWind.json` (tema).
- `NorthWind.SemanticModel/` - `definition.pbism` + `modelReference.json`
  (referencia en vivo a SSAS, no un modelo importado).
- `preview-layout.js` - datos de layout generados desde el contrato
  (nombres/títulos/tipos/rects; se regenera con `build_report.py`).
- [preview.html](preview.html) - vista previa estática del diseño (sin
  datos, no es render de Power BI); se mantiene a mano y lee
  `preview-layout.js`.
