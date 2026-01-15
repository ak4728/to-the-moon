"""Configuration management for the bot."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from tradingview_ta import Interval


@dataclass
class Config:
    """Configuration data class with type hints."""
    discord_token: str
    webhook_url: str
    user_agent: str
    api_url: str
    symbol_url: str
    ark_url: str
    client_id: str
    client_secret: str
    default_int: str
    buy_color: int
    sell_color: int
    ticker_color: int
    watchlist_color: int
    image: str
    interval_image: str
    channel_lock: bool


class ConfigManager:
    """Singleton configuration manager."""
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[Config] = None
    
    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_path: str = 'config.json') -> None:
        """Load configuration from JSON file."""
        config_file = Path(config_path)
        
        if not config_file.exists():
            error_msg = f"""
❌ Configuration file '{config_path}' not found!

🔧 To set up your bot:

1. Run the setup script:
   python setup.py

2. Or manually copy the sample config:
   cp sample-config.json config.json

3. Then edit config.json with your Discord bot token and other settings.

📚 See README.md for detailed setup instructions.
            """.strip()
            
            raise FileNotFoundError(error_msg)
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Validate required fields
            required_fields = ['discord_token']
            missing_fields = [field for field in required_fields if not config_data.get(field)]
            
            if missing_fields:
                error_msg = f"""
❌ Required configuration fields missing: {', '.join(missing_fields)}

🔧 Please update your config.json file with the missing values.
   You can run 'python setup.py' to reconfigure your bot.
                """.strip()
                raise ValueError(error_msg)
            
            self._config = Config(**config_data)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except TypeError as e:
            raise ValueError(f"Missing or invalid configuration keys: {e}")
    
    @property
    def config(self) -> Config:
        """Get the configuration object."""
        if self._config is None:
            self.load_config()
        return self._config
    
    @property
    def intervals(self) -> Dict[str, Interval]:
        """Get trading intervals mapping."""
        return {
            "1-minute": Interval.INTERVAL_1_MINUTE,
            "5-minutes": Interval.INTERVAL_5_MINUTES,
            "15-minutes": Interval.INTERVAL_15_MINUTES,
            "1-hour": Interval.INTERVAL_1_HOUR,
            "4-hours": Interval.INTERVAL_4_HOURS,
            "1-day": Interval.INTERVAL_1_DAY,
            "1-week": Interval.INTERVAL_1_WEEK,
            "1-month": Interval.INTERVAL_1_MONTH,
        }
    
    def get_selected_interval(self) -> Interval:
        """Get the selected trading interval."""
        return self.intervals[self.config.default_int]


# Global config manager instance
config_manager = ConfigManager()