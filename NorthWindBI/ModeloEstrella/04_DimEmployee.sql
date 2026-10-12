USE NorthWindDW;
GO
IF OBJECT_ID('dbo.DimEmployee','U') IS NULL
BEGIN
    CREATE TABLE dbo.DimEmployee
    (
        EmployeeKey       int IDENTITY(1,1) NOT NULL CONSTRAINT PK_DimEmployee PRIMARY KEY,
        EmployeeID        int NOT NULL,
        FirstName         nvarchar(10) NOT NULL,
        LastName          nvarchar(20) NOT NULL,
        FullName          nvarchar(31) NOT NULL,
        Title             nvarchar(30) NULL,
        TitleOfCourtesy   nvarchar(25) NULL,
        HireDate          date NULL,
        City              nvarchar(15) NULL,
        Region            nvarchar(15) NULL,
        PostalCode        nvarchar(10) NULL,
        Country           nvarchar(15) NULL,
        ReportsToEmployeeID int NULL,
        ValidFrom         datetime2(0) NOT NULL CONSTRAINT DF_DimEmployee_ValidFrom DEFAULT SYSUTCDATETIME(),
        ValidTo           datetime2(0) NOT NULL CONSTRAINT DF_DimEmployee_ValidTo DEFAULT ('9999-12-31 23:59:59'),
        IsCurrent         bit NOT NULL CONSTRAINT DF_DimEmployee_IsCurrent DEFAULT (1),
        CONSTRAINT CK_DimEmployee_Validity CHECK (ValidFrom < ValidTo)
    );
    CREATE INDEX IX_DimEmployee_NaturalCurrent
        ON dbo.DimEmployee(EmployeeID, IsCurrent);
END;
GO
