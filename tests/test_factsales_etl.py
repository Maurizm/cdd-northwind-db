"""Static regression checks for the NorthWind FactSales SSIS package and its
SQL Server Agent job.  Everything here is deterministic: no SQL Server or
SSISDB instance is required to run these tests."""

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BI = ROOT / "NorthWindBI"
ETL = BI / "NorthWindETL"
DTSX = ETL / "FactSales.dtsx"
JOB = ETL / "NorthWindJob.sql"
DW_PROCS = BI / "NorthWindDW" / "Schema" / "Programmability" / "Stored Procedures"
OLTP_PROCS = BI / "NorthWindOLTP" / "Schema" / "Programmability" / "Stored Procedures"
STAGING_SQL = BI / "NorthWindDW" / "Schema" / "Tables" / "staging.sales.sql"
FACT_SQL = BI / "NorthWindDW" / "Schema" / "Tables" / "FactSales.sql"

DTS = "{www.microsoft.com/SqlServer/Dts}"
SQLTASK = "{www.microsoft.com/sqlserver/dts/tasks/sqltask}"

SOURCE_CM_GUID = "{DCCF39B1-C7D0-4756-A1CA-4D1D2D8AB8D6}"
TARGET_CM_GUID = "{57CD113C-0B40-4D11-AFD2-78210A30FCF0}"

PKG_TEXT = DTSX.read_text(encoding="utf-8")


def package_tree():
    return ET.parse(DTSX).getroot()


def executables(root):
    container = root.find(f"{DTS}Executables")
    return list(container.findall(f"{DTS}Executable"))


def columns_of(sql_path):
    """Parse the column names declared inside a CREATE TABLE script."""
    text = sql_path.read_text(encoding="utf-8")
    body = re.search(r"\((.*)\)", text, re.S).group(1)
    names = []
    for line in body.splitlines():
        line = line.strip().rstrip(",")
        match = re.match(r"\[?(\w+)\]?\s+(MONEY|money|INT|int|BIGINT|bigint|"
                         r"SMALLINT|smallint|TINYINT|tinyint|NVARCHAR|nvarchar|"
                         r"NCHAR|nchar|VARCHAR|varchar|CHAR|char|NTEXT|ntext|"
                         r"REAL|real|FLOAT|float|DECIMAL|decimal|NUMERIC|numeric|"
                         r"DATETIME|datetime|DATE|date|BIT|bit)\b", line)
        if match:
            names.append(match.group(1))
    return names


class FactSalesPackageTests(unittest.TestCase):
    def setUp(self):
        self.root = package_tree()
        self.exes = executables(self.root)

    def test_package_parses_as_xml(self):
        self.assertEqual(self.root.tag, f"{DTS}Executable")
        self.assertEqual(self.root.get(f"{DTS}ExecutableType"), "Microsoft.Package")

    def test_six_executables(self):
        self.assertEqual(len(self.exes), 6)
        names = {e.get(f"{DTS}ObjectName") for e in self.exes}
        self.assertIn("Load Sales", names)
        self.assertIn("Clean-up staging", names)

    def test_control_flow_sql(self):
        self.assertIn("TRUNCATE TABLE [staging].[sales]", PKG_TEXT)
        self.assertIn("GetDatabaseRowVersion", PKG_TEXT)
        self.assertIn("GetLastPackageRowVersion", PKG_TEXT)
        self.assertIn("'Orders'", PKG_TEXT)
        self.assertIn("DW_MergeFactSales", PKG_TEXT)
        self.assertIn("UpdateLastPackageRowVersion", PKG_TEXT)

    def test_extraction_sproc_and_params(self):
        self.assertIn("GetOrdersChangesByRowVersion", PKG_TEXT)
        self.assertIn("@startRow", PKG_TEXT)
        self.assertIn("@endRow", PKG_TEXT)

    def test_connection_managers_preserved(self):
        self.assertIn(SOURCE_CM_GUID, PKG_TEXT)
        self.assertIn(TARGET_CM_GUID, PKG_TEXT)
        self.assertIn("Source.NorthWindOLTP", PKG_TEXT)
        self.assertIn("Target.NorthWindDW", PKG_TEXT)
        self.assertIn("$Project::ServerName", PKG_TEXT)

    def test_user_variables(self):
        self.assertIn('DTS:ObjectName="dbts"', PKG_TEXT)
        self.assertIn('DTS:ObjectName="lastRowVersion"', PKG_TEXT)
        self.assertIn('DTS:DataType="20"', PKG_TEXT)

    def test_dimension_lookups(self):
        self.assertGreaterEqual(PKG_TEXT.count('componentClassID="Microsoft.Lookup"'), 6)
        for table in ("DimCustomer", "DimEmployee", "DimProduct",
                      "DimSupplier", "DimShipper"):
            self.assertIn(f"from [dbo].[{table}]", PKG_TEXT)
        for key in ("CustomerKey", "EmployeeKey", "ProductKey",
                    "SupplierKey", "ShipperKey"):
            self.assertIn(key, PKG_TEXT)

    def test_factsales_composite_lookup(self):
        """Update path requires a Lookup on (OrderID, OrderLineNum)."""
        self.assertRegex(
            PKG_TEXT,
            r"(?s)from \[dbo\]\.\[FactSales\].*\[OrderID\] = \?.*\[OrderLineNum\] = \?",
        )
        self.assertIn("Lookup No Match Output", PKG_TEXT)

    def test_destinations(self):
        self.assertIn("[staging].[sales]", PKG_TEXT)
        self.assertIn("[dbo].[FactSales]", PKG_TEXT)
        self.assertGreaterEqual(
            PKG_TEXT.count('componentClassID="Microsoft.OLEDBDestination"'), 2)

    def test_derived_measures(self):
        self.assertIn('componentClassID="Microsoft.DerivedColumn"', PKG_TEXT)
        for col in ("GrossAmount", "DiscountAmount", "NetAmount",
                    "AllocatedFreight"):
            self.assertIn(col, PKG_TEXT)
        # zero-guard on AllocatedFreight and -1 default for missing keys
        self.assertIn("NULL(DT_CY)", PKG_TEXT)
        self.assertIn("ISNULL", PKG_TEXT)

    def test_referenced_procedures_exist(self):
        procs = set(re.findall(r"EXECUTE\s*\[dbo\]\.\[(\w+)\]", PKG_TEXT))
        self.assertGreaterEqual(len(procs), 5)
        for proc in procs:
            candidates = [DW_PROCS / f"{proc}.sql", OLTP_PROCS / f"{proc}.sql"]
            self.assertTrue(
                any(c.exists() for c in candidates),
                f"{proc}.sql missing in DW and OLTP Programmability folders",
            )

    def test_parameter_mapping_binds_rowversions(self):
        self.assertIn("User::lastRowVersion", PKG_TEXT)
        self.assertIn("User::dbts", PKG_TEXT)
        self.assertRegex(PKG_TEXT, r'"@startRow:Input"')
        self.assertRegex(PKG_TEXT, r'"@endRow:Input"')


class NorthWindJobTests(unittest.TestCase):
    def setUp(self):
        self.text = JOB.read_text(encoding="utf-8")

    def test_job_named_northwindjob(self):
        self.assertRegex(self.text, r"sp_add_job\s+@job_name\s*=\s*N?'NorthWindJob'")

    def test_one_step_per_dtsx(self):
        dtsx_files = sorted(ETL.glob("*.dtsx"))
        self.assertGreaterEqual(len(dtsx_files), 2)
        steps = re.findall(r"sp_add_jobstep", self.text)
        self.assertEqual(len(steps), len(dtsx_files))
        for pkg in dtsx_files:
            self.assertIn(pkg.name, self.text, f"{pkg.name} has no job step")

    def test_factsales_last_and_dims_first(self):
        positions = {}
        for match in re.finditer(
                r"@step_id=(\d+)[^;]*?\\(\w+\.dtsx)", self.text, re.S):
            positions[int(match.group(1))] = match.group(2)
        self.assertTrue(positions, "no sp_add_jobstep commands found")
        max_step = max(positions)
        self.assertEqual(positions[max_step], "FactSales.dtsx")
        for step, pkg in positions.items():
            if pkg != "FactSales.dtsx":
                self.assertTrue(pkg.startswith("Dim"), pkg)

    def test_schedule_and_server(self):
        self.assertIn("sp_add_jobschedule", self.text)
        self.assertIn("sp_add_jobserver", self.text)
        # daily schedule (freq_type=4) starting at 02:00
        self.assertIn("@freq_type=4", self.text)
        self.assertIn("@active_start_time=20000", self.text)

    def test_failure_stops_job(self):
        for match in re.finditer(
                r"sp_add_jobstep[^;]*@on_fail_action=(\d+)", self.text, re.S):
            self.assertEqual(match.group(1), "2")


class StagingSchemaTests(unittest.TestCase):
    def test_staging_columns_subset_of_fact(self):
        staging_cols = set(columns_of(STAGING_SQL))
        fact_cols = columns_of(FACT_SQL)
        self.assertIn("SalesKey", fact_cols)  # identity column sanity check
        non_identity = set(fact_cols) - {"SalesKey"}
        self.assertTrue(staging_cols <= non_identity,
                        staging_cols - non_identity)


if __name__ == "__main__":
    unittest.main()
