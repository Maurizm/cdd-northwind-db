USE NorthWindDW;
GO
IF OBJECT_ID('dbo.DimCustomer','U') IS NULL
BEGIN
    CREATE TABLE dbo.DimCustomer
    (
        CustomerKey       int IDENTITY(1,1) NOT NULL CONSTRAINT PK_DimCustomer PRIMARY KEY,
        CustomerID        nchar(5) NOT NULL, -- clave natural del OLTP
        CompanyName       nvarchar(40) NOT NULL,
        ContactName       nvarchar(30) NULL,
        ContactTitle      nvarchar(30) NULL,
        Address           nvarchar(60) NULL,
        City              nvarchar(15) NULL,
        Region            nvarchar(15) NULL,
        PostalCode        nvarchar(10) NULL,
        Country           nvarchar(15) NULL,
        Phone             nvarchar(24) NULL,
        Fax               nvarchar(24) NULL,
        ValidFrom         datetime2(0) NOT NULL CONSTRAINT DF_DimCustomer_ValidFrom DEFAULT SYSUTCDATETIME(),
        ValidTo           datetime2(0) NOT NULL CONSTRAINT DF_DimCustomer_ValidTo DEFAULT ('9999-12-31 23:59:59'),
        IsCurrent         bit NOT NULL CONSTRAINT DF_DimCustomer_IsCurrent DEFAULT (1),
        CONSTRAINT CK_DimCustomer_Validity CHECK (ValidFrom < ValidTo)
    );
    CREATE INDEX IX_DimCustomer_NaturalCurrent
        ON dbo.DimCustomer(CustomerID, IsCurrent);
END;
GO
