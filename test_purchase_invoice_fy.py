from app.db import Database


class DummyConfig:
    retailer_id = 1


class DummyDB(Database):
    def __init__(self):
        super().__init__(DummyConfig())
        self.rows = []

    def _ensure_invoice_financial_year_schema(self):
        pass

    def query(self, sql, params=()):
        return list(self.rows)


def test_allows_same_invoice_in_different_fy():
    db = DummyDB()
    db.rows = [
        {"invoice_no": "122", "supplierid_id": 5, "retailer_id": 1, "invoice_financial_year": "2025-26", "invoice_date": "2025-06-15"},
    ]

    assert db.invoice_number_exists_for_supplier_fy("122", 5, "2026-04-10") is False


def test_rejects_duplicate_invoice_in_same_fy():
    db = DummyDB()
    db.rows = [
        {"invoice_no": "122", "supplierid_id": 5, "retailer_id": 1, "invoice_financial_year": "2025-26", "invoice_date": "2025-06-15"},
    ]

    assert db.invoice_number_exists_for_supplier_fy("122", 5, "2025-06-20") is True


def test_invoice_financial_year_is_saved_as_readable_label():
    assert Database._invoice_financial_year("2026-04-01") == "2026-27"
    assert Database._invoice_financial_year("2026-03-31") == "2025-26"
