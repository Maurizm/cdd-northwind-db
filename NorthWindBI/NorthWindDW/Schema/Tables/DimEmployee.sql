CREATE TABLE [dbo].[DimEmployee]
(
    [EmployeeKey] [int] IDENTITY(1,1) NOT NULL,
    [EmployeeCode] [int] NOT NULL,
    [FullName] [nvarchar](31) NOT NULL,
    [Title] [nvarchar](30) NULL,
    [City] [nvarchar](15) NULL,
    [Country] [nvarchar](15) NULL,
    [HireFullDate] [date] NULL,
    [ManagerName] [nvarchar](31) NULL,
    CONSTRAINT [PK_DimEmployee] PRIMARY KEY CLUSTERED ([EmployeeKey] ASC)
);
GO
CREATE UNIQUE NONCLUSTERED INDEX [IX_DimEmployee_Code] ON [dbo].[DimEmployee] ([EmployeeCode] ASC);