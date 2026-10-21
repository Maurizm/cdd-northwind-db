CREATE TABLE [dbo].[DimGeography] (
    [GeographyKey]  INT IDENTITY(1,1) NOT NULL,
    [City]          NVARCHAR(15) NOT NULL,
    [Region]        NVARCHAR(15) NOT NULL,
    [Country]       NVARCHAR(15) NOT NULL,
    CONSTRAINT [PK_DimGeography] PRIMARY KEY CLUSTERED ([GeographyKey] ASC)
);
GO

CREATE UNIQUE NONCLUSTERED INDEX [UX_DimGeography_NaturalKey]
    ON [dbo].[DimGeography] ([Country] ASC, [Region] ASC, [City] ASC);
GO
