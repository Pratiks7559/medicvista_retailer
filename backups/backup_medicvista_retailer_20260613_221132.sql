-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: medicvista_retailer
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `batch_inventory_cache`
--

DROP TABLE IF EXISTS `batch_inventory_cache`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `batch_inventory_cache` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `product_id` bigint NOT NULL,
  `retailer_id` bigint DEFAULT NULL,
  `batch_no` varchar(20) NOT NULL,
  `expiry_date` varchar(7) NOT NULL,
  `current_stock` float NOT NULL DEFAULT '0',
  `current_free_qty` float NOT NULL DEFAULT '0',
  `total_stock` float NOT NULL DEFAULT '0',
  `mrp` float NOT NULL DEFAULT '0',
  `purchase_rate` float NOT NULL DEFAULT '0',
  `rate_a` float NOT NULL DEFAULT '0',
  `rate_b` float NOT NULL DEFAULT '0',
  `rate_c` float NOT NULL DEFAULT '0',
  `is_expired` tinyint(1) NOT NULL DEFAULT '0',
  `expiry_status` varchar(20) NOT NULL DEFAULT 'valid',
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_product` (`product_id`),
  KEY `idx_retailer` (`retailer_id`),
  KEY `idx_batch` (`batch_no`),
  KEY `idx_expiry_status` (`expiry_status`),
  CONSTRAINT `batch_inventory_cache_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `core_productmaster` (`productid`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `batch_inventory_cache`
--

LOCK TABLES `batch_inventory_cache` WRITE;
/*!40000 ALTER TABLE `batch_inventory_cache` DISABLE KEYS */;
INSERT INTO `batch_inventory_cache` VALUES (30,107,1,'121','12-2026',18,0,18,5,2,1,2,3,0,'valid','2026-06-12 22:58:12'),(31,107,1,'110','12-2029',90,0,90,5,2,1,2,3,0,'valid','2026-06-12 18:04:26'),(32,107,1,'101','12-2029',210,0,210,5,2,0,0,0,0,'valid','2026-06-13 15:04:47');
/*!40000 ALTER TABLE `batch_inventory_cache` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `challan1`
--

DROP TABLE IF EXISTS `challan1`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `challan1` (
  `challan_id` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint DEFAULT NULL,
  `challan_no` varchar(50) NOT NULL,
  `challan_date` date NOT NULL,
  `supplier_id_id` bigint NOT NULL,
  `challan_total` float NOT NULL DEFAULT '0',
  `transport_charges` float NOT NULL DEFAULT '0',
  `challan_paid` float NOT NULL DEFAULT '0',
  `challan_remark` longtext NOT NULL,
  `is_invoiced` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`challan_id`),
  UNIQUE KEY `challan_no` (`challan_no`),
  KEY `idx_challan_no` (`challan_no`),
  KEY `idx_supplier` (`supplier_id_id`),
  KEY `idx_retailer` (`retailer_id`),
  KEY `idx_challan_date` (`challan_date`),
  CONSTRAINT `challan1_ibfk_1` FOREIGN KEY (`supplier_id_id`) REFERENCES `core_suppliermaster` (`supplierid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `challan1`
--

LOCK TABLES `challan1` WRITE;
/*!40000 ALTER TABLE `challan1` DISABLE KEYS */;
/*!40000 ALTER TABLE `challan1` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `contra_entry`
--

DROP TABLE IF EXISTS `contra_entry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contra_entry` (
  `contra_id` bigint NOT NULL AUTO_INCREMENT,
  `contra_no` varchar(20) NOT NULL,
  `contra_date` date NOT NULL,
  `contra_type` varchar(20) NOT NULL,
  `amount` float NOT NULL,
  `from_account` varchar(100) NOT NULL,
  `to_account` varchar(100) NOT NULL,
  `reference_no` varchar(50) DEFAULT NULL,
  `narration` longtext,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`contra_id`),
  UNIQUE KEY `contra_no` (`contra_no`),
  KEY `idx_contra_no` (`contra_no`),
  KEY `idx_contra_date` (`contra_date`),
  KEY `idx_amount` (`amount`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contra_entry`
--

LOCK TABLES `contra_entry` WRITE;
/*!40000 ALTER TABLE `contra_entry` DISABLE KEYS */;
/*!40000 ALTER TABLE `contra_entry` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_backup`
--

DROP TABLE IF EXISTS `core_backup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_backup` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint DEFAULT NULL,
  `backup_filename` varchar(255) NOT NULL,
  `backup_path` varchar(500) NOT NULL,
  `backup_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(50) DEFAULT 'Success',
  `file_size` varchar(50) DEFAULT '0 KB',
  PRIMARY KEY (`id`),
  KEY `idx_retailer` (`retailer_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_backup`
--

LOCK TABLES `core_backup` WRITE;
/*!40000 ALTER TABLE `core_backup` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_backup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_customermaster`
--

DROP TABLE IF EXISTS `core_customermaster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_customermaster` (
  `customerid` bigint NOT NULL AUTO_INCREMENT,
  `customer_name` varchar(200) NOT NULL DEFAULT 'NA',
  `customer_type` varchar(200) DEFAULT 'TYPE-A',
  `customer_address` varchar(200) DEFAULT 'NA',
  `customer_mobile` varchar(15) DEFAULT 'NA',
  `customer_whatsapp` varchar(15) DEFAULT 'NA',
  `customer_emailid` varchar(60) DEFAULT 'NA',
  `customer_spoc` varchar(100) DEFAULT 'NA',
  `customer_dlno` varchar(30) DEFAULT 'NA',
  `customer_gstno` varchar(20) DEFAULT 'NA',
  `customer_food_license_no` varchar(30) DEFAULT 'NA',
  `customer_credit_days` int NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`customerid`),
  KEY `idx_customer_name` (`customer_name`),
  KEY `idx_customer_mobile` (`customer_mobile`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_customermaster`
--

LOCK TABLES `core_customermaster` WRITE;
/*!40000 ALTER TABLE `core_customermaster` DISABLE KEYS */;
INSERT INTO `core_customermaster` VALUES (3,'fak1','TYPE-A','','','','','','','','',0,'2026-06-12 22:52:56');
/*!40000 ALTER TABLE `core_customermaster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_invoicemaster`
--

DROP TABLE IF EXISTS `core_invoicemaster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_invoicemaster` (
  `invoiceid` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint DEFAULT NULL,
  `invoice_no` varchar(20) NOT NULL,
  `invoice_date` date NOT NULL,
  `supplierid_id` bigint NOT NULL,
  `transport_charges` float NOT NULL DEFAULT '0',
  `invoice_total` float NOT NULL DEFAULT '0',
  `invoice_paid` float NOT NULL DEFAULT '0',
  `payment_status` varchar(20) NOT NULL DEFAULT 'pending',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`invoiceid`),
  KEY `idx_invoice_no` (`invoice_no`),
  KEY `idx_invoice_date` (`invoice_date`),
  KEY `idx_supplier` (`supplierid_id`),
  KEY `idx_retailer` (`retailer_id`),
  KEY `idx_status` (`payment_status`),
  CONSTRAINT `core_invoicemaster_ibfk_1` FOREIGN KEY (`supplierid_id`) REFERENCES `core_suppliermaster` (`supplierid`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_invoicemaster`
--

LOCK TABLES `core_invoicemaster` WRITE;
/*!40000 ALTER TABLE `core_invoicemaster` DISABLE KEYS */;
INSERT INTO `core_invoicemaster` VALUES (10,1,'12','2026-06-13',3,0,4.2,0,'pending','2026-06-13 14:03:59');
/*!40000 ALTER TABLE `core_invoicemaster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_invoicepaid`
--

DROP TABLE IF EXISTS `core_invoicepaid`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_invoicepaid` (
  `payment_id` bigint NOT NULL AUTO_INCREMENT,
  `ip_invoiceid_id` bigint NOT NULL,
  `payment_date` date NOT NULL,
  `payment_amount` float NOT NULL DEFAULT '0',
  `payment_mode` varchar(30) DEFAULT NULL,
  `payment_ref_no` varchar(30) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`payment_id`),
  KEY `idx_invoice` (`ip_invoiceid_id`),
  CONSTRAINT `core_invoicepaid_ibfk_1` FOREIGN KEY (`ip_invoiceid_id`) REFERENCES `core_invoicemaster` (`invoiceid`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_invoicepaid`
--

LOCK TABLES `core_invoicepaid` WRITE;
/*!40000 ALTER TABLE `core_invoicepaid` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_invoicepaid` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_invoiceseries`
--

DROP TABLE IF EXISTS `core_invoiceseries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_invoiceseries` (
  `series_id` bigint NOT NULL AUTO_INCREMENT,
  `series_name` varchar(10) NOT NULL,
  `series_prefix` varchar(5) DEFAULT NULL,
  `current_number` int NOT NULL DEFAULT '1',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_date` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`series_id`),
  UNIQUE KEY `series_name` (`series_name`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_invoiceseries`
--

LOCK TABLES `core_invoiceseries` WRITE;
/*!40000 ALTER TABLE `core_invoiceseries` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_invoiceseries` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_productmaster`
--

DROP TABLE IF EXISTS `core_productmaster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_productmaster` (
  `productid` bigint NOT NULL AUTO_INCREMENT,
  `product_name` varchar(200) NOT NULL,
  `product_company` varchar(200) NOT NULL,
  `product_packing` varchar(20) NOT NULL,
  `product_image` varchar(100) DEFAULT 'images/medicine_default.png',
  `product_salt` varchar(300) DEFAULT NULL,
  `product_category` varchar(30) DEFAULT NULL,
  `product_hsn` varchar(20) DEFAULT NULL,
  `product_hsn_percent` varchar(20) DEFAULT NULL,
  `product_barcode` varchar(50) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`productid`),
  UNIQUE KEY `product_barcode` (`product_barcode`),
  KEY `idx_product_name` (`product_name`),
  KEY `idx_product_company` (`product_company`)
) ENGINE=InnoDB AUTO_INCREMENT=108 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_productmaster`
--

LOCK TABLES `core_productmaster` WRITE;
/*!40000 ALTER TABLE `core_productmaster` DISABLE KEYS */;
INSERT INTO `core_productmaster` VALUES (107,'amox','amxo','10','images/medicine_default.png','','','','','','2026-06-12 17:26:34');
/*!40000 ALTER TABLE `core_productmaster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_purchasemaster`
--

DROP TABLE IF EXISTS `core_purchasemaster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_purchasemaster` (
  `purchaseid` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint DEFAULT NULL,
  `product_supplierid_id` bigint NOT NULL,
  `product_invoiceid_id` bigint NOT NULL,
  `product_invoice_no` varchar(20) NOT NULL,
  `productid_id` bigint NOT NULL,
  `product_name` varchar(200) NOT NULL,
  `product_company` varchar(200) NOT NULL,
  `product_packing` varchar(20) NOT NULL,
  `product_batch_no` varchar(20) NOT NULL,
  `product_expiry` varchar(7) NOT NULL,
  `product_MRP` float NOT NULL DEFAULT '0',
  `product_purchase_rate` float NOT NULL DEFAULT '0',
  `product_quantity` float NOT NULL DEFAULT '0',
  `product_free_qty` float NOT NULL DEFAULT '0',
  `product_scheme` float NOT NULL DEFAULT '0',
  `product_discount_got` float NOT NULL DEFAULT '0',
  `product_transportation_charges` float NOT NULL DEFAULT '0',
  `actual_rate_per_qty` float NOT NULL DEFAULT '0',
  `product_actual_rate` float NOT NULL DEFAULT '0',
  `total_amount` float NOT NULL DEFAULT '0',
  `purchase_entry_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `CGST` float NOT NULL DEFAULT '0',
  `SGST` float NOT NULL DEFAULT '0',
  `purchase_calculation_mode` varchar(5) NOT NULL DEFAULT 'flat',
  `rate_a` float DEFAULT '0',
  `rate_b` float DEFAULT '0',
  `rate_c` float DEFAULT '0',
  `source_challan_no` varchar(50) DEFAULT NULL,
  `source_challan_date` date DEFAULT NULL,
  PRIMARY KEY (`purchaseid`),
  KEY `product_supplierid_id` (`product_supplierid_id`),
  KEY `idx_invoice` (`product_invoiceid_id`),
  KEY `idx_product` (`productid_id`),
  KEY `idx_batch` (`product_batch_no`),
  CONSTRAINT `core_purchasemaster_ibfk_1` FOREIGN KEY (`product_invoiceid_id`) REFERENCES `core_invoicemaster` (`invoiceid`),
  CONSTRAINT `core_purchasemaster_ibfk_2` FOREIGN KEY (`productid_id`) REFERENCES `core_productmaster` (`productid`),
  CONSTRAINT `core_purchasemaster_ibfk_3` FOREIGN KEY (`product_supplierid_id`) REFERENCES `core_suppliermaster` (`supplierid`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_purchasemaster`
--

LOCK TABLES `core_purchasemaster` WRITE;
/*!40000 ALTER TABLE `core_purchasemaster` DISABLE KEYS */;
INSERT INTO `core_purchasemaster` VALUES (16,1,3,10,'12',107,'amox','amxo','10','101','12-2026',5,2,2,2,0,0,0,2,2,4.2,'2026-06-13 14:03:59',2.5,2.5,'flat',0,0,0,NULL,NULL);
/*!40000 ALTER TABLE `core_purchasemaster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_retailer`
--

DROP TABLE IF EXISTS `core_retailer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_retailer` (
  `retailer_id` bigint NOT NULL AUTO_INCREMENT,
  `retailer_name` varchar(200) NOT NULL,
  `store_code` varchar(50) NOT NULL,
  `address` longtext,
  `contact` varchar(20) DEFAULT '',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`retailer_id`),
  UNIQUE KEY `store_code` (`store_code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_retailer`
--

LOCK TABLES `core_retailer` WRITE;
/*!40000 ALTER TABLE `core_retailer` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_retailer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_returninvoicemaster`
--

DROP TABLE IF EXISTS `core_returninvoicemaster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_returninvoicemaster` (
  `returninvoiceid` varchar(20) NOT NULL,
  `retailer_id` bigint DEFAULT NULL,
  `returninvoice_date` date NOT NULL,
  `returnsupplierid_id` bigint NOT NULL,
  `return_charges` float NOT NULL DEFAULT '0',
  `returninvoice_total` float NOT NULL DEFAULT '0',
  `returninvoice_paid` float NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`returninvoiceid`),
  KEY `idx_supplier` (`returnsupplierid_id`),
  CONSTRAINT `core_returninvoicemaster_ibfk_1` FOREIGN KEY (`returnsupplierid_id`) REFERENCES `core_suppliermaster` (`supplierid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_returninvoicemaster`
--

LOCK TABLES `core_returninvoicemaster` WRITE;
/*!40000 ALTER TABLE `core_returninvoicemaster` DISABLE KEYS */;
INSERT INTO `core_returninvoicemaster` VALUES ('2345',1,'2026-06-13',3,0,10.5,0,'2026-06-13 14:10:25');
/*!40000 ALTER TABLE `core_returninvoicemaster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_returnpurchasemaster`
--

DROP TABLE IF EXISTS `core_returnpurchasemaster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_returnpurchasemaster` (
  `returnpurchaseid` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint DEFAULT NULL,
  `returninvoiceid_id` varchar(20) NOT NULL,
  `returnproduct_supplierid_id` bigint NOT NULL,
  `returnproductid_id` bigint NOT NULL,
  `returnproduct_batch_no` varchar(20) NOT NULL,
  `returnproduct_expiry` varchar(7) NOT NULL,
  `returnproduct_MRP` float NOT NULL DEFAULT '0',
  `returnproduct_purchase_rate` float NOT NULL DEFAULT '0',
  `returnproduct_quantity` float NOT NULL DEFAULT '0',
  `returnproduct_free_qty` float NOT NULL DEFAULT '0',
  `returnproduct_cgst` float NOT NULL DEFAULT '2.5',
  `returnproduct_sgst` float NOT NULL DEFAULT '2.5',
  `returntotal_amount` float NOT NULL DEFAULT '0',
  `return_reason` varchar(200) DEFAULT NULL,
  `returnpurchase_entry_date` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`returnpurchaseid`),
  KEY `returnproductid_id` (`returnproductid_id`),
  KEY `returnproduct_supplierid_id` (`returnproduct_supplierid_id`),
  KEY `idx_return_invoice` (`returninvoiceid_id`),
  CONSTRAINT `core_returnpurchasemaster_ibfk_1` FOREIGN KEY (`returninvoiceid_id`) REFERENCES `core_returninvoicemaster` (`returninvoiceid`),
  CONSTRAINT `core_returnpurchasemaster_ibfk_2` FOREIGN KEY (`returnproductid_id`) REFERENCES `core_productmaster` (`productid`),
  CONSTRAINT `core_returnpurchasemaster_ibfk_3` FOREIGN KEY (`returnproduct_supplierid_id`) REFERENCES `core_suppliermaster` (`supplierid`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_returnpurchasemaster`
--

LOCK TABLES `core_returnpurchasemaster` WRITE;
/*!40000 ALTER TABLE `core_returnpurchasemaster` DISABLE KEYS */;
INSERT INTO `core_returnpurchasemaster` VALUES (2,1,'2345',3,107,'101','12-2026',5,2,5,2,2.5,2.5,10.5,'','2026-06-13 14:10:25');
/*!40000 ALTER TABLE `core_returnpurchasemaster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_returnsalesinvoicemaster`
--

DROP TABLE IF EXISTS `core_returnsalesinvoicemaster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_returnsalesinvoicemaster` (
  `return_sales_invoice_no` varchar(20) NOT NULL,
  `retailer_id` bigint DEFAULT NULL,
  `return_sales_invoice_date` date NOT NULL,
  `return_sales_customerid_id` bigint NOT NULL,
  `return_sales_charges` float NOT NULL DEFAULT '0',
  `transport_charges` float NOT NULL DEFAULT '0',
  `sales_invoice_no_id` bigint DEFAULT NULL,
  `return_sales_invoice_total` float NOT NULL,
  `return_sales_invoice_paid` float NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`return_sales_invoice_no`),
  KEY `idx_customer` (`return_sales_customerid_id`),
  CONSTRAINT `core_returnsalesinvoicemaster_ibfk_1` FOREIGN KEY (`return_sales_customerid_id`) REFERENCES `core_customermaster` (`customerid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_returnsalesinvoicemaster`
--

LOCK TABLES `core_returnsalesinvoicemaster` WRITE;
/*!40000 ALTER TABLE `core_returnsalesinvoicemaster` DISABLE KEYS */;
INSERT INTO `core_returnsalesinvoicemaster` VALUES ('16',1,'2026-06-13',3,0,0,NULL,6.3,0,'2026-06-13 15:04:47');
/*!40000 ALTER TABLE `core_returnsalesinvoicemaster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_returnsalesmaster`
--

DROP TABLE IF EXISTS `core_returnsalesmaster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_returnsalesmaster` (
  `return_sales_id` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint DEFAULT NULL,
  `return_sales_invoice_no_id` varchar(20) NOT NULL,
  `return_customerid_id` bigint NOT NULL,
  `return_productid_id` bigint NOT NULL,
  `return_product_name` varchar(200) NOT NULL DEFAULT 'NA',
  `return_product_company` varchar(200) DEFAULT 'NA',
  `return_product_packing` varchar(20) DEFAULT 'NA',
  `return_product_batch_no` varchar(20) NOT NULL,
  `return_product_expiry` varchar(7) NOT NULL,
  `return_product_MRP` float NOT NULL DEFAULT '0',
  `return_sale_rate` float NOT NULL DEFAULT '0',
  `return_sale_quantity` float NOT NULL DEFAULT '0',
  `return_sale_free_qty` float NOT NULL DEFAULT '0',
  `return_sale_scheme` float NOT NULL DEFAULT '0',
  `return_sale_discount` float NOT NULL DEFAULT '0',
  `return_sale_cgst` float NOT NULL DEFAULT '0',
  `return_sale_sgst` float NOT NULL DEFAULT '0',
  `return_sale_total_amount` float NOT NULL DEFAULT '0',
  `return_reason` varchar(200) DEFAULT NULL,
  `return_sale_entry_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `return_sale_calculation_mode` varchar(20) NOT NULL DEFAULT 'percentage',
  PRIMARY KEY (`return_sales_id`),
  KEY `return_customerid_id` (`return_customerid_id`),
  KEY `return_productid_id` (`return_productid_id`),
  KEY `idx_return_invoice` (`return_sales_invoice_no_id`),
  CONSTRAINT `core_returnsalesmaster_ibfk_1` FOREIGN KEY (`return_sales_invoice_no_id`) REFERENCES `core_returnsalesinvoicemaster` (`return_sales_invoice_no`),
  CONSTRAINT `core_returnsalesmaster_ibfk_2` FOREIGN KEY (`return_customerid_id`) REFERENCES `core_customermaster` (`customerid`),
  CONSTRAINT `core_returnsalesmaster_ibfk_3` FOREIGN KEY (`return_productid_id`) REFERENCES `core_productmaster` (`productid`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_returnsalesmaster`
--

LOCK TABLES `core_returnsalesmaster` WRITE;
/*!40000 ALTER TABLE `core_returnsalesmaster` DISABLE KEYS */;
INSERT INTO `core_returnsalesmaster` VALUES (2,1,'16',3,107,'amox','amxo','10','101','12-2026',5,2,3,0,0,0,2.5,2.5,6.3,'','2026-06-13 15:04:47','flat');
/*!40000 ALTER TABLE `core_returnsalesmaster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_salesinvoicemaster`
--

DROP TABLE IF EXISTS `core_salesinvoicemaster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_salesinvoicemaster` (
  `sales_invoice_no` varchar(20) NOT NULL,
  `retailer_id` bigint DEFAULT NULL,
  `sales_invoice_date` date NOT NULL,
  `customerid_id` bigint NOT NULL,
  `invoice_series_id` bigint DEFAULT NULL,
  `sales_transport_charges` float NOT NULL DEFAULT '0',
  `sales_invoice_paid` float NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_invoice_no`),
  KEY `invoice_series_id` (`invoice_series_id`),
  KEY `idx_invoice_date` (`sales_invoice_date`),
  KEY `idx_customer` (`customerid_id`),
  KEY `idx_retailer` (`retailer_id`),
  KEY `idx_sales_date` (`sales_invoice_date`),
  CONSTRAINT `core_salesinvoicemaster_ibfk_1` FOREIGN KEY (`customerid_id`) REFERENCES `core_customermaster` (`customerid`),
  CONSTRAINT `core_salesinvoicemaster_ibfk_2` FOREIGN KEY (`invoice_series_id`) REFERENCES `core_invoiceseries` (`series_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_salesinvoicemaster`
--

LOCK TABLES `core_salesinvoicemaster` WRITE;
/*!40000 ALTER TABLE `core_salesinvoicemaster` DISABLE KEYS */;
INSERT INTO `core_salesinvoicemaster` VALUES ('INV0000001',1,'2026-06-13',3,NULL,0,0,'2026-06-13 15:00:58');
/*!40000 ALTER TABLE `core_salesinvoicemaster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_salesinvoicepaid`
--

DROP TABLE IF EXISTS `core_salesinvoicepaid`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_salesinvoicepaid` (
  `sales_payment_id` bigint NOT NULL AUTO_INCREMENT,
  `sales_ip_invoice_no_id` varchar(20) NOT NULL,
  `sales_payment_date` date NOT NULL,
  `sales_payment_amount` float NOT NULL DEFAULT '0',
  `sales_payment_mode` varchar(30) NOT NULL DEFAULT 'NA',
  `sales_payment_ref_no` varchar(30) NOT NULL DEFAULT 'NA',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_payment_id`),
  KEY `idx_invoice` (`sales_ip_invoice_no_id`),
  CONSTRAINT `core_salesinvoicepaid_ibfk_1` FOREIGN KEY (`sales_ip_invoice_no_id`) REFERENCES `core_salesinvoicemaster` (`sales_invoice_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_salesinvoicepaid`
--

LOCK TABLES `core_salesinvoicepaid` WRITE;
/*!40000 ALTER TABLE `core_salesinvoicepaid` DISABLE KEYS */;
/*!40000 ALTER TABLE `core_salesinvoicepaid` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_salesmaster`
--

DROP TABLE IF EXISTS `core_salesmaster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_salesmaster` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint DEFAULT NULL,
  `sales_invoice_no_id` varchar(20) NOT NULL,
  `customerid_id` bigint NOT NULL,
  `productid_id` bigint NOT NULL,
  `product_name` varchar(200) NOT NULL DEFAULT 'NA',
  `product_company` varchar(200) DEFAULT 'NA',
  `product_packing` varchar(20) DEFAULT 'NA',
  `product_batch_no` varchar(20) NOT NULL,
  `product_expiry` varchar(7) NOT NULL,
  `product_MRP` float NOT NULL DEFAULT '0',
  `sale_rate` float NOT NULL DEFAULT '0',
  `sale_quantity` float NOT NULL DEFAULT '0',
  `sale_free_qty` float NOT NULL DEFAULT '0',
  `sale_scheme` float NOT NULL DEFAULT '0',
  `sale_discount` float NOT NULL DEFAULT '0',
  `sale_cgst` float NOT NULL DEFAULT '0',
  `sale_sgst` float NOT NULL DEFAULT '0',
  `sale_total_amount` float NOT NULL DEFAULT '0',
  `sale_entry_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `rate_applied` varchar(10) DEFAULT 'NA',
  `sale_calculation_mode` varchar(5) NOT NULL DEFAULT 'flat',
  `source_challan_no` varchar(50) DEFAULT NULL,
  `source_challan_date` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_invoice` (`sales_invoice_no_id`),
  KEY `idx_customer` (`customerid_id`),
  KEY `idx_product` (`productid_id`),
  KEY `idx_batch` (`product_batch_no`),
  CONSTRAINT `core_salesmaster_ibfk_1` FOREIGN KEY (`sales_invoice_no_id`) REFERENCES `core_salesinvoicemaster` (`sales_invoice_no`),
  CONSTRAINT `core_salesmaster_ibfk_2` FOREIGN KEY (`customerid_id`) REFERENCES `core_customermaster` (`customerid`),
  CONSTRAINT `core_salesmaster_ibfk_3` FOREIGN KEY (`productid_id`) REFERENCES `core_productmaster` (`productid`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_salesmaster`
--

LOCK TABLES `core_salesmaster` WRITE;
/*!40000 ALTER TABLE `core_salesmaster` DISABLE KEYS */;
INSERT INTO `core_salesmaster` VALUES (17,1,'INV0000001',3,107,'amox','amxo','10','101','12-2026',5,2,12,0,0,0,2.5,2.5,63,'2026-06-13 15:00:58','A','flat',NULL,NULL);
/*!40000 ALTER TABLE `core_salesmaster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_suppliermaster`
--

DROP TABLE IF EXISTS `core_suppliermaster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_suppliermaster` (
  `supplierid` bigint NOT NULL AUTO_INCREMENT,
  `supplier_name` varchar(200) NOT NULL,
  `supplier_type` varchar(200) DEFAULT '',
  `supplier_address` varchar(200) DEFAULT '',
  `supplier_mobile` varchar(15) NOT NULL,
  `supplier_whatsapp` varchar(15) DEFAULT '',
  `supplier_emailid` varchar(60) DEFAULT '',
  `supplier_spoc` varchar(100) DEFAULT '',
  `supplier_dlno` varchar(30) DEFAULT '',
  `supplier_gstno` varchar(20) DEFAULT '',
  `supplier_bank` varchar(200) DEFAULT '',
  `supplier_branch` varchar(200) DEFAULT 'NA',
  `supplier_bankaccountno` varchar(30) DEFAULT '',
  `supplier_bankifsc` varchar(20) DEFAULT '',
  `supplier_upi` varchar(50) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`supplierid`),
  KEY `idx_supplier_name` (`supplier_name`),
  KEY `idx_supplier_mobile` (`supplier_mobile`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_suppliermaster`
--

LOCK TABLES `core_suppliermaster` WRITE;
/*!40000 ALTER TABLE `core_suppliermaster` DISABLE KEYS */;
INSERT INTO `core_suppliermaster` VALUES (3,'fake','fake','','958888888888','','','','','','','','','','','2026-06-12 17:25:59');
/*!40000 ALTER TABLE `core_suppliermaster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customer_challan`
--

DROP TABLE IF EXISTS `customer_challan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_challan` (
  `customer_challan_id` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint DEFAULT NULL,
  `customer_challan_no` varchar(50) NOT NULL,
  `customer_challan_date` date NOT NULL,
  `customer_name_id_id` bigint NOT NULL,
  `challan_series_id` bigint DEFAULT NULL,
  `customer_transport_charges` float NOT NULL DEFAULT '0',
  `challan_total` float NOT NULL DEFAULT '0',
  `challan_invoice_paid` float NOT NULL DEFAULT '0',
  `is_invoiced` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`customer_challan_id`),
  UNIQUE KEY `customer_challan_no` (`customer_challan_no`),
  KEY `idx_customer` (`customer_name_id_id`),
  KEY `idx_retailer` (`retailer_id`),
  CONSTRAINT `customer_challan_ibfk_1` FOREIGN KEY (`customer_name_id_id`) REFERENCES `core_customermaster` (`customerid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer_challan`
--

LOCK TABLES `customer_challan` WRITE;
/*!40000 ALTER TABLE `customer_challan` DISABLE KEYS */;
/*!40000 ALTER TABLE `customer_challan` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customer_challan_master`
--

DROP TABLE IF EXISTS `customer_challan_master`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_challan_master` (
  `customer_challan_master_id` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint DEFAULT NULL,
  `customer_challan_id` bigint NOT NULL,
  `customer_challan_no` varchar(50) NOT NULL,
  `customer_name_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  `product_name` varchar(200) NOT NULL,
  `product_company` varchar(200) NOT NULL,
  `product_packing` varchar(20) NOT NULL,
  `product_batch_no` varchar(20) NOT NULL,
  `product_expiry` varchar(7) NOT NULL,
  `product_mrp` float NOT NULL,
  `sale_rate` float NOT NULL,
  `sale_quantity` float NOT NULL,
  `sale_free_qty` float NOT NULL DEFAULT '0',
  `sale_discount` float NOT NULL DEFAULT '0',
  `sale_cgst` float NOT NULL DEFAULT '2.5',
  `sale_sgst` float NOT NULL DEFAULT '2.5',
  `sale_total_amount` float NOT NULL,
  `sales_entry_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `rate_applied` varchar(10) DEFAULT 'NA',
  PRIMARY KEY (`customer_challan_master_id`),
  KEY `customer_name_id` (`customer_name_id`),
  KEY `product_id` (`product_id`),
  KEY `idx_challan` (`customer_challan_id`),
  CONSTRAINT `customer_challan_master_ibfk_1` FOREIGN KEY (`customer_challan_id`) REFERENCES `customer_challan` (`customer_challan_id`),
  CONSTRAINT `customer_challan_master_ibfk_2` FOREIGN KEY (`customer_name_id`) REFERENCES `core_customermaster` (`customerid`),
  CONSTRAINT `customer_challan_master_ibfk_3` FOREIGN KEY (`product_id`) REFERENCES `core_productmaster` (`productid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer_challan_master`
--

LOCK TABLES `customer_challan_master` WRITE;
/*!40000 ALTER TABLE `customer_challan_master` DISABLE KEYS */;
/*!40000 ALTER TABLE `customer_challan_master` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventory_transaction`
--

DROP TABLE IF EXISTS `inventory_transaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inventory_transaction` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint DEFAULT NULL,
  `product_id` bigint NOT NULL,
  `batch_no` varchar(100) DEFAULT '',
  `expiry_date` varchar(20) DEFAULT '',
  `transaction_type` varchar(50) NOT NULL,
  `quantity` decimal(12,3) DEFAULT '0.000',
  `free_quantity` decimal(12,3) DEFAULT '0.000',
  `transaction_date` datetime DEFAULT NULL,
  `reference_type` varchar(50) DEFAULT '',
  `reference_id` bigint DEFAULT '0',
  `reference_number` varchar(100) DEFAULT '',
  `rate` decimal(12,4) DEFAULT '0.0000',
  `mrp` decimal(12,4) DEFAULT '0.0000',
  `total_value` decimal(14,2) DEFAULT '0.00',
  `created_at` datetime DEFAULT NULL,
  `created_by_id` bigint DEFAULT NULL,
  `remarks` varchar(1000) DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `idx_retailer_product` (`retailer_id`,`product_id`),
  KEY `idx_transaction_type` (`transaction_type`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventory_transaction`
--

LOCK TABLES `inventory_transaction` WRITE;
/*!40000 ALTER TABLE `inventory_transaction` DISABLE KEYS */;
INSERT INTO `inventory_transaction` VALUES (1,1,107,'101','12-2026','PURCHASE',20.000,2.000,'2026-06-13 14:03:59','INVOICE',10,'12',2.0000,5.0000,4.20,'2026-06-13 14:03:59',NULL,'Purchase Invoice 12 (packing x10)'),(2,1,107,'101','12-2026','PURCHASE_RETURN',5.000,2.000,'2026-06-13 14:10:26','PURCHASE_RETURN',0,'2345',2.0000,5.0000,10.50,'2026-06-13 14:10:26',NULL,'Purchase Return 2345'),(4,1,107,'101','12-2026','SALE',12.000,0.000,'2026-06-13 15:00:58','INVOICE',0,'INV0000001',2.0000,5.0000,63.00,'2026-06-13 15:00:58',NULL,'Sales Invoice INV0000001'),(5,1,107,'101','12-2026','SALES_RETURN',3.000,0.000,'2026-06-13 15:04:47','SALES_RETURN',0,'16',2.0000,5.0000,6.30,'2026-06-13 15:04:47',NULL,'Sales Return 16');
/*!40000 ALTER TABLE `inventory_transaction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `retailer_pending_status_updates`
--

DROP TABLE IF EXISTS `retailer_pending_status_updates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `retailer_pending_status_updates` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `request_id` bigint NOT NULL,
  `new_status` varchar(30) NOT NULL,
  `queued_at` datetime NOT NULL,
  `attempt_count` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_queued_at` (`queued_at`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `retailer_pending_status_updates`
--

LOCK TABLES `retailer_pending_status_updates` WRITE;
/*!40000 ALTER TABLE `retailer_pending_status_updates` DISABLE KEYS */;
/*!40000 ALTER TABLE `retailer_pending_status_updates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `retailer_report_data_cache`
--

DROP TABLE IF EXISTS `retailer_report_data_cache`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `retailer_report_data_cache` (
  `request_id` bigint NOT NULL,
  `request_type` varchar(30) NOT NULL,
  `from_date` varchar(20) NOT NULL,
  `to_date` varchar(20) NOT NULL,
  `generated_at` datetime NOT NULL,
  `data_json` longtext NOT NULL,
  `fetched_at` datetime NOT NULL,
  PRIMARY KEY (`request_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `retailer_report_data_cache`
--

LOCK TABLES `retailer_report_data_cache` WRITE;
/*!40000 ALTER TABLE `retailer_report_data_cache` DISABLE KEYS */;
/*!40000 ALTER TABLE `retailer_report_data_cache` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `retailer_request`
--

DROP TABLE IF EXISTS `retailer_request`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `retailer_request` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint NOT NULL,
  `request_type` varchar(20) NOT NULL,
  `reference_id` bigint DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'Pending',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `processed_at` datetime DEFAULT NULL,
  `remarks` longtext,
  `from_date` varchar(20) DEFAULT '',
  `to_date` varchar(20) DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `idx_retailer` (`retailer_id`),
  KEY `idx_status` (`status`),
  KEY `idx_request_type` (`request_type`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `retailer_request`
--

LOCK TABLES `retailer_request` WRITE;
/*!40000 ALTER TABLE `retailer_request` DISABLE KEYS */;
/*!40000 ALTER TABLE `retailer_request` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `retailer_users`
--

DROP TABLE IF EXISTS `retailer_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `retailer_users` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint NOT NULL,
  `username` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `full_name` varchar(200) DEFAULT '',
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `idx_retailer` (`retailer_id`),
  KEY `idx_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `retailer_users`
--

LOCK TABLES `retailer_users` WRITE;
/*!40000 ALTER TABLE `retailer_users` DISABLE KEYS */;
INSERT INTO `retailer_users` VALUES (14,1,'retailer1','retailer1','BSL Pharmacy',1,'2026-06-12 17:25:04'),(15,2,'retailer2','retailer2','MedPlus Retail',1,'2026-06-12 17:25:04'),(16,3,'retailer3','retailer3','Apollo Pharmacy',1,'2026-06-12 17:25:04'),(17,4,'retailer4','retailer4','Wellness Forever',1,'2026-06-12 17:25:04');
/*!40000 ALTER TABLE `retailer_users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_issue_detail`
--

DROP TABLE IF EXISTS `stock_issue_detail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock_issue_detail` (
  `detail_id` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint DEFAULT NULL,
  `issue_id_id` bigint NOT NULL,
  `product_id_id` bigint NOT NULL,
  `batch_no` varchar(20) NOT NULL,
  `expiry_date` varchar(7) NOT NULL,
  `quantity_issued` float NOT NULL,
  `unit_rate` float NOT NULL DEFAULT '0',
  `total_amount` float NOT NULL DEFAULT '0',
  `remarks` longtext,
  PRIMARY KEY (`detail_id`),
  KEY `product_id_id` (`product_id_id`),
  KEY `idx_issue` (`issue_id_id`),
  CONSTRAINT `stock_issue_detail_ibfk_1` FOREIGN KEY (`issue_id_id`) REFERENCES `stock_issue_master` (`issue_id`),
  CONSTRAINT `stock_issue_detail_ibfk_2` FOREIGN KEY (`product_id_id`) REFERENCES `core_productmaster` (`productid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_issue_detail`
--

LOCK TABLES `stock_issue_detail` WRITE;
/*!40000 ALTER TABLE `stock_issue_detail` DISABLE KEYS */;
/*!40000 ALTER TABLE `stock_issue_detail` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_issue_master`
--

DROP TABLE IF EXISTS `stock_issue_master`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock_issue_master` (
  `issue_id` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint DEFAULT NULL,
  `issue_no` varchar(20) NOT NULL,
  `issue_date` date NOT NULL,
  `issue_type` varchar(20) NOT NULL,
  `total_value` float NOT NULL DEFAULT '0',
  `remarks` longtext,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`issue_id`),
  UNIQUE KEY `issue_no` (`issue_no`),
  KEY `idx_issue_no` (`issue_no`),
  KEY `idx_retailer` (`retailer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_issue_master`
--

LOCK TABLES `stock_issue_master` WRITE;
/*!40000 ALTER TABLE `stock_issue_master` DISABLE KEYS */;
/*!40000 ALTER TABLE `stock_issue_master` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `supplier_challan_master`
--

DROP TABLE IF EXISTS `supplier_challan_master`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `supplier_challan_master` (
  `challan_id` bigint NOT NULL AUTO_INCREMENT,
  `retailer_id` bigint DEFAULT NULL,
  `product_suppliername_id` bigint NOT NULL,
  `product_challan_id` bigint NOT NULL,
  `product_challan_no` varchar(50) NOT NULL,
  `product_id` bigint NOT NULL,
  `product_name` varchar(200) NOT NULL,
  `product_company` varchar(200) NOT NULL,
  `product_packing` varchar(20) NOT NULL,
  `product_batch_no` varchar(20) NOT NULL,
  `product_expiry` varchar(7) NOT NULL,
  `product_mrp` float NOT NULL,
  `product_purchase_rate` float NOT NULL,
  `product_quantity` float NOT NULL,
  `product_free_qty` float NOT NULL DEFAULT '0',
  `product_scheme` float NOT NULL DEFAULT '0',
  `product_discount` float NOT NULL DEFAULT '0',
  `product_transportation_charges` float NOT NULL DEFAULT '0',
  `actual_rate_per_qty` float NOT NULL DEFAULT '0',
  `product_actual_rate` float NOT NULL DEFAULT '0',
  `total_amount` float NOT NULL DEFAULT '0',
  `challan_entry_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `cgst` float NOT NULL DEFAULT '2.5',
  `sgst` float NOT NULL DEFAULT '2.5',
  `challan_calculation_mode` varchar(10) NOT NULL DEFAULT 'flat',
  `rate_a` float DEFAULT '0',
  `rate_b` float DEFAULT '0',
  `rate_c` float DEFAULT '0',
  PRIMARY KEY (`challan_id`),
  KEY `product_id` (`product_id`),
  KEY `product_suppliername_id` (`product_suppliername_id`),
  KEY `idx_challan` (`product_challan_id`),
  CONSTRAINT `supplier_challan_master_ibfk_1` FOREIGN KEY (`product_challan_id`) REFERENCES `challan1` (`challan_id`),
  CONSTRAINT `supplier_challan_master_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `core_productmaster` (`productid`),
  CONSTRAINT `supplier_challan_master_ibfk_3` FOREIGN KEY (`product_suppliername_id`) REFERENCES `core_suppliermaster` (`supplierid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `supplier_challan_master`
--

LOCK TABLES `supplier_challan_master` WRITE;
/*!40000 ALTER TABLE `supplier_challan_master` DISABLE KEYS */;
/*!40000 ALTER TABLE `supplier_challan_master` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-13 22:11:33
