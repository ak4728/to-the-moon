<p align="center">
  <img alt="to-the-moon.py" src="https://dl3.pushbulletusercontent.com/25CJDZ1FmLHTYh6e1AHLtaCLLzzWO70S/Untitled-1.png" width="750px">
</p>

Stock market watch bot for discord. Written in Python.

## Requirements
- Python 3.6 and up - https://www.python.org/downloads/
- git - https://git-scm.com/download/

## Command List
![image](https://user-images.githubusercontent.com/5445968/128292062-26fcce26-ca2a-46fd-ac01-e55774921472.png)

## How to setup

### Quick Setup (Recommended)
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd to-the-moon
   ```

2. **Run the setup script**
   ```bash
   python setup.py
   ```
   This will:
   - Create `config.json` from the sample template
   - Prompt you for your Discord bot token and other settings
   - Set up the watchlist file
   - Guide you through the configuration process

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   (If that doesn't work, try `python -m pip install -r requirements.txt`)

4. **Start the bot**
   ```bash
   python main.py
   ```

### Manual Setup
1. **Create a Discord bot** at [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to "Bot" section and create a bot
   - Copy the token (keep it secret!)

2. **Configure the bot**
   - Copy `sample-config.json` to `config.json`
   - Edit `config.json` and fill in at minimum:
     - `discord_token`: Your bot token from step 1
     - `webhook_url`: Discord webhook URL for trading signals (optional)

3. **Install and run** (same as steps 3-4 above)

### Configuration Options

| Field | Required | Description |
|-------|----------|-------------|
| `discord_token` | ✅ Yes | Bot token from Discord Developer Portal |
| `webhook_url` | ❌ No | Discord webhook for trading signals |
| `client_id` | ❌ No | Reddit app client ID (for Reddit features) |
| `client_secret` | ❌ No | Reddit app client secret (for Reddit features) |
| `default_int` | ✅ Yes | Default trading interval (pre-configured) |

### Security Notes ⚠️
- **Never commit `config.json` to git** - it contains sensitive tokens
- The `.gitignore` file excludes `config.json` automatically
- Keep your Discord token and API keys secret




## Contributors

<a href = "https://github.com/Tanu-N-Prabhu/Python/graphs/contributors">
  <img src = "https://contrib.rocks/image?repo=ak4728/to-the-moon"/>
</a>


