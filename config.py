"""
Configuration Management Module
Centralized configuration with environment variable validation
"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass


class Config:
    """Centralized configuration management with validation"""
    
    # ==========================================
    # KAFKA CONFIGURATION
    # ==========================================
    KAFKA_BROKER: str = os.getenv('KAFKA_BROKER', 'localhost:9092')
    KAFKA_TOPIC: str = os.getenv('KAFKA_TOPIC', 'weather-data')
    
    # ==========================================
    # MONGODB CONFIGURATION
    # ==========================================
    MONGO_URI: Optional[str] = os.getenv('MONGO_URI')
    MONGO_DB_NAME: str = os.getenv('MONGO_DB_NAME', 'weather_db')
    MONGO_COLLECTION_NAME: str = os.getenv('MONGO_COLLECTION_NAME', 'weather_data')
    
    # ==========================================
    # OPENWEATHERMAP API CONFIGURATION
    # ==========================================
    OPENWEATHERMAP_API_KEY: Optional[str] = os.getenv('OPENWEATHERMAP_API_KEY')
    OPENWEATHERMAP_API_URL: str = "http://api.openweathermap.org/data/2.5/weather"
    
    # ==========================================
    # PRODUCER CONFIGURATION
    # ==========================================
    DEFAULT_CITY: str = os.getenv('DEFAULT_CITY', 'Quezon City')
    FETCH_INTERVAL: int = int(os.getenv('FETCH_INTERVAL', '15'))
    
    # Supported cities for multi-city support
    SUPPORTED_CITIES: list = [
    "Quezon City,PH",
    "Manila,PH",
    "Cebu City,PH",
    "Davao City,PH",
    "Makati,PH",
    "Tokyo,JP",
    "Singapore,SG",
    "Bangkok,TH",
    "Seoul,KR",
    "Los Angeles,US"
]
    
    # ==========================================
    # DASHBOARD CONFIGURATION
    # ==========================================
    DASHBOARD_TITLE: str = os.getenv('DASHBOARD_TITLE', 'Weather Monitoring System')
    DASHBOARD_ICON: str = os.getenv('DASHBOARD_ICON', '🌤️')
    AUTO_REFRESH_INTERVAL: int = int(os.getenv('AUTO_REFRESH_INTERVAL', '15000'))
    
    # ==========================================
    # LOGGING CONFIGURATION
    # ==========================================
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = os.getenv(
        'LOG_FORMAT',
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # ==========================================
    # PERFORMANCE SETTINGS
    # ==========================================
    CACHE_TTL: int = int(os.getenv('CACHE_TTL', '300'))
    MAX_RECENT_RECORDS: int = int(os.getenv('MAX_RECENT_RECORDS', '100'))
    BATCH_SIZE: int = int(os.getenv('BATCH_SIZE', '10'))
    
    # ==========================================
    # KAFKA PRODUCER SETTINGS
    # ==========================================
    KAFKA_ACKS: str = 'all'
    KAFKA_RETRIES: int = 3
    KAFKA_MAX_IN_FLIGHT: int = 1
    KAFKA_REQUEST_TIMEOUT: int = 30000
    KAFKA_RETRY_BACKOFF: int = 1000
    
    # ==========================================
    # KAFKA CONSUMER SETTINGS
    # ==========================================
    KAFKA_AUTO_OFFSET_RESET: str = 'latest'
    KAFKA_ENABLE_AUTO_COMMIT: bool = True
    KAFKA_GROUP_ID: str = 'weather-consumer-group'
    
    # ==========================================
    # API REQUEST SETTINGS
    # ==========================================
    API_TIMEOUT: int = 10
    API_MAX_RETRIES: int = 3
    API_RETRY_DELAY: int = 5
    
    # ==========================================
    # MONGODB SETTINGS
    # ==========================================
    MONGO_MAX_POOL_SIZE: int = 50
    MONGO_MIN_POOL_SIZE: int = 10
    MONGO_SERVER_SELECTION_TIMEOUT: int = 5000
    MONGO_CONNECT_TIMEOUT: int = 10000
    MONGO_SOCKET_TIMEOUT: int = 10000
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate required configuration variables
        Raises ConfigurationError if any required variable is missing
        """
        errors = []
        
        # Check required variables
        if not cls.MONGO_URI:
            errors.append("MONGO_URI is required. Please set it in .env file.")
        
        if not cls.OPENWEATHERMAP_API_KEY:
            errors.append("OPENWEATHERMAP_API_KEY is required. Please set it in .env file.")
        
        # Validate numeric values
        if cls.FETCH_INTERVAL < 1:
            errors.append("FETCH_INTERVAL must be at least 1 second.")
        
        if cls.AUTO_REFRESH_INTERVAL < 1000:
            errors.append("AUTO_REFRESH_INTERVAL must be at least 1000 milliseconds.")
        
        if cls.MAX_RECENT_RECORDS < 1:
            errors.append("MAX_RECENT_RECORDS must be at least 1.")
        
        if cls.BATCH_SIZE < 1:
            errors.append("BATCH_SIZE must be at least 1.")
        
        # If there are errors, raise exception
        if errors:
            error_message = "\n".join([f"  - {error}" for error in errors])
            raise ConfigurationError(
                f"\n\nConfiguration Errors Found:\n{error_message}\n\n"
                f"Please check your .env file or environment variables.\n"
                f"See .env.example for reference.\n"
            )
    
    @classmethod
    def get_api_url(cls, city: str) -> str:
        """
        Get the complete API URL for a given city
        
        Args:
            city: City name to fetch weather data for
            
        Returns:
            Complete API URL with parameters
        """
        return (
            f"{cls.OPENWEATHERMAP_API_URL}"
            f"?q={city}"
            f"&appid={cls.OPENWEATHERMAP_API_KEY}"
            f"&units=metric"
        )
    
    @classmethod
    def display_config(cls) -> None:
        """Display current configuration (without sensitive data)"""
        print("\n" + "="*60)
        print("WEATHER REPORTING SYSTEM - CONFIGURATION")
        print("="*60)
        print(f"Kafka Broker: {cls.KAFKA_BROKER}")
        print(f"Kafka Topic: {cls.KAFKA_TOPIC}")
        print(f"MongoDB Database: {cls.MONGO_DB_NAME}")
        print(f"MongoDB Collection: {cls.MONGO_COLLECTION_NAME}")
        print(f"Default City: {cls.DEFAULT_CITY}")
        print(f"Fetch Interval: {cls.FETCH_INTERVAL}s")
        print(f"Auto Refresh: {cls.AUTO_REFRESH_INTERVAL}ms")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print(f"API Key: {'*' * 20} (hidden)")
        print(f"MongoDB URI: {'*' * 20} (hidden)")
        print("="*60 + "\n")


# Validate configuration on import
try:
    Config.validate()
except ConfigurationError as e:
    print(f"\n❌ Configuration Error:\n{e}")
    sys.exit(1)


# Export for easy importing
__all__ = ['Config', 'ConfigurationError']

    # Logging configuration – this is what the original logger needs
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")          # Can be DEBUG, INFO, WARNING, etc.
    LOG_FORMAT = "[%(asctime)s] %(levelname)s %(name)s] %(message)s"
