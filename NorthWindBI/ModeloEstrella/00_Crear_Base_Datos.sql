/*
Objeto: Base de datos dimensional NorthWindDW
Ejecutar con permisos para crear bases de datos.
La base transaccional de origen debe existir como NorthWind.
*/
IF DB_ID(N'NorthWindDW') IS NULL
    CREATE DATABASE NorthWindDW;
GO
USE NorthWindDW;
GO
