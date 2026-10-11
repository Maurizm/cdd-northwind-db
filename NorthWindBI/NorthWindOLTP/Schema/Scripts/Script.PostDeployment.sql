/*
 Post-Deployment Script — NorthWindOLTP
 Carga de datos en orden de dependencias FK (padres primero).
 clean.data.sql hace que el despliegue sea repetible.
*/
:r .\clean.data.sql
:r .\region.data.sql
:r .\territories.data.sql
:r .\categories.data.sql
:r .\suppliers.data.sql
:r .\shippers.data.sql
:r .\employees.data.sql
:r .\employee_territories.data.sql
:r .\customers.data.sql
:r .\customer_demographics.data.sql
:r .\customer_customer_demo.data.sql
:r .\products.data.sql
:r .\orders.data.sql
:r .\order_details.data.sql

PRINT 'Carga de NorthWind completada.';