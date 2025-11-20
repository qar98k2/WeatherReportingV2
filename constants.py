"""
Constants Module
Centralized constants for the Weather Reporting System
"""

# ==========================================
# WEATHER CONDITION MAPPINGS
# ==========================================
WEATHER_ICONS = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "🌧️",
    "Drizzle": "🌦️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Fog": "🌫️",
    "Haze": "🌫️",
    "Smoke": "💨",
    "Dust": "💨",
    "Sand": "💨",
    "Ash": "🌋",
    "Squall": "💨",
    "Tornado": "🌪️"
}

WEATHER_DESCRIPTIONS = {
    "Clear": "Clear Sky",
    "Clouds": "Cloudy",
    "Rain": "Rainy",
    "Drizzle": "Drizzle",
    "Thunderstorm": "Thunderstorm",
    "Snow": "Snowy",
    "Mist": "Misty",
    "Fog": "Foggy",
    "Haze": "Hazy",
    "Smoke": "Smoky",
    "Dust": "Dusty",
    "Sand": "Sandy",
    "Ash": "Volcanic Ash",
    "Squall": "Squall",
    "Tornado": "Tornado"
}

# ==========================================
# TEMPERATURE THRESHOLDS (Celsius)
# ==========================================
TEMP_FREEZING = 0
TEMP_COLD = 15
TEMP_COMFORTABLE_MIN = 20
TEMP_COMFORTABLE_MAX = 28
TEMP_HOT = 32
TEMP_VERY_HOT = 35
TEMP_DANGEROUS = 40

# ==========================================
# HUMIDITY THRESHOLDS (%)
# ==========================================
HUMIDITY_LOW = 30
HUMIDITY_COMFORTABLE_MIN = 40
HUMIDITY_COMFORTABLE_MAX = 60
HUMIDITY_HIGH = 70
HUMIDITY_VERY_HIGH = 80

# ==========================================
# WIND SPEED THRESHOLDS (km/h)
# ==========================================
WIND_CALM = 5
WIND_LIGHT = 20
WIND_MODERATE = 40
WIND_STRONG = 60
WIND_VERY_STRONG = 80
WIND_STORM = 100

# ==========================================
# PRESSURE THRESHOLDS (hPa)
# ==========================================
PRESSURE_LOW = 1000
PRESSURE_NORMAL_MIN = 1013
PRESSURE_NORMAL_MAX = 1020
PRESSURE_HIGH = 1030

# ==========================================
# VISIBILITY THRESHOLDS (km)
# ==========================================
VISIBILITY_POOR = 1
VISIBILITY_MODERATE = 5
VISIBILITY_GOOD = 10

# ==========================================
# ALERT MESSAGES
# ==========================================
ALERTS = {
    "extreme_heat": "⚠️ EXTREME HEAT WARNING! Temperature above 40°C. Stay indoors and stay hydrated!",
    "dangerous_heat": "🔥 DANGEROUS HEAT! Temperature above 35°C. Avoid outdoor activities!",
    "very_hot": "☀️ VERY HOT! Temperature above 32°C. Stay hydrated and seek shade!",
    "hot": "🌡️ Hot weather. Stay hydrated!",
    "freezing": "❄️ FREEZING ALERT! Temperature below 0°C. Protect yourself from cold!",
    "cold": "🧊 COLD ALERT! Temperature below 15°C. Dress warmly!",
    "high_humidity": "💧 High humidity levels. May feel uncomfortable.",
    "low_humidity": "🏜️ Low humidity. Stay hydrated.",
    "strong_wind": "💨 Strong winds detected. Be cautious outdoors!",
    "storm_wind": "🌪️ STORM WARNING! Very strong winds. Stay indoors!",
    "poor_visibility": "🌫️ Poor visibility. Drive carefully!",
    "low_pressure": "📉 Low pressure system. Weather changes expected.",
    "high_pressure": "📈 High pressure system. Stable weather expected."
}

# ==========================================
# DATA FIELD NAMES
# ==========================================
FIELD_TIMESTAMP = "timestamp"
FIELD_TEMPERATURE = "temperature"
FIELD_FEELS_LIKE = "feels_like"
FIELD_HUMIDITY = "humidity"
FIELD_PRESSURE = "pressure"
FIELD_WIND_SPEED = "wind_speed"
FIELD_WIND_DIRECTION = "wind_direction"
FIELD_VISIBILITY = "visibility"
FIELD_CONDITION = "condition"
FIELD_DESCRIPTION = "description"
FIELD_LOCATION = "location"
FIELD_COUNTRY = "country"
FIELD_SUNRISE = "sunrise"
FIELD_SUNSET = "sunset"
FIELD_CLOUDINESS = "cloudiness"

# ==========================================
# AGGREGATION PERIODS
# ==========================================
AGG_HOURLY = "H"
AGG_DAILY = "D"
AGG_WEEKLY = "W"
AGG_MONTHLY = "M"

# ==========================================
# CHART COLORS
# ==========================================
COLOR_TEMPERATURE = "#ff6a00"
COLOR_HUMIDITY = "#00b4d8"
COLOR_PRESSURE = "#9d4edd"
COLOR_WIND = "#06ffa5"
COLOR_VISIBILITY = "#ffd60a"

COLOR_GRADIENT_START = "rgba(255,106,0,0.1)"
COLOR_GRADIENT_END = "rgba(255,106,0,0.3)"

# ==========================================
# UI THEME COLORS
# ==========================================
THEME_DARK_BG = "#0f111a"
THEME_DARK_TEXT = "#ffffff"
THEME_DARK_ACCENT = "#00ffc6"
THEME_DARK_CARD_BG = "rgba(255,255,255,0.05)"
THEME_DARK_BORDER = "rgba(255,255,255,0.2)"

THEME_LIGHT_BG = "#f8f9fa"
THEME_LIGHT_TEXT = "#212529"
THEME_LIGHT_ACCENT = "#0d6efd"
THEME_LIGHT_CARD_BG = "rgba(0,0,0,0.07)"
THEME_LIGHT_BORDER = "rgba(0,0,0,0.2)"

# ==========================================
# EXPORT FORMATS
# ==========================================
EXPORT_CSV = "csv"
EXPORT_EXCEL = "xlsx"
EXPORT_PDF = "pdf"
EXPORT_JSON = "json"

# ==========================================
# TIME FORMATS
# ==========================================
TIME_FORMAT_ISO = "%Y-%m-%dT%H:%M:%S%z"
TIME_FORMAT_DISPLAY = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT_SHORT = "%H:%M:%S"
TIME_FORMAT_DATE = "%Y-%m-%d"

# ==========================================
# ERROR MESSAGES
# ==========================================
ERROR_NO_DATA = "No data available"
ERROR_CONNECTION_FAILED = "Connection failed"
ERROR_API_ERROR = "API request failed"
ERROR_INVALID_DATA = "Invalid data format"
ERROR_DATABASE_ERROR = "Database operation failed"
ERROR_KAFKA_ERROR = "Kafka operation failed"

# ==========================================
# SUCCESS MESSAGES
# ==========================================
SUCCESS_DATA_SAVED = "Data saved successfully"
SUCCESS_CONNECTION = "Connection established"
SUCCESS_EXPORT = "Data exported successfully"

# ==========================================
# MONGODB INDEXES
# ==========================================
INDEX_TIMESTAMP = "timestamp"
INDEX_LOCATION = "location"
INDEX_TIMESTAMP_LOCATION = "timestamp_location"

# ==========================================
# CACHE KEYS
# ==========================================
CACHE_LATEST_DATA = "latest_data"
CACHE_RECENT_DATA = "recent_data"
CACHE_HISTORICAL_DATA = "historical_data"
CACHE_AGGREGATED_DATA = "aggregated_data"

# ==========================================
# VALIDATION LIMITS
# ==========================================
TEMP_MIN = -50  # Minimum valid temperature (°C)
TEMP_MAX = 60   # Maximum valid temperature (°C)
HUMIDITY_MIN = 0
HUMIDITY_MAX = 100
PRESSURE_MIN = 800
PRESSURE_MAX = 1100
WIND_SPEED_MIN = 0
WIND_SPEED_MAX = 200
VISIBILITY_MIN = 0
VISIBILITY_MAX = 50

# ==========================================
# PAGINATION
# ==========================================
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000

# ==========================================
# RETRY SETTINGS
# ==========================================
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
RETRY_BACKOFF_FACTOR = 2

# ==========================================
# FORECAST SETTINGS
# ==========================================
FORECAST_HOURS = 3
FORECAST_INTERVAL = 60  # minutes

# ==========================================
# DASHBOARD SETTINGS
# ==========================================
DASHBOARD_REFRESH_INTERVAL = 15  # seconds
CHART_HEIGHT = 400
CHART_WIDTH = 800
MAX_CHART_POINTS = 100

# ==========================================
# LOGGING
# ==========================================
LOG_MAX_BYTES = 10485760  # 10MB
LOG_BACKUP_COUNT = 5
