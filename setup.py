#!/usr/bin/env python3
"""
Setup script for to-the-moon Discord bot.
This script helps users configure their bot by copying the sample config
and prompting for required values.
"""

import json
import shutil
from pathlib import Path


def setup_config():
    """Set up the configuration file."""
    config_path = Path("config.json")
    sample_config_path = Path("sample-config.json")
    
    # Check if config already exists
    if config_path.exists():
        response = input("config.json already exists. Overwrite? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Setup cancelled.")
            return False
    
    # Check if sample config exists
    if not sample_config_path.exists():
        print("❌ Error: sample-config.json not found!")
        print("Make sure you're running this from the project root directory.")
        return False
    
    # Copy sample config
    shutil.copy(sample_config_path, config_path)
    print("✅ Created config.json from sample-config.json")
    
    # Load the config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print("\n🔧 Let's configure your bot!")
    print("=" * 50)
    
    # Required fields
    required_fields = {
        'discord_token': {
            'prompt': "Discord Bot Token (from https://discord.com/developers/applications)",
            'description': "This is required to connect your bot to Discord"
        },
        'webhook_url': {
            'prompt': "Discord Webhook URL (optional, for trading signals)",
            'description': "Used to send trading signals to a Discord channel"
        }
    }
    
    # Optional Reddit fields
    reddit_fields = {
        'client_id': {
            'prompt': "Reddit Client ID (optional, for Reddit sentiment)",
            'description': "From https://www.reddit.com/prefs/apps"
        },
        'client_secret': {
            'prompt': "Reddit Client Secret (optional, for Reddit sentiment)",
            'description': "From https://www.reddit.com/prefs/apps"
        }
    }
    
    # Configure required fields
    for field, info in required_fields.items():
        print(f"\n📝 {info['description']}")
        current_value = config.get(field, '')
        if current_value:
            print(f"Current value: {current_value[:20]}..." if len(current_value) > 20 else f"Current value: {current_value}")
        
        new_value = input(f"{info['prompt']}: ").strip()
        if new_value:
            config[field] = new_value
            print("✅ Updated!")
        elif not current_value and field == 'discord_token':
            print("❌ Discord token is required! Bot will not work without it.")
    
    # Configure Reddit fields
    print(f"\n🤔 Do you want to configure Reddit integration? (y/N): ", end="")
    setup_reddit = input().strip().lower() in ['y', 'yes']
    
    if setup_reddit:
        for field, info in reddit_fields.items():
            print(f"\n📝 {info['description']}")
            current_value = config.get(field, '')
            if current_value:
                print(f"Current value: {current_value}")
            
            new_value = input(f"{info['prompt']}: ").strip()
            if new_value:
                config[field] = new_value
                print("✅ Updated!")
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n✅ Configuration saved!")
    print(f"📁 Config file location: {config_path.absolute()}")
    print("\n⚠️  IMPORTANT SECURITY NOTES:")
    print("   • Never commit config.json to version control")
    print("   • Keep your Discord token secret")
    print("   • The .gitignore file will exclude config.json from git")
    
    return True


def setup_watchlist():
    """Set up an empty watchlist file."""
    watchlist_path = Path("watchlist.txt")
    
    if not watchlist_path.exists():
        with open(watchlist_path, 'w') as f:
            json.dump({}, f, indent=2)
        print(f"✅ Created empty watchlist: {watchlist_path}")
    else:
        print(f"📁 Watchlist already exists: {watchlist_path}")


def main():
    """Main setup function."""
    print("🚀 to-the-moon Discord Bot Setup")
    print("=" * 40)
    
    try:
        # Setup configuration
        if setup_config():
            # Setup watchlist
            setup_watchlist()
            
            print("\n🎉 Setup complete!")
            print("\n📋 Next steps:")
            print("1. Install dependencies: pip install -r requirements.txt")
            print("2. Run the bot: python main.py")
            print("3. Invite your bot to Discord servers")
            print("\n📚 Check README.md for more detailed instructions.")
        
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("Please check the error and try again.")


if __name__ == "__main__":
    main()