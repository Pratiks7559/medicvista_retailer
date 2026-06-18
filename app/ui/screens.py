# Legacy re-exports — kept for backward compatibility
from .dashboard_screen import DashboardScreen
from .inventory.inventory_screen import InventoryScreen
from .inventory.transaction_history_screen import TransactionHistoryScreen
from .product.product_screen import ProductScreen
from .purchase.purchase_screen import PurchaseScreen
from .purchase.reorder_level_screen import ReorderLevelScreen
from .sales.sales_screen import SalesScreen
from .reports.reports_screen import ReportsScreen
from .reports.financial_report_screen import FinancialReportScreen
from .supplier.supplier_screen import SupplierScreen
from .customer.customer_screen import CustomerScreen
from .retailer_requests.retailer_requests_screen import RetailerRequestsScreen

# Alias kept for application.py that previously imported TableScreen/SettingsScreen
TableScreen = InventoryScreen


class SettingsScreen:
    pass
