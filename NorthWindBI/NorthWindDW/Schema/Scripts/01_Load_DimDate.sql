PRINT 'Cargando DimDate...';
SET NOCOUNT ON;

-- 1. Registro desconocido (-1) para fechas nulas o no aplicables
INSERT INTO [dbo].[DimDate] (
    [DateKey], [FullDate], [DayOfMonth], [DayName], [DayOfWeek],
    [DayOfYear], [WeekOfYear], [MonthOfYear], [MonthName],
    [Quarter], [QuarterName], [Year], [IsWeekend]
)
VALUES (
    -1, '1900-01-01', 0, N'Desconocido', 0,
    0, 0, 0, N'Desconocido',
    0, N'N/A', 1900, 0
);

-- 2. Generación del rango de fechas (1996 al 1999)
DECLARE @StartDate DATE = '1996-01-01';
DECLARE @EndDate   DATE = '1999-12-31';

;WITH DateSeries AS (
    SELECT @StartDate AS CurrentDate
    UNION ALL
    SELECT DATEADD(DAY, 1, CurrentDate)
    FROM DateSeries
    WHERE CurrentDate < @EndDate
)
INSERT INTO [dbo].[DimDate] (
    [DateKey],
    [FullDate],
    [DayOfMonth],
    [DayName],
    [DayOfWeek],
    [DayOfYear],
    [WeekOfYear],
    [MonthOfYear],
    [MonthName],
    [Quarter],
    [QuarterName],
    [Year],
    [IsWeekend]
)
SELECT
    CONVERT(INT, CONVERT(VARCHAR(8), CurrentDate, 112)) AS DateKey,
    CurrentDate AS FullDate,
    DATEPART(DAY, CurrentDate) AS DayOfMonth,
    CASE DATEPART(WEEKDAY, CurrentDate)
        WHEN 1 THEN N'Domingo'
        WHEN 2 THEN N'Lunes'
        WHEN 3 THEN N'Martes'
        WHEN 4 THEN N'Miércoles'
        WHEN 5 THEN N'Jueves'
        WHEN 6 THEN N'Viernes'
        WHEN 7 THEN N'Sábado'
    END AS DayName,
    DATEPART(WEEKDAY, CurrentDate) AS DayOfWeek,
    DATEPART(DAYOFYEAR, CurrentDate) AS DayOfYear,
    DATEPART(WEEK, CurrentDate) AS WeekOfYear,
    DATEPART(MONTH, CurrentDate) AS MonthOfYear,
    CASE DATEPART(MONTH, CurrentDate)
        WHEN 1 THEN N'Enero'
        WHEN 2 THEN N'Febrero'
        WHEN 3 THEN N'Marzo'
        WHEN 4 THEN N'Abril'
        WHEN 5 THEN N'Mayo'
        WHEN 6 THEN N'Junio'
        WHEN 7 THEN N'Julio'
        WHEN 8 THEN N'Agosto'
        WHEN 9 THEN N'Septiembre'
        WHEN 10 THEN N'Octubre'
        WHEN 11 THEN N'Noviembre'
        WHEN 12 THEN N'Diciembre'
    END AS MonthName,
    DATEPART(QUARTER, CurrentDate) AS Quarter,
    CONCAT(N'T', DATEPART(QUARTER, CurrentDate)) AS QuarterName,
    DATEPART(YEAR, CurrentDate) AS Year,
    CASE WHEN DATEPART(WEEKDAY, CurrentDate) IN (1, 7) THEN 1 ELSE 0 END AS IsWeekend
FROM DateSeries
OPTION (MAXRECURSION 2000);

PRINT 'DimDate cargada exitosamente: ' + CAST(@@ROWCOUNT + 1 AS VARCHAR) + ' registros.';
GO
