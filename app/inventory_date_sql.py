def transaction_document_date_sql(alias: str) -> str:
    return f"""CASE
        WHEN {alias}.transaction_type IN (
            'PURCHASE', 'REVERT_PURCHASE', 'SALE', 'REVERT_SALE',
            'PURCHASE_RETURN', 'REVERT_PURCHASE_RETURN',
            'SALES_RETURN', 'REVERT_SALES_RETURN'
        ) THEN {alias}.invoice_date
        ELSE {alias}.transaction_date
    END"""


def transaction_document_date_filter(alias: str) -> str:
    return f" AND DATE({transaction_document_date_sql(alias)}) BETWEEN %s AND %s"
