CREATE TABLE [staging].[sales]
(
    [OrderID]           INT      NOT NULL,
    [OrderLineNum]      SMALLINT NOT NULL,
    [OrderDateKey]      INT      NOT NULL,
    [RequiredDateKey]   INT      NOT NULL,
    [ShippedDateKey]    INT      NOT NULL,
    [CustomerKey]       INT      NOT NULL,
    [EmployeeKey]       INT      NOT NULL,
    [ProductKey]        INT      NOT NULL,
    [SupplierKey]       INT      NOT NULL,
    [ShipperKey]        INT      NOT NULL,
    [Quantity]          SMALLINT NOT NULL,
    [UnitPrice]         MONEY    NOT NULL,
    [Discount]          REAL     NOT NULL,
    [GrossAmount]       MONEY    NOT NULL,
    [DiscountAmount]    MONEY    NOT NULL,
    [NetAmount]         MONEY    NOT NULL,
    [Freight]           MONEY    NULL,
    [AllocatedFreight]  MONEY    NULL
);
GO
