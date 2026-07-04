# Dual Database Configuration Guide

## 🎯 Architecture

MedicVista Retailer ab **2 databases** use karta hai:

### 1. Retailer App Database
- **Name**: `medicvista_retailer`
- **Purpose**: Purchase, Sales, Inventory, Customers, Suppliers
- **Location**: Always localhost
- **Size**: Retailer-specific data

### 2. Django ERP Database (Retailer Requests Only)
- **Name**: 
  - LOCAL: `pharma_db`
  - CLOUD: `medicvistapharma_db`
- **Purpose**: `retailer_request` table sync
- **Location**: localhost (MySQL)
- **Size**: Only request data

---

## 📋 Configuration Files

### config.ini (LOCAL)
```ini
[database]
name = medicvista_retailer    # Retailer's own data

[erp_database]
name = pharma_db              # Django ERP local database
```

### config_deploy.ini (CLOUD)
```ini
[database]
name = medicvista_retailer    # Retailer's own data

[erp_database]
name = medicvistapharma_db    # Django ERP cloud database
```

---

## 🔄 Switching Between Modes

### LOCAL Mode
```bash
.\switch_config.bat
# Choose option 1: LOCAL
```

**Result:**
- Retailer App → `medicvista_retailer`
- Retailer Requests → `pharma_db`
- Django Server → `http://127.0.0.1:8000`

### CLOUD Mode
```bash
.\switch_config.bat
# Choose option 2: CLOUD
```

**Result:**
- Retailer App → `medicvista_retailer`
- Retailer Requests → `medicvistapharma_db`
- Django Server → `https://medicvista.godaddysites.com`

---

## 🗄️ Database Separation

| Feature | Database | Why? |
|---------|----------|------|
| Products | medicvista_retailer | Retailer-specific |
| Inventory | medicvista_retailer | Retailer-specific |
| Sales | medicvista_retailer | Retailer-specific |
| Purchases | medicvista_retailer | Retailer-specific |
| **Retailer Requests** | **pharma_db / medicvistapharma_db** | **Sync with Django ERP** |

---

## ✅ Benefits

1. **Flexible Switching**: Easily switch Django ERP database
2. **Data Isolation**: Retailer data remains separate
3. **Sync Independence**: Retailer requests connect to ERP database
4. **Testing**: Test with pharma_db locally, deploy with medicvistapharma_db

---

## 🚀 Quick Start

```bash
# 1. Verify current config
.\verify_config.bat

# 2. Switch to desired mode
.\switch_config.bat

# 3. Start application
python main.py
```

---

## 📝 Summary

**2 Databases, 1 Application:**
- `medicvista_retailer` → Retailer's own data
- `pharma_db` / `medicvistapharma_db` → Django ERP sync

**Easy Switching:**
- `.\switch_config.bat` → Select mode
- Config automatically adjusts both databases
