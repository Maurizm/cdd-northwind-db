PRINT 'Sembrando PackageConfig...';
SET NOCOUNT ON;

IF NOT EXISTS(SELECT TOP(1) 1 FROM [dbo].[PackageConfig] WHERE [TableName] = 'Customer')
    INSERT [dbo].[PackageConfig] ([TableName], [LastRowVersion]) VALUES ('Customer', 0);
GO
IF NOT EXISTS(SELECT TOP(1) 1 FROM [dbo].[PackageConfig] WHERE [TableName] = 'Employee')
    INSERT [dbo].[PackageConfig] ([TableName], [LastRowVersion]) VALUES ('Employee', 0);
GO
IF NOT EXISTS(SELECT TOP(1) 1 FROM [dbo].[PackageConfig] WHERE [TableName] = 'Product')
    INSERT [dbo].[PackageConfig] ([TableName], [LastRowVersion]) VALUES ('Product', 0);
GO
IF NOT EXISTS(SELECT TOP(1) 1 FROM [dbo].[PackageConfig] WHERE [TableName] = 'Supplier')
    INSERT [dbo].[PackageConfig] ([TableName], [LastRowVersion]) VALUES ('Supplier', 0);
GO
IF NOT EXISTS(SELECT TOP(1) 1 FROM [dbo].[PackageConfig] WHERE [TableName] = 'Shipper')
    INSERT [dbo].[PackageConfig] ([TableName], [LastRowVersion]) VALUES ('Shipper', 0);
GO
IF NOT EXISTS(SELECT TOP(1) 1 FROM [dbo].[PackageConfig] WHERE [TableName] = 'Orders')
    INSERT [dbo].[PackageConfig] ([TableName], [LastRowVersion]) VALUES ('Orders', 0);
GO
