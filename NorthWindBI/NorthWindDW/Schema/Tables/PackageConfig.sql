CREATE TABLE [dbo].[PackageConfig] (
    [PackageID]      INT IDENTITY(1,1) NOT NULL,
    [TableName]      VARCHAR(50) NOT NULL,
    [LastRowVersion] BIGINT NULL,
    CONSTRAINT [PK_PackageConfig] PRIMARY KEY CLUSTERED ([PackageID] ASC)
);
GO
