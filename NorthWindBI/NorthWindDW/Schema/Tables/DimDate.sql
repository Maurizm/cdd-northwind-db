CREATE TABLE [dbo].[DimDate] (
    [DateKey]           INT NOT NULL,
    [FullDate]          DATE NOT NULL,
    [DayOfMonth]        TINYINT NOT NULL,
    [DayName]           NVARCHAR(15) NOT NULL,
    [DayOfWeek]         TINYINT NOT NULL,
    [DayOfYear]         SMALLINT NOT NULL,
    [WeekOfYear]        TINYINT NOT NULL,
    [MonthOfYear]       TINYINT NOT NULL,
    [MonthName]         NVARCHAR(15) NOT NULL,
    [Quarter]           TINYINT NOT NULL,
    [QuarterName]       NVARCHAR(10) NOT NULL,
    [Year]              SMALLINT NOT NULL,
    [IsWeekend]         BIT NOT NULL,
    CONSTRAINT [PK_DimDate] PRIMARY KEY CLUSTERED ([DateKey] ASC)
);
GO
