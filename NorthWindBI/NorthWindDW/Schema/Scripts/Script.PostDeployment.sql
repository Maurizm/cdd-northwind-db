/*
 Post-Deployment Script — NorthWindDW
 ETL desde la BD OLTP. Requiere que el OLTP esté publicado y poblado
 EN LA MISMA INSTANCIA antes de publicar este proyecto.
*/
-- ⚠ BD OLTP de origen: cámbiala aquí si tu OLTP se llama distinto:
:setvar OLTP_DB "NorthWindOLTP"

:r .\clean_dw.data.sql
:r .\01_etl_dim_date.sql
:r .\02_etl_dimensions.sql
:r .\03_etl_fact.sql
-- 04_analitica.sql es para ejecutar manualmente en SSMS; NO se incluye en el deploy:
-- :r .\04_analitica.sql

PRINT 'Validación del ETL (ambos valores deben coincidir):';
SELECT (SELECT COUNT(*) FROM [$(OLTP_DB)].dbo.OrderDetails) AS LineasOLTP,
       (SELECT COUNT(*) FROM dbo.FactSales)                AS LineasDW;