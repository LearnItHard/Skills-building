"""
MinerU Converter Configuration Module

Handles API token, URLs, and conversion parameters.
Supports environment variables, .env files, and config.json.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

# Optional .env file support
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


def find_config_file() -> Optional[str]:
    """
    Find config file in standard locations.
    Searches in order:
    1. .env (current directory)
    2. config.json (current directory)
    3. mineru-config.json (current directory)
    4. config.json (user's home directory)
    5. .mineru/config.json (user's home directory)
    """
    home = str(Path.home())
    
    search_paths = [
        ".env",
        "config.json",
        "./mineru-config.json",
        os.path.join(home, "config.json"),
        os.path.join(home, ".mineru", "config.json"),
    ]
    
    for path in search_paths:
        if Path(path).exists():
            return path
    return None


def load_config_json(path: str) -> Dict[str, Any]:
    """Load config from JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


@dataclass
class MinerUConfig:
    """MinerU API configuration."""
    
    # API settings (v4 async API)
    api_token: str
    api_url: str = "https://mineru.net/api/v4"
    
    # Conversion options
    enable_formula: bool = True
    enable_table: bool = True
    language: str = "ch"  # ch, en, or ch,en
    is_ocr: bool = False  # Force OCR mode
    model_version: str = "vlm"  # vlm, MinerU-HTML
    
    # File handling
    output_dir: str = "./output"
    keep_temp_files: bool = False
    
    # Retry and polling settings
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    timeout: int = 300  # 5 minutes for large files
    poll_interval: int = 3  # seconds between status checks
    max_poll_attempts: int = 100  # maximum status checks
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "MinerUConfig":
        """
        Create config from environment variables.
        
        Searches for config in multiple locations:
        1. Environment variables (highest priority)
        2. .env file in current directory
        3. config.json in current directory
        4. config.json in user's home directory
        5. .mineru/config.json in user's home directory
        
        Config file format (JSON):
        {
            "api_token": "your_token_here",
            "api_url": "https://mineru.net/api/v4",
            "language": "ch",
            ...
        }
        """
        # Try to find and load config file
        config_file = env_file or find_config_file()
        
        if config_file and Path(config_file).exists():
            if config_file.endswith('.json'):
                # Load from JSON config
                config_dict = load_config_json(config_file)
                return cls.from_dict(config_dict)
            elif DOTENV_AVAILABLE:
                # Load .env file
                load_dotenv(config_file)
        
        # Fall back to environment variables
        api_token = os.getenv("MINERU_API_TOKEN")
        if not api_token:
            raise ValueError(
                "MINERU_API_TOKEN not found. Please set it via:\n"
                "1) Environment variable: export MINERU_API_TOKEN='your_token'\n"
                "2) .env file in project root\n"
                "3) config.json in current/home directory\n"
                "4) Pass directly: MinerUConfig(api_token='your_token')\n"
                "Get token from: https://mineru.net/apiManage"
            )
        
        return cls(
            api_token=api_token,
            api_url=os.getenv("MINERU_API_URL", "https://mineru.net/api/v4"),
            enable_formula=os.getenv("MINERU_ENABLE_FORMULA", "true").lower() == "true",
            enable_table=os.getenv("MINERU_ENABLE_TABLE", "true").lower() == "true",
            language=os.getenv("MINERU_LANGUAGE", "ch"),
            is_ocr=os.getenv("MINERU_IS_OCR", "false").lower() == "true",
            model_version=os.getenv("MINERU_MODEL_VERSION", "vlm"),
            output_dir=os.getenv("MINERU_OUTPUT_DIR", "./output"),
            keep_temp_files=os.getenv("MINERU_KEEP_TEMP", "false").lower() == "true",
            max_retries=int(os.getenv("MINERU_MAX_RETRIES", "3")),
            retry_delay=int(os.getenv("MINERU_RETRY_DELAY", "5")),
            timeout=int(os.getenv("MINERU_TIMEOUT", "300")),
            poll_interval=int(os.getenv("MINERU_POLL_INTERVAL", "3")),
            max_poll_attempts=int(os.getenv("MINERU_MAX_POLL_ATTEMPTS", "100")),
        )
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "MinerUConfig":
        """Create config from dictionary."""
        # Map JSON keys to class fields
        key_mapping = {
            "apiToken": "api_token",
            "apiUrl": "api_url",
            "enableFormula": "enable_formula",
            "enableTable": "enable_table",
            "isOcr": "is_ocr",
            "modelVersion": "model_version",
            "outputDir": "output_dir",
            "keepTempFiles": "keep_temp_files",
            "maxRetries": "max_retries",
            "retryDelay": "retry_delay",
            "pollInterval": "poll_interval",
            "maxPollAttempts": "max_poll_attempts",
        }
        
        # Convert keys
        converted = {}
        for key, value in config_dict.items():
            mapped_key = key_mapping.get(key, key.lower())
            if mapped_key == "api_token" or not hasattr(cls, mapped_key):
                converted[mapped_key] = value
        
        # Set defaults for missing fields
        defaults = {
            "api_url": "https://mineru.net/api/v4",
            "enable_formula": True,
            "enable_table": True,
            "language": "ch",
            "is_ocr": False,
            "model_version": "vlm",
            "output_dir": "./output",
            "keep_temp_files": False,
            "max_retries": 3,
            "retry_delay": 5,
            "timeout": 300,
            "poll_interval": 3,
            "max_poll_attempts": 100,
        }
        
        for key, value in defaults.items():
            if key not in converted:
                converted[key] = value
        
        return cls(**converted)
    
    def get_headers(self) -> Dict[str, str]:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }


# Supported file formats
SUPPORTED_INPUT_FORMATS = {
    '.pdf': 'pdf',
    '.doc': 'doc',
    '.docx': 'docx',
    '.ppt': 'ppt',
    '.pptx': 'pptx',
    '.png': 'image',
    '.jpg': 'image',
    '.jpeg': 'image',
}

# DOCX to PDF conversion timeout (seconds)
DOCX_CONVERT_TIMEOUT = 60
