USE NorthWindDW;
GO
IF OBJECT_ID('dbo.DimDate','U') IS NULL
BEGIN
    CREATE TABLE dbo.DimDate
    (
        DateKey       int          NOT NULL PRIMARY KEY, -- formato AAAAMMDD; 0 = desconocida
        FullDate      date         NULL,
        [Day]         tinyint      NULL,
        [Month]       tinyint      NULL,
        MonthName     nvarchar(20) NULL,
        [Quarter]     tinyint      NULL,
        [Year]        smallint     NULL,
        WeekOfYear    tinyint      NULL,
        DayOfWeek     tinyint      NULL,
        DayName       nvarchar(20) NULL,
        IsWeekend     bit          NULL
    );
END;
GO
IF NOT EXISTS (SELECT 1 FROM dbo.DimDate WHERE DateKey = 0)
    INSERT dbo.DimDate(DateKey, FullDate) VALUES (0, NULL);
GO
