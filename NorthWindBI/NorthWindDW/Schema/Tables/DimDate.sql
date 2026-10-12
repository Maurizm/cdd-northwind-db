CREATE TABLE [dbo].[DimDate]
(
    [DateKey] [int] NOT NULL,
    [FullDate] [date] NOT NULL,
    [DayOfMonth] [tinyint] NOT NULL,
    [DayOfWeekNum] [tinyint] NOT NULL,
    [DayName] [nvarchar](15) NOT NULL,
    [WeekOfYear] [tinyint] NOT NULL,
    [MonthNum] [tinyint] NOT NULL,
    [MonthName] [nvarchar](15) NOT NULL,
    [QuarterNum] [tinyint] NOT NULL,
    [SemesterNum] [tinyint] NOT NULL,
    [YearNum] [smallint] NOT NULL,
    [IsWeekend] [bit] NOT NULL,
    CONSTRAINT [PK_DimDate] PRIMARY KEY CLUSTERED ([DateKey] ASC)
);