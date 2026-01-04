"""
Configuration management for the competitive intelligence scraper.
"""
import os
import yaml
from pathlib import Path


class Config:
    """Configuration loader and manager."""

    def __init__(self, config_path=None):
        """
        Initialize configuration from YAML file.

        Args:
            config_path: Path to config.yaml file. If None, uses default location.
        """
        if config_path is None:
            # Default to config.yaml in project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config.yaml"

        self.config_path = Path(config_path)
        self._load_config()

    def _load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)

    @property
    def our_location(self):
        """Get our property location details."""
        return self._config['our_location']

    @property
    def search_params(self):
        """Get search parameters."""
        return self._config['search']

    @property
    def dates(self):
        """Get date ranges for searches."""
        return self._config['dates']

    @property
    def filters(self):
        """Get filter criteria."""
        return self._config['filters']

    @property
    def rate_limit(self):
        """Get rate limiting settings."""
        return self._config['rate_limit']

    @property
    def output_settings(self):
        """Get output settings."""
        return self._config['output']

    def get(self, key, default=None):
        """Get configuration value by key."""
        return self._config.get(key, default)

    @property
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent

    @property
    def data_dir(self):
        """Get data directory path."""
        return self.project_root / "data"

    @property
    def output_dir(self):
        """Get output directory path."""
        return self.project_root / "output"

    def ensure_directories(self):
        """Ensure all required directories exist."""
        dirs = [
            self.data_dir / "raw",
            self.data_dir / "processed",
            self.data_dir / "archive",
            self.output_dir
        ]
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
