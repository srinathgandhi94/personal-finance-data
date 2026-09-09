SELECT DATE_PART('year', t."Date"), DATE_PART('month', "Date"), p."Category", SUM(t."Units"), SUM(t."Amount")
from ods."Transactions" t
join ods."Portfolio" p on t."TickerCode" = p."TickerCode"
and t."Action" = 'Buy'
GROUP BY DATE_PART('year', t."Date"), DATE_PART('month', t."Date"), p."Category"
ORDER by 1, 2, 3;

SELECT p."ScripName", p."Category"
, SUM(CASE WHEN t."Action" = 'Buy' THEN t."PrincipalAmount" ELSE t."PrincipalAmount" * -1 END)
, SUM(CASE WHEN t."Action" = 'Buy' THEN t."TransactionPrincipalAmount" ELSE t."TransactionPrincipalAmount" * -1 END)
, SUM(CASE WHEN t."Action" = 'Buy' THEN t."Units" ELSE t."Units" * -1 END)
from ods."Transactions" t
join ods."Portfolio" p on t."TickerCode" = p."TickerCode"
where p."Category" IN ('Stocks', 'ETF')
and t."Platform" = 'NJ India'
GROUP BY p."Category", p."ScripName"
ORDER by 1, 2

SELECT SUM(CASE WHEN t."Action" = 'Buy' THEN t."PrincipalAmount" ELSE t."PrincipalAmount" * -1 END)
, SUM(CASE WHEN t."Action" = 'Buy' THEN t."TransactionPrincipalAmount" ELSE t."TransactionPrincipalAmount" * -1 END)
from ods."Transactions" t
join ods."Portfolio" p on t."TickerCode" = p."TickerCode"
where p."Category" IN ('Stocks', 'ETF')
and t."Platform" = 'NJ India'
ORDER by 1;

-- Create the ods.ExpenseManager table
-- Source: Wallet Report.xlsx (personal expense tracker export)
-- Load strategy: truncate-and-load (no natural unique key exists in the source data)
CREATE TABLE ods."ExpenseManager" (
    "ExpenseId" SERIAL PRIMARY KEY,
    "Account" TEXT,
    "Category" TEXT,
    "Currency" TEXT,
    "Amount" NUMERIC,
    "RefCurrencyAmount" NUMERIC,
    "Type" TEXT,
    "PaymentType" TEXT,
    "PaymentTypeLocal" TEXT,
    "Note" TEXT,
    "Date" TIMESTAMP,
    "GpsLatitude" NUMERIC,
    "GpsLongitude" NUMERIC,
    "GpsAccuracyInMeters" NUMERIC,
    "WarrantyInMonth" INTEGER,
    "Transfer" BOOLEAN,
    "Payee" TEXT,
    "Labels" TEXT,
    "EnvelopeId" TEXT,
    "CustomCategory" BOOLEAN,
    "CreateTS" TIMESTAMP DEFAULT NOW(),
    "ModifyTS" TIMESTAMP DEFAULT NOW()
);