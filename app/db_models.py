# E:/akhiri_final_project/final_smart_medicvista_erp/Medicvist_retailer/app/db_models.py

import datetime
from decimal import Decimal

# Base class for all models (can be extended with ORM-specific features later)
class BaseModel:
    """
    A base class for database models.
    In a real application, this would integrate with an ORM like SQLAlchemy.
    """
    def __repr__(self):
        # Generic representation for debugging
        attrs = ', '.join(f"{k}={getattr(self, k)!r}" for k in self.__dict__ if not k.startswith('_'))
        return f"{self.__class__.__name__}({attrs})"

# --- User and Pharmacy Management ---

class WebUser(BaseModel):
    """
    Corresponds to Django's Web_User model (AbstractUser).
    Represents users of the system.
    """
    def __init__(self, id=None, username=None, password=None, user_type=None, user_contact=None,
                 path=None, profile_picture=None, user_isactive=0,
                 last_login=None, is_superuser=False, first_name='', last_name='',
                 email='', is_staff=False, is_active=True, date_joined=None):
        self.id = id  # INTEGER PRIMARY KEY AUTOINCREMENT
        self.username = username  # VARCHAR(150) NOT NULL UNIQUE
        self.password = password  # VARCHAR(128) NOT NULL (hashed password)
        self.user_type = user_type  # VARCHAR(50) NOT NULL
        self.user_contact = user_contact  # VARCHAR(100) NOT NULL
        self.path = path  # VARCHAR(100) (ImageField path)
        self.profile_picture = profile_picture  # VARCHAR(100) (ImageField path)
        self.user_isactive = user_isactive  # TINYINT(1) NOT NULL DEFAULT 0

        # Fields from AbstractUser (can be simplified if not all are needed for Tkinter app)
        self.last_login = last_login  # DATETIME(6)
        self.is_superuser = is_superuser  # TINYINT(1) NOT NULL
        self.first_name = first_name  # VARCHAR(150) NOT NULL
        self.last_name = last_name  # VARCHAR(150) NOT NULL
        self.email = email  # VARCHAR(254) NOT NULL
        self.is_staff = is_staff  # TINYINT(1) NOT NULL
        self.is_active = is_active  # TINYINT(1) NOT NULL
        self.date_joined = date_joined if date_joined is not None else datetime.datetime.now() # DATETIME(6) NOT NULL

class PharmacyDetails(BaseModel):
    """
    Corresponds to Django's Pharmacy_Details model.
    Stores general pharmacy information.
    """
    def __init__(self, id=None, pharmaname=None, pharmaweburl=None, proprietorname=None,
                 proprietorcontact=None, proprietoremail=None):
        self.id = id  # INTEGER PRIMARY KEY AUTOINCREMENT
        self.pharmaname = pharmaname  # VARCHAR(300) NOT NULL
        self.pharmaweburl = pharmaweburl  # VARCHAR(150) NOT NULL
        self.proprietorname = proprietorname  # VARCHAR(100) NOT NULL
        self.proprietorcontact = proprietorcontact  # VARCHAR(12) NOT NULL
        self.proprietoremail = proprietoremail  # VARCHAR(100) NOT NULL

class Retailer(BaseModel):
    """
    Corresponds to Django's Retailer model.
    Represents individual retailer entities.
    """
    def __init__(self, retailer_id=None, retailer_name=None, store_code=None, address='',
                 contact='', is_active=True, created_at=None, updated_at=None):
        self.retailer_id = retailer_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_name = retailer_name  # VARCHAR(200) NOT NULL
        self.store_code = store_code  # VARCHAR(50) NOT NULL UNIQUE
        self.address = address  # LONGTEXT DEFAULT ''
        self.contact = contact  # VARCHAR(20) DEFAULT ''
        self.is_active = is_active  # TINYINT(1) NOT NULL DEFAULT 1
        self.created_at = created_at if created_at is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.updated_at = updated_at if updated_at is not None else datetime.datetime.now() # DATETIME(6) NOT NULL (auto_now)

class RetailerRequest(BaseModel):
    """
    Corresponds to Django's RetailerRequest model.
    Manages requests from retailers (e.g., stock, purchase, sale).
    """
    REQUEST_TYPES = ['STOCK', 'PURCHASE', 'SALE']
    STATUS_CHOICES = ['Pending', 'Processed', 'Failed']

    def __init__(self, id=None, retailer_id=None, request_type=None, reference_id=None,
                 status='Pending', created_at=None, processed_at=None, remarks=''):
        self.id = id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT NOT NULL (FK to Retailer)
        self.request_type = request_type  # VARCHAR(20) NOT NULL (choices)
        self.reference_id = reference_id  # BIGINT
        self.status = status  # VARCHAR(20) NOT NULL DEFAULT 'Pending' (choices)
        self.created_at = created_at if created_at is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.processed_at = processed_at  # DATETIME(6)
        self.remarks = remarks  # LONGTEXT DEFAULT ''

# --- Product Management ---

class ProductMaster(BaseModel):
    """
    Corresponds to Django's ProductMaster model.
    Stores details about each product.
    """
    def __init__(self, productid=None, product_name=None, product_company=None,
                 product_packing=None, product_image='images/medicine_default.png',
                 product_salt=None, product_category=None, product_hsn=None,
                 product_hsn_percent=None, product_barcode=None):
        self.productid = productid  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.product_name = product_name  # VARCHAR(200) NOT NULL
        self.product_company = product_company  # VARCHAR(200) NOT NULL
        self.product_packing = product_packing  # VARCHAR(20) NOT NULL
        self.product_image = product_image  # VARCHAR(100) DEFAULT 'images/medicine_default.png'
        self.product_salt = product_salt  # VARCHAR(300)
        self.product_category = product_category  # VARCHAR(30)
        self.product_hsn = product_hsn  # VARCHAR(20)
        self.product_hsn_percent = product_hsn_percent  # VARCHAR(20)
        self.product_barcode = product_barcode  # VARCHAR(50) UNIQUE

# --- Supplier and Customer Management ---

class SupplierMaster(BaseModel):
    """
    Corresponds to Django's SupplierMaster model.
    Stores details about product suppliers.
    """
    def __init__(self, supplierid=None, supplier_name=None, supplier_type='',
                 supplier_address='', supplier_mobile=None, supplier_whatsapp='',
                 supplier_emailid='', supplier_spoc='', supplier_dlno='',
                 supplier_gstno='', supplier_bank='', supplier_branch='NA',
                 supplier_bankaccountno='', supplier_bankifsc='', supplier_upi=''):
        self.supplierid = supplierid  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.supplier_name = supplier_name  # VARCHAR(200) NOT NULL
        self.supplier_type = supplier_type  # VARCHAR(200) DEFAULT ''
        self.supplier_address = supplier_address  # VARCHAR(200) DEFAULT ''
        self.supplier_mobile = supplier_mobile  # VARCHAR(15) NOT NULL
        self.supplier_whatsapp = supplier_whatsapp  # VARCHAR(15) DEFAULT ''
        self.supplier_emailid = supplier_emailid  # VARCHAR(60) DEFAULT ''
        self.supplier_spoc = supplier_spoc  # VARCHAR(100) DEFAULT ''
        self.supplier_dlno = supplier_dlno  # VARCHAR(30) DEFAULT ''
        self.supplier_gstno = supplier_gstno  # VARCHAR(20) DEFAULT ''
        self.supplier_bank = supplier_bank  # VARCHAR(200) DEFAULT ''
        self.supplier_branch = supplier_branch  # VARCHAR(200) DEFAULT 'NA'
        self.supplier_bankaccountno = supplier_bankaccountno  # VARCHAR(30) DEFAULT ''
        self.supplier_bankifsc = supplier_bankifsc  # VARCHAR(20) DEFAULT ''
        self.supplier_upi = supplier_upi  # VARCHAR(50)

class CustomerMaster(BaseModel):
    """
    Corresponds to Django's CustomerMaster model.
    Stores details about customers.
    """
    def __init__(self, customerid=None, customer_name='NA', customer_type='TYPE-A',
                 customer_address='NA', customer_mobile='NA', customer_whatsapp='NA',
                 customer_emailid='NA', customer_spoc='NA', customer_dlno='NA',
                 customer_gstno='NA', customer_food_license_no='NA', customer_credit_days=0):
        self.customerid = customerid  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.customer_name = customer_name  # VARCHAR(200) NOT NULL DEFAULT 'NA'
        self.customer_type = customer_type  # VARCHAR(200) DEFAULT 'TYPE-A'
        self.customer_address = customer_address  # VARCHAR(200) DEFAULT 'NA'
        self.customer_mobile = customer_mobile  # VARCHAR(15) DEFAULT 'NA'
        self.customer_whatsapp = customer_whatsapp  # VARCHAR(15) DEFAULT 'NA'
        self.customer_emailid = customer_emailid  # VARCHAR(60) DEFAULT 'NA'
        self.customer_spoc = customer_spoc  # VARCHAR(100) DEFAULT 'NA'
        self.customer_dlno = customer_dlno  # VARCHAR(30) DEFAULT 'NA'
        self.customer_gstno = customer_gstno  # VARCHAR(20) DEFAULT 'NA'
        self.customer_food_license_no = customer_food_license_no  # VARCHAR(30) DEFAULT 'NA'
        self.customer_credit_days = customer_credit_days  # INT NOT NULL DEFAULT 0

# --- Purchase and Sales Invoicing ---

class InvoiceSeries(BaseModel):
    """
    Corresponds to Django's InvoiceSeries model.
    Manages invoice numbering series.
    """
    def __init__(self, series_id=None, series_name=None, series_prefix=None,
                 current_number=1, is_active=True, created_date=None):
        self.series_id = series_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.series_name = series_name  # VARCHAR(10) NOT NULL UNIQUE
        self.series_prefix = series_prefix  # VARCHAR(5)
        self.current_number = current_number  # INT NOT NULL DEFAULT 1
        self.is_active = is_active  # TINYINT(1) NOT NULL DEFAULT 1
        self.created_date = created_date if created_date is not None else datetime.datetime.now() # DATETIME(6) NOT NULL

    def get_next_invoice_number(self):
        # This logic would be implemented in your application layer
        if self.series_prefix:
            invoice_no = f"{self.series_prefix}{self.current_number:07d}"
        else:
            invoice_no = f"{self.series_name}{self.current_number:07d}"
        # In a real ORM, you'd update self.current_number and save the object
        return invoice_no

class InvoiceMaster(BaseModel):
    """
    Corresponds to Django's InvoiceMaster model (Purchase Invoices).
    """
    def __init__(self, invoiceid=None, retailer_id=None, invoice_no=None,
                 invoice_date=None, supplierid=None, transport_charges=0.0,
                 invoice_total=0.0, invoice_paid=0.0, payment_status='pending'):
        self.invoiceid = invoiceid  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.invoice_no = invoice_no  # VARCHAR(20) NOT NULL
        self.invoice_date = invoice_date if invoice_date is not None else datetime.date.today() # DATE NOT NULL
        self.supplierid = supplierid  # BIGINT NOT NULL (FK to SupplierMaster)
        self.transport_charges = transport_charges  # FLOAT NOT NULL
        self.invoice_total = invoice_total  # FLOAT NOT NULL
        self.invoice_paid = invoice_paid  # FLOAT NOT NULL DEFAULT 0.0
        self.payment_status = payment_status  # VARCHAR(20) NOT NULL DEFAULT 'pending'

    @property
    def balance_due(self):
        return self.invoice_total - self.invoice_paid

class InvoicePaid(BaseModel):
    """
    Corresponds to Django's InvoicePaid model (Payments for Purchase Invoices).
    """
    def __init__(self, payment_id=None, ip_invoiceid=None, payment_date=None,
                 payment_amount=0.0, payment_mode=None, payment_ref_no=None):
        self.payment_id = payment_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.ip_invoiceid = ip_invoiceid  # BIGINT NOT NULL (FK to InvoiceMaster)
        self.payment_date = payment_date if payment_date is not None else datetime.date.today() # DATE NOT NULL
        self.payment_amount = payment_amount  # FLOAT NOT NULL
        self.payment_mode = payment_mode  # VARCHAR(30)
        self.payment_ref_no = payment_ref_no  # VARCHAR(30)

class PurchaseMaster(BaseModel):
    """
    Corresponds to Django's PurchaseMaster model.
    Details of individual products purchased.
    """
    def __init__(self, purchaseid=None, retailer_id=None, product_supplierid=None,
                 product_invoiceid=None, product_invoice_no=None, productid=None,
                 product_name=None, product_company=None, product_packing=None,
                 product_batch_no=None, product_expiry=None, product_MRP=0.0,
                 product_purchase_rate=0.0, product_quantity=0.0, product_free_qty=0.0,
                 product_scheme=0.0, product_discount_got=0.0,
                 product_transportation_charges=0.0, actual_rate_per_qty=0.0,
                 product_actual_rate=0.0, total_amount=0.0, purchase_entry_date=None,
                 CGST=0.0, SGST=0.0, purchase_calculation_mode='flat',
                 rate_a=0.0, rate_b=0.0, rate_c=0.0, source_challan_no=None,
                 source_challan_date=None):
        self.purchaseid = purchaseid  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.product_supplierid = product_supplierid  # BIGINT NOT NULL (FK to SupplierMaster)
        self.product_invoiceid = product_invoiceid  # BIGINT NOT NULL (FK to InvoiceMaster)
        self.product_invoice_no = product_invoice_no  # VARCHAR(20) NOT NULL
        self.productid = productid  # BIGINT NOT NULL (FK to ProductMaster)
        self.product_name = product_name  # VARCHAR(200) NOT NULL
        self.product_company = product_company  # VARCHAR(200) NOT NULL
        self.product_packing = product_packing  # VARCHAR(20) NOT NULL
        self.product_batch_no = product_batch_no  # VARCHAR(20) NOT NULL
        self.product_expiry = product_expiry  # VARCHAR(7) NOT NULL (Format: MM-YYYY)
        self.product_MRP = product_MRP  # FLOAT NOT NULL
        self.product_purchase_rate = product_purchase_rate  # FLOAT NOT NULL
        self.product_quantity = product_quantity  # FLOAT NOT NULL
        self.product_free_qty = product_free_qty  # FLOAT NOT NULL DEFAULT 0.0
        self.product_scheme = product_scheme  # FLOAT NOT NULL DEFAULT 0.0
        self.product_discount_got = product_discount_got  # FLOAT NOT NULL
        self.product_transportation_charges = product_transportation_charges  # FLOAT NOT NULL
        self.actual_rate_per_qty = actual_rate_per_qty  # FLOAT NOT NULL DEFAULT 0.0
        self.product_actual_rate = product_actual_rate  # FLOAT NOT NULL DEFAULT 0.0
        self.total_amount = total_amount  # FLOAT NOT NULL DEFAULT 0.0
        self.purchase_entry_date = purchase_entry_date if purchase_entry_date is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.CGST = CGST  # FLOAT NOT NULL DEFAULT 0.0
        self.SGST = SGST  # FLOAT NOT NULL DEFAULT 0.0
        self.purchase_calculation_mode = purchase_calculation_mode  # VARCHAR(5) NOT NULL DEFAULT 'flat'
        self.rate_a = rate_a  # FLOAT DEFAULT 0.0
        self.rate_b = rate_b  # FLOAT DEFAULT 0.0
        self.rate_c = rate_c  # FLOAT DEFAULT 0.0
        self.source_challan_no = source_challan_no # VARCHAR(50)
        self.source_challan_date = source_challan_date # DATE

class SalesInvoiceMaster(BaseModel):
    """
    Corresponds to Django's SalesInvoiceMaster model.
    """
    def __init__(self, sales_invoice_no=None, retailer_id=None, sales_invoice_date=None,
                 customerid=None, invoice_series_id=None, sales_transport_charges=0.0,
                 sales_invoice_paid=0.0):
        self.sales_invoice_no = sales_invoice_no  # VARCHAR(20) PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.sales_invoice_date = sales_invoice_date if sales_invoice_date is not None else datetime.date.today() # DATE NOT NULL
        self.customerid = customerid  # BIGINT NOT NULL (FK to CustomerMaster)
        self.invoice_series_id = invoice_series_id  # BIGINT (FK to InvoiceSeries)
        self.sales_transport_charges = sales_transport_charges  # FLOAT NOT NULL DEFAULT 0.0
        self.sales_invoice_paid = sales_invoice_paid  # FLOAT NOT NULL DEFAULT 0.0

    # @property sales_invoice_total would be a method in the application layer
    # @property balance_due would be a method in the application layer

class SalesMaster(BaseModel):
    """
    Corresponds to Django's SalesMaster model.
    Details of individual products sold.
    """
    def __init__(self, id=None, retailer_id=None, sales_invoice_no=None, customerid=None,
                 productid=None, product_name='NA', product_company='NA',
                 product_packing='NA', product_batch_no=None, product_expiry=None,
                 product_MRP=0.0, sale_rate=0.0, sale_quantity=0.0, sale_free_qty=0.0,
                 sale_scheme=0.0, sale_discount=0.0, sale_cgst=0.0, sale_sgst=0.0,
                 sale_total_amount=0.0, sale_entry_date=None, rate_applied='NA',
                 sale_calculation_mode='flat', source_challan_no=None, source_challan_date=None):
        self.id = id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.sales_invoice_no = sales_invoice_no  # VARCHAR(20) NOT NULL (FK to SalesInvoiceMaster)
        self.customerid = customerid  # BIGINT NOT NULL (FK to CustomerMaster)
        self.productid = productid  # BIGINT NOT NULL (FK to ProductMaster)
        self.product_name = product_name  # VARCHAR(200) NOT NULL DEFAULT 'NA'
        self.product_company = product_company  # VARCHAR(200) DEFAULT 'NA'
        self.product_packing = product_packing  # VARCHAR(20) DEFAULT 'NA'
        self.product_batch_no = product_batch_no  # VARCHAR(20) NOT NULL
        self.product_expiry = product_expiry  # VARCHAR(7) NOT NULL (Format: MM-YYYY)
        self.product_MRP = product_MRP  # FLOAT NOT NULL DEFAULT 0.0
        self.sale_rate = sale_rate  # FLOAT NOT NULL DEFAULT 0.0
        self.sale_quantity = sale_quantity  # FLOAT NOT NULL DEFAULT 0.0
        self.sale_free_qty = sale_free_qty  # FLOAT NOT NULL DEFAULT 0.0
        self.sale_scheme = sale_scheme  # FLOAT NOT NULL DEFAULT 0.0
        self.sale_discount = sale_discount  # FLOAT NOT NULL DEFAULT 0.0
        self.sale_cgst = sale_cgst  # FLOAT NOT NULL DEFAULT 0.0
        self.sale_sgst = sale_sgst  # FLOAT NOT NULL DEFAULT 0.0
        self.sale_total_amount = sale_total_amount  # FLOAT NOT NULL DEFAULT 0.0
        self.sale_entry_date = sale_entry_date if sale_entry_date is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.rate_applied = rate_applied  # VARCHAR(10) DEFAULT 'NA'
        self.sale_calculation_mode = sale_calculation_mode  # VARCHAR(5) NOT NULL DEFAULT 'flat'
        self.source_challan_no = source_challan_no # VARCHAR(50)
        self.source_challan_date = source_challan_date # DATE

class SalesInvoicePaid(BaseModel):
    """
    Corresponds to Django's SalesInvoicePaid model (Payments for Sales Invoices).
    """
    def __init__(self, sales_payment_id=None, sales_ip_invoice_no=None, sales_payment_date=None,
                 sales_payment_amount=0.0, sales_payment_mode='NA', sales_payment_ref_no='NA'):
        self.sales_payment_id = sales_payment_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.sales_ip_invoice_no = sales_ip_invoice_no  # VARCHAR(20) NOT NULL (FK to SalesInvoiceMaster)
        self.sales_payment_date = sales_payment_date if sales_payment_date is not None else datetime.date.today() # DATE NOT NULL
        self.sales_payment_amount = sales_payment_amount  # FLOAT NOT NULL
        self.sales_payment_mode = sales_payment_mode  # VARCHAR(30) NOT NULL DEFAULT 'NA'
        self.sales_payment_ref_no = sales_payment_ref_no  # VARCHAR(30) NOT NULL DEFAULT 'NA'

# --- Product Rates ---

class ProductRateMaster(BaseModel):
    """
    Corresponds to Django's ProductRateMaster model.
    Stores product-specific rates.
    """
    def __init__(self, id=None, rate_productid=None, rate_A=0.0, rate_B=0.0,
                 rate_C=0.0, rate_date=None):
        self.id = id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.rate_productid = rate_productid  # BIGINT NOT NULL (FK to ProductMaster)
        self.rate_A = rate_A  # FLOAT NOT NULL DEFAULT 0.0
        self.rate_B = rate_B  # FLOAT NOT NULL DEFAULT 0.0
        self.rate_C = rate_C  # FLOAT NOT NULL DEFAULT 0.0
        self.rate_date = rate_date if rate_date is not None else datetime.date.today() # DATE NOT NULL

class SaleRateMaster(BaseModel):
    """
    Corresponds to Django's SaleRateMaster model.
    Stores batch-specific sale rates.
    """
    def __init__(self, id=None, productid=None, product_batch_no=None,
                 rate_A=0.0, rate_B=0.0, rate_C=0.0):
        self.id = id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.productid = productid  # BIGINT NOT NULL (FK to ProductMaster)
        self.product_batch_no = product_batch_no  # VARCHAR(20) NOT NULL
        self.rate_A = rate_A  # FLOAT NOT NULL DEFAULT 0.0
        self.rate_B = rate_B  # FLOAT NOT NULL DEFAULT 0.0
        self.rate_C = rate_C  # FLOAT NOT NULL DEFAULT 0.0

# --- Returns Management ---

class ReturnInvoiceMaster(BaseModel):
    """
    Corresponds to Django's ReturnInvoiceMaster model (Purchase Returns).
    """
    def __init__(self, returninvoiceid=None, retailer_id=None, returninvoice_date=None,
                 returnsupplierid=None, return_charges=0.0, returninvoice_total=0.0,
                 returninvoice_paid=0.0):
        self.returninvoiceid = returninvoiceid  # VARCHAR(20) PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.returninvoice_date = returninvoice_date if returninvoice_date is not None else datetime.date.today() # DATE NOT NULL
        self.returnsupplierid = returnsupplierid  # BIGINT NOT NULL (FK to SupplierMaster)
        self.return_charges = return_charges  # FLOAT NOT NULL DEFAULT 0.0
        self.returninvoice_total = returninvoice_total  # FLOAT NOT NULL
        self.returninvoice_paid = returninvoice_paid  # FLOAT NOT NULL DEFAULT 0.0

    @property
    def balance_due(self):
        return self.returninvoice_total - self.returninvoice_paid

class PurchaseReturnInvoicePaid(BaseModel):
    """
    Corresponds to Django's PurchaseReturnInvoicePaid model.
    Payments for Purchase Returns.
    """
    def __init__(self, pr_payment_id=None, pr_ip_returninvoiceid=None, pr_payment_date=None,
                 pr_payment_amount=0.0, pr_payment_mode=None, pr_payment_ref_no=None):
        self.pr_payment_id = pr_payment_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.pr_ip_returninvoiceid = pr_ip_returninvoiceid  # VARCHAR(20) NOT NULL (FK to ReturnInvoiceMaster)
        self.pr_payment_date = pr_payment_date if pr_payment_date is not None else datetime.date.today() # DATE NOT NULL
        self.pr_payment_amount = pr_payment_amount  # FLOAT NOT NULL
        self.pr_payment_mode = pr_payment_mode  # VARCHAR(30)
        self.pr_payment_ref_no = pr_payment_ref_no  # VARCHAR(30)

class ReturnPurchaseMaster(BaseModel):
    """
    Corresponds to Django's ReturnPurchaseMaster model.
    Details of individual products returned (purchase).
    """
    def __init__(self, returnpurchaseid=None, retailer_id=None, returninvoiceid=None,
                 returnproduct_supplierid=None, returnproductid=None,
                 returnproduct_batch_no=None, returnproduct_expiry=None,
                 returnproduct_MRP=0.0, returnproduct_purchase_rate=0.0,
                 returnproduct_quantity=0.0, returnproduct_free_qty=0.0,
                 returnproduct_cgst=2.5, returnproduct_sgst=2.5,
                 returntotal_amount=0.0, return_reason=None, returnpurchase_entry_date=None):
        self.returnpurchaseid = returnpurchaseid  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.returninvoiceid = returninvoiceid  # VARCHAR(20) NOT NULL (FK to ReturnInvoiceMaster)
        self.returnproduct_supplierid = returnproduct_supplierid  # BIGINT NOT NULL (FK to SupplierMaster)
        self.returnproductid = returnproductid  # BIGINT NOT NULL (FK to ProductMaster)
        self.returnproduct_batch_no = returnproduct_batch_no  # VARCHAR(20) NOT NULL
        self.returnproduct_expiry = returnproduct_expiry  # DATE NOT NULL
        self.returnproduct_MRP = returnproduct_MRP  # FLOAT NOT NULL DEFAULT 0.0
        self.returnproduct_purchase_rate = returnproduct_purchase_rate  # FLOAT NOT NULL
        self.returnproduct_quantity = returnproduct_quantity  # FLOAT NOT NULL
        self.returnproduct_free_qty = returnproduct_free_qty  # FLOAT NOT NULL DEFAULT 0.0
        self.returnproduct_cgst = returnproduct_cgst  # FLOAT NOT NULL DEFAULT 2.5
        self.returnproduct_sgst = returnproduct_sgst  # FLOAT NOT NULL DEFAULT 2.5
        self.returntotal_amount = returntotal_amount  # FLOAT NOT NULL DEFAULT 0.0
        self.return_reason = return_reason  # VARCHAR(200)
        self.returnpurchase_entry_date = returnpurchase_entry_date if returnpurchase_entry_date is not None else datetime.date.today() # DATE NOT NULL

class ReturnSalesInvoiceMaster(BaseModel):
    """
    Corresponds to Django's ReturnSalesInvoiceMaster model.
    """
    def __init__(self, return_sales_invoice_no=None, retailer_id=None,
                 return_sales_invoice_date=None, return_sales_customerid=None,
                 return_sales_charges=0.0, transport_charges=0.0,
                 sales_invoice_no_id=None, return_sales_invoice_total=0.0,
                 return_sales_invoice_paid=0.0, created_at=None):
        self.return_sales_invoice_no = return_sales_invoice_no  # VARCHAR(20) PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.return_sales_invoice_date = return_sales_invoice_date if return_sales_invoice_date is not None else datetime.date.today() # DATE NOT NULL
        self.return_sales_customerid = return_sales_customerid  # BIGINT NOT NULL (FK to CustomerMaster)
        self.return_sales_charges = return_sales_charges  # FLOAT NOT NULL DEFAULT 0.0
        self.transport_charges = transport_charges  # FLOAT NOT NULL DEFAULT 0.0
        self.sales_invoice_no_id = sales_invoice_no_id  # BIGINT (FK to SalesMaster.id)
        self.return_sales_invoice_total = return_sales_invoice_total  # FLOAT NOT NULL
        self.return_sales_invoice_paid = return_sales_invoice_paid  # FLOAT NOT NULL DEFAULT 0.0
        self.created_at = created_at if created_at is not None else datetime.datetime.now() # DATETIME(6) NOT NULL

    @property
    def balance_due(self):
        return self.return_sales_invoice_total - self.return_sales_invoice_paid

class ReturnSalesInvoicePaid(BaseModel):
    """
    Corresponds to Django's ReturnSalesInvoicePaid model.
    Payments for Sales Returns.
    """
    def __init__(self, return_sales_payment_id=None, return_sales_ip_invoice_no=None,
                 return_sales_payment_date=None, return_sales_payment_amount=0.0,
                 return_sales_payment_mode='NA', return_sales_payment_ref_no='NA'):
        self.return_sales_payment_id = return_sales_payment_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.return_sales_ip_invoice_no = return_sales_ip_invoice_no  # VARCHAR(20) NOT NULL (FK to ReturnSalesInvoiceMaster)
        self.return_sales_payment_date = return_sales_payment_date if return_sales_payment_date is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.return_sales_payment_amount = return_sales_payment_amount  # FLOAT NOT NULL
        self.return_sales_payment_mode = return_sales_payment_mode  # VARCHAR(30) NOT NULL DEFAULT 'NA'
        self.return_sales_payment_ref_no = return_sales_payment_ref_no  # VARCHAR(30) NOT NULL DEFAULT 'NA'

class ReturnSalesMaster(BaseModel):
    """
    Corresponds to Django's ReturnSalesMaster model.
    Details of individual products returned (sales).
    """
    RETURN_REASON_CHOICES = ['non_moving', 'breakage', 'expiry', 'Select Reason']
    CALCULATION_MODE_CHOICES = ['percentage', 'fixed']

    def __init__(self, return_sales_id=None, retailer_id=None, return_sales_invoice_no=None,
                 return_customerid=None, return_productid=None, return_product_name='NA',
                 return_product_company='NA', return_product_packing='NA',
                 return_product_batch_no=None, return_product_expiry=None,
                 return_product_MRP=0.0, return_sale_rate=0.0, return_sale_quantity=0.0,
                 return_sale_free_qty=0.0, return_sale_scheme=0.0, return_sale_discount=0.0,
                 return_sale_cgst=0.0, return_sale_sgst=0.0, return_sale_total_amount=0.0,
                 return_reason=None, return_sale_entry_date=None,
                 return_sale_calculation_mode='percentage'):
        self.return_sales_id = return_sales_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.return_sales_invoice_no = return_sales_invoice_no  # VARCHAR(20) NOT NULL (FK to ReturnSalesInvoiceMaster)
        self.return_customerid = return_customerid  # BIGINT NOT NULL (FK to CustomerMaster)
        self.return_productid = return_productid  # BIGINT NOT NULL (FK to ProductMaster)
        self.return_product_name = return_product_name  # VARCHAR(200) NOT NULL DEFAULT 'NA'
        self.return_product_company = return_product_company  # VARCHAR(200) DEFAULT 'NA'
        self.return_product_packing = return_product_packing  # VARCHAR(20) DEFAULT 'NA'
        self.return_product_batch_no = return_product_batch_no  # VARCHAR(20) NOT NULL
        self.return_product_expiry = return_product_expiry  # VARCHAR(7) NOT NULL (Format: MM-YYYY)
        self.return_product_MRP = return_product_MRP  # FLOAT NOT NULL DEFAULT 0.0
        self.return_sale_rate = return_sale_rate  # FLOAT NOT NULL DEFAULT 0.0
        self.return_sale_quantity = return_sale_quantity  # FLOAT NOT NULL DEFAULT 0.0
        self.return_sale_free_qty = return_sale_free_qty  # FLOAT NOT NULL DEFAULT 0.0
        self.return_sale_scheme = return_sale_scheme  # FLOAT NOT NULL DEFAULT 0.0
        self.return_sale_discount = return_sale_discount  # FLOAT NOT NULL DEFAULT 0.0
        self.return_sale_cgst = return_sale_cgst  # FLOAT NOT NULL DEFAULT 0.0
        self.return_sale_sgst = return_sale_sgst  # FLOAT NOT NULL DEFAULT 0.0
        self.return_sale_total_amount = return_sale_total_amount  # FLOAT NOT NULL DEFAULT 0.0
        self.return_reason = return_reason  # VARCHAR(200) (choices)
        self.return_sale_entry_date = return_sale_entry_date if return_sale_entry_date is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.return_sale_calculation_mode = return_sale_calculation_mode  # VARCHAR(20) NOT NULL DEFAULT 'percentage' (choices)

# --- Challan Management ---

class Challan1(BaseModel):
    """
    Corresponds to Django's Challan1 model (Supplier Challans).
    """
    def __init__(self, challan_id=None, retailer_id=None, challan_no=None,
                 challan_date=None, supplier_id=None, challan_total=0.0,
                 transport_charges=0.0, challan_paid=0.0, challan_remark='None',
                 is_invoiced=False, created_at=None, updated_at=None):
        self.challan_id = challan_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.challan_no = challan_no  # VARCHAR(50) NOT NULL UNIQUE
        self.challan_date = challan_date if challan_date is not None else datetime.date.today() # DATE NOT NULL
        self.supplier_id = supplier_id  # BIGINT NOT NULL (FK to SupplierMaster)
        self.challan_total = challan_total  # FLOAT NOT NULL DEFAULT 0.0
        self.transport_charges = transport_charges  # FLOAT NOT NULL DEFAULT 0.0
        self.challan_paid = challan_paid  # FLOAT NOT NULL DEFAULT 0.0
        self.challan_remark = challan_remark  # LONGTEXT NOT NULL DEFAULT 'None'
        self.is_invoiced = is_invoiced  # TINYINT(1) NOT NULL DEFAULT 0
        self.created_at = created_at if created_at is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.updated_at = updated_at if updated_at is not None else datetime.datetime.now() # DATETIME(6) NOT NULL (auto_now)

class SupplierChallanMaster(BaseModel):
    """
    Corresponds to Django's SupplierChallanMaster model.
    Details of individual products in a supplier challan.
    """
    def __init__(self, challan_id=None, retailer_id=None, product_suppliername_id=None,
                 product_challan_id=None, product_challan_no=None, product_id=None,
                 product_name=None, product_company=None, product_packing=None,
                 product_batch_no=None, product_expiry=None, product_mrp=0.0,
                 product_purchase_rate=0.0, product_quantity=0.0, product_free_qty=0.0,
                 product_scheme=0.0, product_discount=0.0,
                 product_transportation_charges=0.0, actual_rate_per_qty=0.0,
                 product_actual_rate=0.0, total_amount=0.0, challan_entry_date=None,
                 cgst=2.5, sgst=2.5, challan_calculation_mode='flat',
                 rate_a=0.0, rate_b=0.0, rate_c=0.0):
        self.challan_id = challan_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.product_suppliername_id = product_suppliername_id  # BIGINT NOT NULL (FK to SupplierMaster)
        self.product_challan_id = product_challan_id  # BIGINT NOT NULL (FK to Challan1)
        self.product_challan_no = product_challan_no  # VARCHAR(50) NOT NULL
        self.product_id = product_id  # BIGINT NOT NULL (FK to ProductMaster)
        self.product_name = product_name  # VARCHAR(200) NOT NULL
        self.product_company = product_company  # VARCHAR(200) NOT NULL
        self.product_packing = product_packing  # VARCHAR(20) NOT NULL
        self.product_batch_no = product_batch_no  # VARCHAR(20) NOT NULL
        self.product_expiry = product_expiry  # VARCHAR(7) NOT NULL (Format: MM-YYYY)
        self.product_mrp = product_mrp  # FLOAT NOT NULL
        self.product_purchase_rate = product_purchase_rate  # FLOAT NOT NULL
        self.product_quantity = product_quantity  # FLOAT NOT NULL
        self.product_free_qty = product_free_qty  # FLOAT NOT NULL DEFAULT 0.0
        self.product_scheme = product_scheme  # FLOAT NOT NULL DEFAULT 0.0
        self.product_discount = product_discount  # FLOAT NOT NULL DEFAULT 0.0
        self.product_transportation_charges = product_transportation_charges  # FLOAT NOT NULL DEFAULT 0.0
        self.actual_rate_per_qty = actual_rate_per_qty  # FLOAT NOT NULL DEFAULT 0.0
        self.product_actual_rate = product_actual_rate  # FLOAT NOT NULL DEFAULT 0.0
        self.total_amount = total_amount  # FLOAT NOT NULL DEFAULT 0.0
        self.challan_entry_date = challan_entry_date if challan_entry_date is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.cgst = cgst  # FLOAT NOT NULL DEFAULT 2.5
        self.sgst = sgst  # FLOAT NOT NULL DEFAULT 2.5
        self.challan_calculation_mode = challan_calculation_mode  # VARCHAR(10) NOT NULL DEFAULT 'flat'
        self.rate_a = rate_a  # FLOAT DEFAULT 0.0
        self.rate_b = rate_b  # FLOAT DEFAULT 0.0
        self.rate_c = rate_c  # FLOAT DEFAULT 0.0

class SupplierChallanMaster2(BaseModel):
    """
    Corresponds to Django's SupplierChallanMaster2 model.
    (Seems to be a duplicate of SupplierChallanMaster, possibly for different reporting/processing)
    """
    def __init__(self, challan_id=None, retailer_id=None, product_suppliername_id=None,
                 product_challan_id=None, product_challan_no=None, product_id=None,
                 product_name=None, product_company=None, product_packing=None,
                 product_batch_no=None, product_expiry=None, product_mrp=0.0,
                 product_purchase_rate=0.0, product_quantity=0.0, product_free_qty=0.0,
                 product_scheme=0.0, product_discount=0.0,
                 product_transportation_charges=0.0, actual_rate_per_qty=0.0,
                 product_actual_rate=0.0, total_amount=0.0, challan_entry_date=None,
                 cgst=2.5, sgst=2.5, challan_calculation_mode='flat',
                 rate_a=0.0, rate_b=0.0, rate_c=0.0):
        self.challan_id = challan_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.product_suppliername_id = product_suppliername_id  # BIGINT NOT NULL (FK to SupplierMaster)
        self.product_challan_id = product_challan_id  # BIGINT NOT NULL (FK to Challan1)
        self.product_challan_no = product_challan_no  # VARCHAR(50) NOT NULL
        self.product_id = product_id  # BIGINT NOT NULL (FK to ProductMaster)
        self.product_name = product_name  # VARCHAR(200) NOT NULL
        self.product_company = product_company  # VARCHAR(200) NOT NULL
        self.product_packing = product_packing  # VARCHAR(20) NOT NULL
        self.product_batch_no = product_batch_no  # VARCHAR(20) NOT NULL
        self.product_expiry = product_expiry  # VARCHAR(7) NOT NULL (Format: MM-YYYY)
        self.product_mrp = product_mrp  # FLOAT NOT NULL
        self.product_purchase_rate = product_purchase_rate  # FLOAT NOT NULL
        self.product_quantity = product_quantity  # FLOAT NOT NULL
        self.product_free_qty = product_free_qty  # FLOAT NOT NULL DEFAULT 0.0
        self.product_scheme = product_scheme  # FLOAT NOT NULL DEFAULT 0.0
        self.product_discount = product_discount  # FLOAT NOT NULL DEFAULT 0.0
        self.product_transportation_charges = product_transportation_charges  # FLOAT NOT NULL DEFAULT 0.0
        self.actual_rate_per_qty = actual_rate_per_qty  # FLOAT NOT NULL DEFAULT 0.0
        self.product_actual_rate = product_actual_rate  # FLOAT NOT NULL DEFAULT 0.0
        self.total_amount = total_amount  # FLOAT NOT NULL DEFAULT 0.0
        self.challan_entry_date = challan_entry_date if challan_entry_date is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.cgst = cgst  # FLOAT NOT NULL DEFAULT 2.5
        self.sgst = sgst  # FLOAT NOT NULL DEFAULT 2.5
        self.challan_calculation_mode = challan_calculation_mode  # VARCHAR(10) NOT NULL DEFAULT 'flat'
        self.rate_a = rate_a  # FLOAT DEFAULT 0.0
        self.rate_b = rate_b  # FLOAT DEFAULT 0.0
        self.rate_c = rate_c  # FLOAT DEFAULT 0.0

class ChallanSeries(BaseModel):
    """
    Corresponds to Django's ChallanSeries model.
    Manages challan numbering series.
    """
    def __init__(self, series_id=None, series_name=None, is_active=True, created_date=None):
        self.series_id = series_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.series_name = series_name  # VARCHAR(10) NOT NULL UNIQUE
        self.is_active = is_active  # TINYINT(1) NOT NULL DEFAULT 1
        self.created_date = created_date if created_date is not None else datetime.datetime.now() # DATETIME(6) NOT NULL

class CustomerChallan(BaseModel):
    """
    Corresponds to Django's CustomerChallan model.
    """
    def __init__(self, customer_challan_id=None, retailer_id=None, customer_challan_no=None,
                 customer_challan_date=None, customer_name_id=None, challan_series_id=None,
                 customer_transport_charges=0.0, challan_total=0.0,
                 challan_invoice_paid=0.0, is_invoiced=False, created_at=None, updated_at=None):
        self.customer_challan_id = customer_challan_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.customer_challan_no = customer_challan_no  # VARCHAR(50) NOT NULL UNIQUE
        self.customer_challan_date = customer_challan_date if customer_challan_date is not None else datetime.date.today() # DATE NOT NULL
        self.customer_name_id = customer_name_id  # BIGINT NOT NULL (FK to CustomerMaster)
        self.challan_series_id = challan_series_id  # BIGINT (FK to ChallanSeries)
        self.customer_transport_charges = customer_transport_charges  # FLOAT NOT NULL DEFAULT 0.0
        self.challan_total = challan_total  # FLOAT NOT NULL DEFAULT 0.0
        self.challan_invoice_paid = challan_invoice_paid  # FLOAT NOT NULL DEFAULT 0.0
        self.is_invoiced = is_invoiced  # TINYINT(1) NOT NULL DEFAULT 0
        self.created_at = created_at if created_at is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.updated_at = updated_at if updated_at is not None else datetime.datetime.now() # DATETIME(6) NOT NULL (auto_now)

class CustomerChallanMaster(BaseModel):
    """
    Corresponds to Django's CustomerChallanMaster model.
    Details of individual products in a customer challan.
    """
    def __init__(self, customer_challan_master_id=None, retailer_id=None,
                 customer_challan_id=None, customer_challan_no=None, customer_name_id=None,
                 product_id=None, product_name=None, product_company=None,
                 product_packing=None, product_batch_no=None, product_expiry=None,
                 product_mrp=0.0, sale_rate=0.0, sale_quantity=0.0, sale_free_qty=0.0,
                 sale_discount=0.0, sale_cgst=2.5, sale_sgst=2.5, sale_total_amount=0.0,
                 sales_entry_date=None, rate_applied='NA'):
        self.customer_challan_master_id = customer_challan_master_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.customer_challan_id = customer_challan_id  # BIGINT NOT NULL (FK to CustomerChallan)
        self.customer_challan_no = customer_challan_no  # VARCHAR(50) NOT NULL
        self.customer_name_id = customer_name_id  # BIGINT NOT NULL (FK to CustomerMaster)
        self.product_id = product_id  # BIGINT NOT NULL (FK to ProductMaster)
        self.product_name = product_name  # VARCHAR(200) NOT NULL
        self.product_company = product_company  # VARCHAR(200) NOT NULL
        self.product_packing = product_packing  # VARCHAR(20) NOT NULL
        self.product_batch_no = product_batch_no  # VARCHAR(20) NOT NULL
        self.product_expiry = product_expiry  # VARCHAR(7) NOT NULL (Format: MM-YYYY)
        self.product_mrp = product_mrp  # FLOAT NOT NULL
        self.sale_rate = sale_rate  # FLOAT NOT NULL
        self.sale_quantity = sale_quantity  # FLOAT NOT NULL
        self.sale_free_qty = sale_free_qty  # FLOAT NOT NULL DEFAULT 0.0
        self.sale_discount = sale_discount  # FLOAT NOT NULL DEFAULT 0.0
        self.sale_cgst = sale_cgst  # FLOAT NOT NULL DEFAULT 2.5
        self.sale_sgst = sale_sgst  # FLOAT NOT NULL DEFAULT 2.5
        self.sale_total_amount = sale_total_amount  # FLOAT NOT NULL
        self.sales_entry_date = sales_entry_date if sales_entry_date is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.rate_applied = rate_applied  # VARCHAR(10) DEFAULT 'NA'

class CustomerChallanMaster2(BaseModel):
    """
    Corresponds to Django's CustomerChallanMaster2 model.
    (Seems to be a duplicate of CustomerChallanMaster, possibly for different reporting/processing)
    """
    def __init__(self, customer_challan_master_id=None, retailer_id=None,
                 customer_challan_id=None, customer_challan_no=None, customer_name_id=None,
                 product_id=None, product_name=None, product_company=None,
                 product_packing=None, product_batch_no=None, product_expiry=None,
                 product_mrp=0.0, sale_rate=0.0, sale_quantity=0.0, sale_free_qty=0.0,
                 sale_discount=0.0, sale_cgst=2.5, sale_sgst=2.5, sale_total_amount=0.0,
                 sales_entry_date=None, rate_applied='NA'):
        self.customer_challan_master_id = customer_challan_master_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.customer_challan_id = customer_challan_id  # BIGINT NOT NULL (FK to CustomerChallan)
        self.customer_challan_no = customer_challan_no  # VARCHAR(50) NOT NULL
        self.customer_name_id = customer_name_id  # BIGINT NOT NULL (FK to CustomerMaster)
        self.product_id = product_id  # BIGINT NOT NULL (FK to ProductMaster)
        self.product_name = product_name  # VARCHAR(200) NOT NULL
        self.product_company = product_company  # VARCHAR(200) NOT NULL
        self.product_packing = product_packing  # VARCHAR(20) NOT NULL
        self.product_batch_no = product_batch_no  # VARCHAR(20) NOT NULL
        self.product_expiry = product_expiry  # VARCHAR(7) NOT NULL (Format: MM-YYYY)
        self.product_mrp = product_mrp  # FLOAT NOT NULL
        self.sale_rate = sale_rate  # FLOAT NOT NULL
        self.sale_quantity = sale_quantity  # FLOAT NOT NULL
        self.sale_free_qty = sale_free_qty  # FLOAT NOT NULL DEFAULT 0.0
        self.sale_discount = sale_discount  # FLOAT NOT NULL DEFAULT 0.0
        self.sale_cgst = sale_cgst  # FLOAT NOT NULL DEFAULT 2.5
        self.sale_sgst = sale_sgst  # FLOAT NOT NULL DEFAULT 2.5
        self.sale_total_amount = sale_total_amount  # FLOAT NOT NULL
        self.sales_entry_date = sales_entry_date if sales_entry_date is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.rate_applied = rate_applied  # VARCHAR(10) DEFAULT 'NA'

# --- Stock Management ---

class StockIssueMaster(BaseModel):
    """
    Corresponds to Django's StockIssueMaster model.
    Manages stock issues/adjustments.
    """
    ISSUE_TYPES = ['damage', 'expiry', 'theft', 'loss', 'adjustment', 'transfer', 'sample', 'other']

    def __init__(self, issue_id=None, retailer_id=None, issue_no=None, issue_date=None,
                 issue_type=None, total_value=0.0, remarks=None, created_by_id=None,
                 created_at=None, updated_at=None):
        self.issue_id = issue_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.issue_no = issue_no  # VARCHAR(20) NOT NULL UNIQUE
        self.issue_date = issue_date if issue_date is not None else datetime.date.today() # DATE NOT NULL
        self.issue_type = issue_type  # VARCHAR(20) NOT NULL (choices)
        self.total_value = total_value  # FLOAT NOT NULL DEFAULT 0.0
        self.remarks = remarks  # LONGTEXT
        self.created_by_id = created_by_id  # BIGINT (FK to WebUser)
        self.created_at = created_at if created_at is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.updated_at = updated_at if updated_at is not None else datetime.datetime.now() # DATETIME(6) NOT NULL (auto_now)

    # The save method's issue_no generation logic would be in your application layer

class StockIssueDetail(BaseModel):
    """
    Corresponds to Django's StockIssueDetail model.
    Details of items in a stock issue.
    """
    def __init__(self, detail_id=None, retailer_id=None, issue_id=None, product_id=None,
                 batch_no=None, expiry_date=None, quantity_issued=0.0, unit_rate=0.0,
                 total_amount=0.0, remarks=None):
        self.detail_id = detail_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.issue_id = issue_id  # BIGINT NOT NULL (FK to StockIssueMaster)
        self.product_id = product_id  # BIGINT NOT NULL (FK to ProductMaster)
        self.batch_no = batch_no  # VARCHAR(20) NOT NULL
        self.expiry_date = expiry_date  # VARCHAR(7) NOT NULL (Format: MM-YYYY)
        self.quantity_issued = quantity_issued  # FLOAT NOT NULL (MinValueValidator(0.01))
        self.unit_rate = unit_rate  # FLOAT NOT NULL DEFAULT 0.0
        self.total_amount = total_amount  # FLOAT NOT NULL DEFAULT 0.0
        self.remarks = remarks  # LONGTEXT

    # The save method's total_amount calculation logic would be in your application layer

# --- Financial Management ---

class ContraEntry(BaseModel):
    """
    Corresponds to Django's ContraEntry model.
    Manages fund transfers between cash and bank.
    """
    CONTRA_TYPES = ['BANK_TO_CASH', 'CASH_TO_BANK']

    def __init__(self, contra_id=None, contra_no=None, contra_date=None, contra_type=None,
                 amount=0.0, from_account=None, to_account=None, reference_no=None,
                 narration=None, created_by_id=None, created_at=None, updated_at=None):
        self.contra_id = contra_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.contra_no = contra_no  # VARCHAR(20) NOT NULL UNIQUE
        self.contra_date = contra_date if contra_date is not None else datetime.date.today() # DATE NOT NULL
        self.contra_type = contra_type  # VARCHAR(20) NOT NULL (choices)
        self.amount = amount  # FLOAT NOT NULL (MinValueValidator(0.01))
        self.from_account = from_account  # VARCHAR(100) NOT NULL
        self.to_account = to_account  # VARCHAR(100) NOT NULL
        self.reference_no = reference_no  # VARCHAR(50)
        self.narration = narration  # LONGTEXT
        self.created_by_id = created_by_id  # BIGINT (FK to WebUser)
        self.created_at = created_at if created_at is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.updated_at = updated_at if updated_at is not None else datetime.datetime.now() # DATETIME(6) NOT NULL (auto_now)

    # The save method's contra_no generation logic would be in your application layer

# --- Inventory Cache Tables ---

class ProductInventoryCache(BaseModel):
    """
    Corresponds to Django's ProductInventoryCache model.
    Cache table for product-level inventory summary.
    """
    def __init__(self, product_id=None, total_stock=0.0, total_batches=0,
                 avg_mrp=0.0, avg_purchase_rate=0.0, total_stock_value=0.0,
                 stock_status='out_of_stock', has_expired_batches=False,
                 last_updated=None):
        self.product_id = product_id  # BIGINT PRIMARY KEY (OneToOneField)
        self.total_stock = total_stock  # FLOAT NOT NULL DEFAULT 0.0
        self.total_batches = total_batches  # INT NOT NULL DEFAULT 0
        self.avg_mrp = avg_mrp  # FLOAT NOT NULL DEFAULT 0.0
        self.avg_purchase_rate = avg_purchase_rate  # FLOAT NOT NULL DEFAULT 0.0
        self.total_stock_value = total_stock_value  # FLOAT NOT NULL DEFAULT 0.0
        self.stock_status = stock_status  # VARCHAR(50) NOT NULL DEFAULT 'out_of_stock'
        self.has_expired_batches = has_expired_batches  # TINYINT(1) NOT NULL DEFAULT 0
        self.last_updated = last_updated if last_updated is not None else datetime.datetime.now() # DATETIME(6) NOT NULL (auto_now)

class BatchInventoryCache(BaseModel):
    """
    Corresponds to Django's BatchInventoryCache model.
    Cache table for batch-level inventory details.
    """
    def __init__(self, id=None, product_id=None, retailer_id=None, batch_no=None,
                 expiry_date=None, current_stock=0.0, current_free_qty=0.0,
                 total_stock=0.0, mrp=0.0, purchase_rate=0.0,
                 rate_a=0.0, rate_b=0.0, rate_c=0.0,
                 is_expired=False, expiry_status='valid', last_updated=None):
        self.id = id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.product_id = product_id  # BIGINT NOT NULL (FK to ProductMaster)
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.batch_no = batch_no  # VARCHAR(20) NOT NULL
        self.expiry_date = expiry_date  # VARCHAR(7) NOT NULL (Format: MM-YYYY)
        self.current_stock = current_stock  # FLOAT NOT NULL DEFAULT 0.0
        self.current_free_qty = current_free_qty  # FLOAT NOT NULL DEFAULT 0.0
        self.total_stock = total_stock  # FLOAT NOT NULL DEFAULT 0.0
        self.mrp = mrp  # FLOAT NOT NULL DEFAULT 0.0
        self.purchase_rate = purchase_rate  # FLOAT NOT NULL DEFAULT 0.0
        self.rate_a = rate_a  # FLOAT NOT NULL DEFAULT 0.0
        self.rate_b = rate_b  # FLOAT NOT NULL DEFAULT 0.0
        self.rate_c = rate_c  # FLOAT NOT NULL DEFAULT 0.0
        self.is_expired = is_expired  # TINYINT(1) NOT NULL DEFAULT 0
        self.expiry_status = expiry_status  # VARCHAR(20) NOT NULL DEFAULT 'valid'
        self.last_updated = last_updated if last_updated is not None else datetime.datetime.now() # DATETIME(6) NOT NULL (auto_now)

# --- Inventory Transaction Table ---

class InventoryTransaction(BaseModel):
    """
    Corresponds to Django's InventoryTransaction model.
    Single source of truth for all inventory movements.
    """
    TRANSACTION_TYPES = ['PURCHASE', 'SALE', 'PURCHASE_RETURN', 'SALES_RETURN',
                         'SUPPLIER_CHALLAN', 'CUSTOMER_CHALLAN', 'STOCK_ISSUE']
    REFERENCE_TYPES = ['INVOICE', 'CHALLAN', 'ISSUE']

    def __init__(self, transaction_id=None, retailer_id=None, product_id=None,
                 batch_no=None, expiry_date=None, transaction_type=None,
                 quantity=Decimal('0.00'), free_quantity=Decimal('0.00'),
                 transaction_date=None, reference_type=None, reference_id=None,
                 reference_number=None, rate=Decimal('0.00'), mrp=Decimal('0.00'),
                 total_value=Decimal('0.00'), created_at=None, created_by_id=None,
                 remarks=None):
        self.transaction_id = transaction_id  # BIGINT AUTO_INCREMENT PRIMARY KEY
        self.retailer_id = retailer_id  # BIGINT (FK to Retailer)
        self.product_id = product_id  # BIGINT NOT NULL (FK to ProductMaster)
        self.batch_no = batch_no  # VARCHAR(20) NOT NULL
        self.expiry_date = expiry_date  # VARCHAR(7) NOT NULL (Format: MM-YYYY)
        self.transaction_type = transaction_type  # VARCHAR(20) NOT NULL (choices)
        self.quantity = quantity  # DECIMAL(10, 2) NOT NULL
        self.free_quantity = free_quantity  # DECIMAL(10, 2) NOT NULL DEFAULT 0.0
        self.transaction_date = transaction_date if transaction_date is not None else datetime.datetime.now() # DATETIME(6) NOT NULL
        self.reference_type = reference_type  # VARCHAR(20) NOT NULL (choices)
        self.reference_id = reference_id  # BIGINT NOT NULL
        self.reference_number = reference_number  # VARCHAR(50) NOT NULL
        self.rate = rate  # DECIMAL(10, 2) NOT NULL
        self.mrp = mrp  # DECIMAL(10, 2) NOT NULL
        self.total_value = total_value  # DECIMAL(12, 2) NOT NULL
        self.created_at = created_at if created_at is not None else datetime.datetime.now() # DATETIME(6) NOT NULL (auto_now_add)
        self.created_by_id = created_by_id  # BIGINT (FK to WebUser)
        self.remarks = remarks  # LONGTEXT

    # The save method's total_value calculation logic would be in your application layer
    # Class methods like get_batch_stock, get_product_stock, get_batch_wise_stock would be
    # implemented in your data access layer (e.g., using SQLAlchemy queries).
