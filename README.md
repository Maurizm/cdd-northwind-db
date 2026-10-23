# Participantes del grupo

Integrantes:

1. García Rojas Lizeth
2. Mérida Ojalvo Daniel Fernando
3. Moya Cardona William
4. Zambrana Revollo Samantha
5. Zurita Mendoza José Mauricio

## Modelo OLAP y reporte Power BI

- Modelo tabular SSAS: [NorthWindOLAP/README.md](NorthWindBI/NorthWindOLAP/README.md)
- Reporte Power BI (PBIP/PBIR): [NorthWindReports/README.md](NorthWindBI/NorthWindReports/README.md)

Generar artefactos:

```
python NorthWindBI/NorthWindOLAP/build_model.py
python NorthWindBI/NorthWindReports/build_report.py
```

Pruebas:

```
python -m unittest discover -s tests -v
```

Solución actual: `NorthWindBI/NorthWindBI.slnx` (el `.sln` heredado queda
sin cambios).

**Advertencia: compilar solo `NorthWindOLAP`. No desplegar la solución
completa, porque el script postdeploy original de `NorthWindDW` limpia y
recarga el DW.**
