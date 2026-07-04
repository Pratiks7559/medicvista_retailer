import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'retailer_sync'))

print("=" * 60)
print("Configuration Debug Report")
print("=" * 60)
print()

# Check main config
print("1. Main Config (config.ini):")
print("-" * 40)
try:
    with open('config.ini', 'r') as f:
        for line in f:
            if 'name =' in line and '#' not in line:
                print(f"   {line.strip()}")
            if 'environment =' in line:
                print(f"   {line.strip()}")
except Exception as e:
    print(f"   Error: {e}")
print()

# Check sync config detection
print("2. Sync Config Detection:")
print("-" * 40)
try:
    from retailer_sync_runner import _load_config
    config = _load_config()
    print(f"   Server URL: {config.get('server_url')}")
    print(f"   Server Mode: {config.get('server_mode')}")
    print(f"   Config has {len(config.get('retailers', {}))} retailers")
except Exception as e:
    print(f"   Error: {e}")
print()

# Check which JSON file exists
print("3. Available Sync Config Files:")
print("-" * 40)
import json
from pathlib import Path

sync_dir = Path('retailer_sync')
for json_file in ['retailer_sync_config_local.json', 'retailer_sync_config_cloud.json']:
    full_path = sync_dir / json_file
    if full_path.exists():
        try:
            with open(full_path, 'r') as f:
                data = json.load(f)
                print(f"   {json_file}:")
                print(f"      Server: {data.get('server_url')}")
        except Exception as e:
            print(f"   {json_file}: Error - {e}")
print()

print("=" * 60)
print("Recommendation:")
print("=" * 60)
print("1. Close the application completely")
print("2. Run: python main.py")
print("3. Check Retailer Requests screen")
print()
