#!/usr/bin/env python3
"""
Health check script for to-the-moon Discord bot.
Validates configuration and dependencies.
"""

import sys
import json
from pathlib import Path
import importlib


def check_python_version():
    """Check Python version."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected")
        print("⚠️  Recommended: Python 3.8+")
        return False
    else:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Good!")
        return True


def check_dependencies():
    """Check if required packages are installed."""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'discord',
        'dhooks', 
        'aiohttp',
        'aiofiles',
        'pandas',
        'tradingview_ta',
        'vadersentiment',
        'asyncpraw',
        'snscrape'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    
    return True


def check_config():
    """Check configuration file."""
    print("\n⚙️  Checking configuration...")
    
    config_path = Path("config.json")
    sample_path = Path("sample-config.json")
    
    # Check if sample exists
    if not sample_path.exists():
        print("❌ sample-config.json not found")
        return False
    else:
        print("✅ sample-config.json found")
    
    # Check if config exists
    if not config_path.exists():
        print("❌ config.json not found")
        print("💡 Run: python setup.py")
        return False
    
    # Validate config
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        required_fields = ['discord_token', 'webhook_url', 'api_url', 'symbol_url']
        missing_fields = []
        empty_required = []
        
        for field in required_fields:
            if field not in config:
                missing_fields.append(field)
            elif not config[field] and field == 'discord_token':
                empty_required.append(field)
        
        if missing_fields:
            print(f"❌ Missing fields: {', '.join(missing_fields)}")
            return False
        
        if empty_required:
            print(f"❌ Required fields are empty: {', '.join(empty_required)}")
            print("💡 Add your Discord bot token to config.json")
            return False
        
        print("✅ config.json is valid")
        
        # Check token format (basic validation)
        token = config.get('discord_token', '')
        if token and (len(token) < 50 or not any(c.isdigit() for c in token)):
            print("⚠️  Discord token format looks suspicious")
            print("💡 Make sure you copied the full token from Discord Developer Portal")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False


def check_files():
    """Check required files."""
    print("\n📁 Checking required files...")
    
    required_files = [
        'main.py',
        'utils.py',
        'config_manager.py',
        'http_client.py',
        'file_manager.py',
        'cache.py',
        'requirements.txt',
        'cogs/market.py',
        'cogs/social_media.py',
        'cogs/config.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            missing_files.append(file_path)
    
    return len(missing_files) == 0


def main():
    """Run all health checks."""
    print("🏥 to-the-moon Bot Health Check")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Configuration", check_config),
        ("Required Files", check_files)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Health Check Summary")
    print("=" * 40)
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All checks passed! Your bot should be ready to run.")
        print("🚀 Start with: python main.py")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above before running the bot.")
        print("📚 See README.md for setup instructions.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)