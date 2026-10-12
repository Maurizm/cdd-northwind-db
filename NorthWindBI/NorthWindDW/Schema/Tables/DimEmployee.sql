CREATE TABLE [dbo].[DimEmployee] (
    [EmployeeKey]       INT IDENTITY(1,1) NOT NULL,
    [EmployeeID]        INT NOT NULL,
    [FullName]          NVARCHAR(35) NOT NULL,
    [LastName]          NVARCHAR(20) NOT NULL,
    [FirstName]         NVARCHAR(10) NOT NULL,
    [Title]             NVARCHAR(30) NULL,
    [TitleOfCourtesy]   NVARCHAR(25) NULL,
    [BirthDate]         DATE NULL,
    [HireDate]          DATE NULL,
    [Address]           NVARCHAR(60) NULL,
    [City]              NVARCHAR(15) NULL,
    [Region]            NVARCHAR(15) NULL,
    [PostalCode]        NVARCHAR(10) NULL,
    [Country]           NVARCHAR(15) NULL,
    [HomePhone]         NVARCHAR(24) NULL,
    [Extension]         NVARCHAR(4) NULL,
    [ManagerName]       NVARCHAR(35) NULL,
    [TerritoriesDesc]   NVARCHAR(MAX) NULL,
    [RegionDesc]        NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_DimEmployee] PRIMARY KEY CLUSTERED ([EmployeeKey] ASC)
);
GO

CREATE NONCLUSTERED INDEX [IX_DimEmployee_ID] ON [dbo].[DimEmployee] ([EmployeeID] ASC);
GO
