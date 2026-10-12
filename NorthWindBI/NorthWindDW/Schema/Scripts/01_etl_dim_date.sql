/* Genera el calendario + el miembro desconocido (clave -1).
   Ancla 2000-01-03 (fue LUNES); módulo normalizado para fechas previas al ancla.
   WeekOfYear usa ISO_WEEK (independiente de SET DATEFIRST). */
PRINT 'Cargando DimDate (1995-2030)...';
SET NOCOUNT ON;

;WITH Fechas AS
(
    SELECT CAST('1995-01-01' AS DATE) AS Fecha
    UNION ALL
    SELECT DATEADD(DAY, 1, Fecha) FROM Fechas WHERE Fecha < '2030-12-31'
),
Calculo AS
(
    SELECT f.Fecha,
           ((DATEDIFF(DAY, '2000-01-03', f.Fecha) % 7) + 7) % 7 AS DOW  -- 0=Lunes ... 6=Domingo
    FROM Fechas f
)
INSERT INTO [dbo].[DimDate]
    ([DateKey], [FullDate], [DayOfMonth], [DayOfWeekNum], [DayName], [WeekOfYear],
     [MonthNum], [MonthName], [QuarterNum], [SemesterNum], [YearNum], [IsWeekend])
SELECT
    CAST(CONVERT(CHAR(8), c.Fecha, 112) AS INT),
    c.Fecha,
    DAY(c.Fecha),
    c.DOW + 1,
    CHOOSE(c.DOW + 1, N'Lunes',N'Martes',N'Miércoles',N'Jueves',N'Viernes',N'Sábado',N'Domingo'),
    DATEPART(ISO_WEEK, c.Fecha),
    MONTH(c.Fecha),
    CHOOSE(MONTH(c.Fecha), N'Enero',N'Febrero',N'Marzo',N'Abril',N'Mayo',N'Junio',
           N'Julio',N'Agosto',N'Septiembre',N'Octubre',N'Noviembre',N'Diciembre'),
    DATEPART(QUARTER, c.Fecha),
    CASE WHEN MONTH(c.Fecha) <= 6 THEN 1 ELSE 2 END,
    YEAR(c.Fecha),
    CASE WHEN c.DOW >= 5 THEN 1 ELSE 0 END
FROM Calculo c
OPTION (MAXRECURSION 0);

-- Miembro desconocido (clave -1) para fechas nulas del OLTP
INSERT INTO [dbo].[DimDate]
    ([DateKey], [FullDate], [DayOfMonth], [DayOfWeekNum], [DayName], [WeekOfYear],
     [MonthNum], [MonthName], [QuarterNum], [SemesterNum], [YearNum], [IsWeekend])
VALUES (-1, '1900-01-01', 1, 1, N'Desconocido', 1, 1, N'Desconocido', 1, 1, 1900, 0);

-- Sanity check: esperado -> Domingo, Lunes, Viernes, Jueves, Domingo
SELECT FullDate, DayName FROM [dbo].[DimDate]
WHERE FullDate IN ('1996-05-12','2000-01-03','2008-02-29','2026-09-10','1995-01-01');