CREATE TABLE [dbo].[DimEmployee](
    [EmployeeKey]       INT IDENTITY(1,1) NOT NULL,
    [EmployeeID]        INT NOT NULL,
    [FullName]          NVARCHAR(31) NOT NULL,
    [LastName]          NVARCHAR(20) NOT NULL,
    [FirstName]         NVARCHAR(10) NOT NULL,
    [Title]             NVARCHAR(30) NULL,
    [TitleOfCourtesy]   NVARCHAR(25) NULL,
    [BirthDate]         DATETIME NULL,
    [HireDate]          DATETIME NULL,
    [Address]           NVARCHAR(60) NULL,
    [City]              NVARCHAR(15) NULL,
    [Region]            NVARCHAR(15) NULL,
    [PostalCode]        NVARCHAR(10) NULL,
    [Country]           NVARCHAR(15) NULL,
    [HomePhone]         NVARCHAR(24) NULL,
    [Extension]         NVARCHAR(4) NULL,
    [TerritoryDesc]     NVARCHAR(MAX) NULL,     -- ✅ CAMBIADO a MAX
    [RegionDesc]        NVARCHAR(MAX) NULL,     -- ✅ CAMBIADO a MAX
    [EffectiveDate]     DATETIME NOT NULL DEFAULT GETDATE(),
    [ExpirationDate]    DATETIME NULL,
    [IsCurrent]         BIT NOT NULL DEFAULT 1,
    CONSTRAINT [PK_DimEmployee] PRIMARY KEY CLUSTERED ([EmployeeKey] ASC)
);
GO

CREATE UNIQUE NONCLUSTERED INDEX [IX_DimEmployee_EmployeeID] 
    ON [dbo].[DimEmployee] ([EmployeeID]) WHERE [IsCurrent] = 1;
GO