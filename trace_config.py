"""
Runtime Config Tracer
---------------------
Run this to see exactly which config is loaded at runtime.
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'retailer_sync'))

print("=" * 70)
print("RUNTIME CONFIG TRACE")
print("=" * 70)
print()

# Step 1: Check environment
print("Step 1: Environment Detection")
print("-" * 70)
from pathlib import Path
import configparser

config_path = Path('config.ini')
if config_path.exists():
    parser = configparser.ConfigParser()
    parser.read(config_path)
    env = parser.get('mode', 'environment', fallback='UNKNOWN')
    print(f"✓ config.ini exists")
    print(f"✓ Environment mode: {env}")
    print()
else:
    print("✗ config.ini NOT FOUND!")
    sys.exit(1)

# Step 2: Load sync config
print("Step 2: Sync Config Loading")
print("-" * 70)
try:
    from retailer_sync_runner import _load_config
    
    # Trace the loading
    base_config = _load_config()
    
    print(f"✓ Config loaded successfully")
    print(f"✓ Server URL: {base_config.get('server_url')}")
    print(f"✓ Server Mode: {base_config.get('server_mode')}")
    print(f"✓ Sync Interval: {base_config.get('sync_interval_seconds')}s")
    print()
    
except Exception as e:
    print(f"✗ Error loading config: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Check which JSON was loaded
print("Step 3: Config File Path Detection")
print("-" * 70)

sync_dir = Path('retailer_sync')
local_config = sync_dir / 'retailer_sync_config_local.json'
cloud_config = sync_dir / 'retailer_sync_config_cloud.json'

print(f"LOCAL config exists: {local_config.exists()}")
print(f"CLOUD config exists: {cloud_config.exists()}")
print()

if env == 'LOCAL' and base_config.get('server_url') != 'http://127.0.0.1:8000':
    print("=" * 70)
    print("⚠️  WARNING: MISMATCH DETECTED!")
    print("=" * 70)
    print(f"Config says: {env}")
    print(f"But loaded: {base_config.get('server_url')}")
    print()
    print("This means the code is not reading config.ini correctly!")
    print("=" * 70)
else:
    print("=" * 70)
    print("✅ CONFIGURATION IS CORRECT")
    print("=" * 70)
    print(f"Mode: {env}")
    print(f"Server: {base_config.get('server_url')}")
    print()

# Step 4: Test actual runner
print("Step 4: Testing Actual Runner Initialization")
print("-" * 70)
try:
    from retailer_sync_runner import RetailerSyncRunner, get_retailer_config
    
    # Get retailer 1 config
    retailer_config = get_retailer_config(base_config, 1)
    
    print(f"✓ Retailer config extracted")
    print(f"✓ Retailer ID: {retailer_config.get('retailer_id')}")
    print(f"✓ Server URL: {retailer_config.get('server_url')}")
    print(f"✓ API Key: {retailer_config.get('api_key')[:10]}...")
    print()
    
    if retailer_config.get('server_url') == 'http://127.0.0.1:8000':
        print("✅ PERFECT! Runner will use LOCAL server")
    else:
        print(f"⚠️  WARNING! Runner will use: {retailer_config.get('server_url')}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
