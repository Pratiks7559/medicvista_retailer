-- MedicVista Retailer Backup
-- Database  : medicvista_retailer
-- Retailer  : 1
-- Generated : 2026-07-04 08:13:57.027204
-- NOTE: Contains ONLY data for retailer_id = 1

SET FOREIGN_KEY_CHECKS=0;
SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO';
SET NAMES utf8mb4;


-- Table: core_productmaster
LOCK TABLES `core_productmaster` WRITE;
INSERT INTO `core_productmaster` (`productid`, `retailer_id`, `product_name`, `product_company`, `product_packing`, `product_image`, `product_salt`, `product_category`, `product_hsn`, `product_hsn_percent`, `product_barcode`, `created_at`) VALUES (113, 1, 'RE1', 'RE1', '2', 'images/medicine_default.png', '', '', '', '', NULL, '2026-07-03 21:01:30');
UNLOCK TABLES;

-- Table: core_suppliermaster
LOCK TABLES `core_suppliermaster` WRITE;
INSERT INTO `core_suppliermaster` (`supplierid`, `supplier_name`, `supplier_type`, `supplier_address`, `supplier_mobile`, `supplier_whatsapp`, `supplier_emailid`, `supplier_spoc`, `supplier_dlno`, `supplier_gstno`, `supplier_bank`, `supplier_branch`, `supplier_bankaccountno`, `supplier_bankifsc`, `supplier_upi`, `created_at`, `retailer_id`) VALUES (3, 'fake', 'fake', '', '958888888888', '', '', '', '', '', '', '', '', '', '', '2026-06-12 17:25:59', 1);
INSERT INTO `core_suppliermaster` (`supplierid`, `supplier_name`, `supplier_type`, `supplier_address`, `supplier_mobile`, `supplier_whatsapp`, `supplier_emailid`, `supplier_spoc`, `supplier_dlno`, `supplier_gstno`, `supplier_bank`, `supplier_branch`, `supplier_bankaccountno`, `supplier_bankifsc`, `supplier_upi`, `created_at`, `retailer_id`) VALUES (4, 'fake3', '', '', '1029384756', '', '', '', '', '', '', '', '', '', '', '2026-07-03 16:55:58', 1);
UNLOCK TABLES;

-- Table: core_customermaster
LOCK TABLES `core_customermaster` WRITE;
INSERT INTO `core_customermaster` (`customerid`, `customer_name`, `customer_type`, `customer_address`, `customer_mobile`, `customer_whatsapp`, `customer_emailid`, `customer_spoc`, `customer_dlno`, `customer_gstno`, `customer_food_license_no`, `customer_credit_days`, `created_at`, `retailer_id`) VALUES (3, 'fak1', 'TYPE-A', '', '', '', '', '', '', '', '', 0, '2026-06-12 22:52:56', 1);
INSERT INTO `core_customermaster` (`customerid`, `customer_name`, `customer_type`, `customer_address`, `customer_mobile`, `customer_whatsapp`, `customer_emailid`, `customer_spoc`, `customer_dlno`, `customer_gstno`, `customer_food_license_no`, `customer_credit_days`, `created_at`, `retailer_id`) VALUES (4, 'Walk-in Customer', 'CASH', 'N/A', 'N/A', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 0, '2026-06-13 22:23:23', 1);
UNLOCK TABLES;

-- Table: core_invoicemaster
LOCK TABLES `core_invoicemaster` WRITE;
INSERT INTO `core_invoicemaster` (`invoiceid`, `retailer_id`, `invoice_no`, `invoice_date`, `supplierid_id`, `transport_charges`, `invoice_total`, `invoice_paid`, `payment_status`, `created_at`) VALUES (5, 1, '1209', '2026-07-03', 3, 0.0, 6.3, 0.0, 'pending', '2026-07-03 21:02:15');
UNLOCK TABLES;

-- Table: core_purchasemaster
LOCK TABLES `core_purchasemaster` WRITE;
INSERT INTO `core_purchasemaster` (`purchaseid`, `retailer_id`, `product_supplierid_id`, `product_invoiceid_id`, `product_invoice_no`, `productid_id`, `product_name`, `product_company`, `product_packing`, `product_batch_no`, `product_expiry`, `product_MRP`, `product_purchase_rate`, `product_quantity`, `product_free_qty`, `product_scheme`, `product_discount_got`, `product_transportation_charges`, `actual_rate_per_qty`, `product_actual_rate`, `total_amount`, `purchase_entry_date`, `CGST`, `SGST`, `purchase_calculation_mode`, `rate_a`, `rate_b`, `rate_c`, `source_challan_no`, `source_challan_date`) VALUES (5, 1, 3, 5, '1209', 113, 'RE1', 'RE1', '2', '123', '12-2027', 3.0, 2.0, 3.0, 0.0, 0.0, 0.0, 0.0, 2.0, 2.0, 6.3, '2026-07-03 21:02:15', 2.5, 2.5, 'flat', 0.0, 0.0, 0.0, NULL, NULL);
UNLOCK TABLES;

-- Table: core_salesinvoicemaster
LOCK TABLES `core_salesinvoicemaster` WRITE;
INSERT INTO `core_salesinvoicemaster` (`sales_invoice_no`, `retailer_id`, `sales_invoice_date`, `customerid_id`, `invoice_series_id`, `sales_transport_charges`, `sales_invoice_paid`, `created_at`) VALUES ('INV0000001', 1, '2026-07-03', 4, NULL, 0.0, 0.0, '2026-07-03 21:18:43');
UNLOCK TABLES;

-- Table: core_salesmaster
LOCK TABLES `core_salesmaster` WRITE;
INSERT INTO `core_salesmaster` (`id`, `retailer_id`, `sales_invoice_no_id`, `customerid_id`, `productid_id`, `product_name`, `product_company`, `product_packing`, `product_batch_no`, `product_expiry`, `product_MRP`, `sale_rate`, `sale_quantity`, `sale_free_qty`, `sale_scheme`, `sale_discount`, `sale_cgst`, `sale_sgst`, `sale_total_amount`, `sale_entry_date`, `rate_applied`, `sale_calculation_mode`, `source_challan_no`, `source_challan_date`) VALUES (31, 1, 'INV0000001', 4, 113, 'RE1', 'RE1', '2', '123', '12-2027', 3.0, 2.0, 3.0, 0.0, 0.0, 0.0, 2.5, 2.5, 9.45, '2026-07-03 21:18:47', 'A', 'flat', NULL, NULL);
UNLOCK TABLES;

-- Table: inventory_transaction
LOCK TABLES `inventory_transaction` WRITE;
INSERT INTO `inventory_transaction` (`id`, `retailer_id`, `product_id`, `batch_no`, `expiry_date`, `transaction_type`, `quantity`, `free_quantity`, `transaction_date`, `reference_type`, `reference_id`, `reference_number`, `rate`, `mrp`, `total_value`, `created_at`, `created_by_id`, `remarks`) VALUES (12, 1, 107, '10101010', '12-2025', 'PURCHASE', '20.000', '0.000', '2026-06-15 11:45:09', 'INVOICE', 11, 'fnj', '2.0000', '5.0000', '4.20', '2026-06-15 11:45:09', NULL, 'Purchase Invoice fnj (packing x10)');
INSERT INTO `inventory_transaction` (`id`, `retailer_id`, `product_id`, `batch_no`, `expiry_date`, `transaction_type`, `quantity`, `free_quantity`, `transaction_date`, `reference_type`, `reference_id`, `reference_number`, `rate`, `mrp`, `total_value`, `created_at`, `created_by_id`, `remarks`) VALUES (23, 1, 113, '123', '12-2027', 'PURCHASE', '6.000', '0.000', '2026-07-03 21:02:15', 'INVOICE', 5, '1209', '2.0000', '3.0000', '6.30', '2026-07-03 21:02:15', NULL, 'Purchase Invoice 1209 (packing x2)');
INSERT INTO `inventory_transaction` (`id`, `retailer_id`, `product_id`, `batch_no`, `expiry_date`, `transaction_type`, `quantity`, `free_quantity`, `transaction_date`, `reference_type`, `reference_id`, `reference_number`, `rate`, `mrp`, `total_value`, `created_at`, `created_by_id`, `remarks`) VALUES (25, 1, 113, '123', '12-2027', 'SALE', '3.000', '0.000', '2026-07-03 21:18:47', 'INVOICE', 0, 'INV0000001', '2.0000', '3.0000', '9.45', '2026-07-03 21:18:47', NULL, 'Sales Invoice INV0000001');
UNLOCK TABLES;

-- Table: retailer_request
LOCK TABLES `retailer_request` WRITE;
INSERT INTO `retailer_request` (`id`, `retailer_id`, `request_type`, `reference_id`, `status`, `created_at`, `processed_at`, `remarks`, `from_date`, `to_date`, `product_ids`) VALUES (70, 1, 'SALES', 68, 'Processed', '2026-07-04 08:07:37', '2026-07-04 08:07:56', '', '2026-07-01', '2026-07-04', '113');
INSERT INTO `retailer_request` (`id`, `retailer_id`, `request_type`, `reference_id`, `status`, `created_at`, `processed_at`, `remarks`, `from_date`, `to_date`, `product_ids`) VALUES (71, 1, 'PURCHASE', 67, 'Processed', '2026-07-04 08:07:37', '2026-07-04 08:07:56', '', '2026-07-01', '2026-07-04', '113');
UNLOCK TABLES;

-- Table: core_backup
LOCK TABLES `core_backup` WRITE;
INSERT INTO `core_backup` (`id`, `retailer_id`, `backup_filename`, `backup_path`, `backup_date`, `status`, `file_size`) VALUES (5, 1, 'backup_medicvista_retailer_20260613_221132.sql', 'C:\\wholesaler project\\MEDICVISTA_RETAILER\\Medicvist_retailer\\backups\\backup_medicvista_retailer_20260613_221132.sql', '2026-06-13 22:11:33', 'Success', '46.3 KB');
INSERT INTO `core_backup` (`id`, `retailer_id`, `backup_filename`, `backup_path`, `backup_date`, `status`, `file_size`) VALUES (6, 1, 'backup_medicvista_retailer_20260618_122909.sql', 'C:\\wholesaler project\\MEDICVISTA_RETAILER\\Medicvist_retailer\\backups\\backup_medicvista_retailer_20260618_122909.sql', '2026-06-18 12:29:10', 'Success', '44.2 KB');
UNLOCK TABLES;

-- Table: retailer_users
LOCK TABLES `retailer_users` WRITE;
INSERT INTO `retailer_users` (`id`, `retailer_id`, `username`, `password`, `full_name`, `is_active`, `created_at`) VALUES (14, 1, 'retailer1', 'retailer1', 'BSL Pharmacy', 1, '2026-06-12 17:25:04');
INSERT INTO `retailer_users` (`id`, `retailer_id`, `username`, `password`, `full_name`, `is_active`, `created_at`) VALUES (15, 2, 'retailer2', 'retailer2', 'MedPlus Retail', 1, '2026-06-12 17:25:04');
INSERT INTO `retailer_users` (`id`, `retailer_id`, `username`, `password`, `full_name`, `is_active`, `created_at`) VALUES (16, 3, 'retailer3', 'retailer3', 'Apollo Pharmacy', 1, '2026-06-12 17:25:04');
INSERT INTO `retailer_users` (`id`, `retailer_id`, `username`, `password`, `full_name`, `is_active`, `created_at`) VALUES (17, 4, 'retailer4', 'retailer4', 'Wellness Forever', 1, '2026-06-12 17:25:04');
UNLOCK TABLES;

SET FOREIGN_KEY_CHECKS=1;
