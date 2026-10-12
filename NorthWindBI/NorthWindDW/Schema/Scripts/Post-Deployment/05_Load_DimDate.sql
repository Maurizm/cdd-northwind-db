PRINT 'Cargando DimDate...';

DELETE FROM [dbo].[DimDate];

DECLARE @StartDate DATE = '1996-01-01';
DECLARE @EndDate   DATE = '1998-12-31';

;WITH DateRange AS (
    SELECT @StartDate AS FullDate
    UNION ALL
    SELECT DATEADD(DAY, 1, FullDate)
    FROM DateRange
    WHERE FullDate < @EndDate
)
INSERT INTO [dbo].[DimDate]
    ([DateKey], [FullDate], [DateName], [DayOfWeek], [DayName],
     [DayOfMonth], [DayOfYear], [WeekOfYear], [MonthName],
     [MonthOfYear], [Quarter], [QuarterName], [Year], [IsWeekend])
SELECT 
    CONVERT(INT, CONVERT(VARCHAR(8), FullDate, 112)) AS DateKey,
    FullDate,
    CONVERT(NVARCHAR(30), FullDate, 109) AS DateName,
    DATEPART(WEEKDAY, FullDate) AS DayOfWeek,
    DATENAME(WEEKDAY, FullDate) AS DayName,
    DATEPART(DAY, FullDate) AS DayOfMonth,
    DATEPART(DAYOFYEAR, FullDate) AS DayOfYear,
    DATEPART(WEEK, FullDate) AS WeekOfYear,
    DATENAME(MONTH, FullDate) AS MonthName,
    DATEPART(MONTH, FullDate) AS MonthOfYear,
    DATEPART(QUARTER, FullDate) AS Quarter,
    'Q' + CAST(DATEPART(QUARTER, FullDate) AS VARCHAR(1)) AS QuarterName,
    DATEPART(YEAR, FullDate) AS Year,
    CASE WHEN DATEPART(WEEKDAY, FullDate) IN (1,7) THEN 1 ELSE 0 END AS IsWeekend
FROM DateRange
OPTION (MAXRECURSION 3000);

PRINT 'DimDate cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';