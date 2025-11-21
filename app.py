"""
Weather Data Producer
Fetches weather data from OpenWeatherMap API and streams to Kafka
"""

import json
import time
import signal
import sys
from datetime import datetime, timezone
from typing import Dict, Optional, Any
import random
import requests
from kafka.errors import KafkaError, KafkaTimeoutError

from config import Config
from logger import setup_logger, log_error, log_success, log_warning
from constants import (
    FIELD_TIMESTAMP, FIELD_TEMPERATURE, FIELD_FEELS_LIKE,
    FIELD_HUMIDITY, FIELD_PRESSURE, FIELD_WIND_SPEED,
    FIELD_WIND_DIRECTION, FIELD_VISIBILITY, FIELD_CONDITION,
    FIELD_DESCRIPTION, FIELD_LOCATION, FIELD_COUNTRY,
    FIELD_SUNRISE, FIELD_SUNSET, FIELD_CLOUDINESS,
    TEMP_MIN, TEMP_MAX, HUMIDITY_MIN, HUMIDITY_MAX,
    PRESSURE_MIN, PRESSURE_MAX, WIND_SPEED_MIN, WIND_SPEED_MAX
)

# Setup logger
logger = setup_logger(__name__)

# Global variables
producer: Optional[KafkaProducer] = None
running = True
message_count = 0


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    running = False


def validate_weather_data(data: Dict[str, Any]) -> bool:
    """
    Validate weather data against expected ranges
    
    Args:
        data: Weather data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    try:
        temp = data.get(FIELD_TEMPERATURE, 0)
        humidity = data.get(FIELD_HUMIDITY, 0)
        pressure = data.get(FIELD_PRESSURE, 0)
        wind_speed = data.get(FIELD_WIND_SPEED, 0)
        
        # Validate temperature
        if not (TEMP_MIN <= temp <= TEMP_MAX):
            log_warning(logger, f"Temperature out of range: {temp}°C")
            return False
        
        # Validate humidity
        if not (HUMIDITY_MIN <= humidity <= HUMIDITY_MAX):
            log_warning(logger, f"Humidity out of range: {humidity}%")
            return False
        
        # Validate pressure
        if not (PRESSURE_MIN <= pressure <= PRESSURE_MAX):
            log_warning(logger, f"Pressure out of range: {pressure} hPa")
            return False
        
        # Validate wind speed
        if not (WIND_SPEED_MIN <= wind_speed <= WIND_SPEED_MAX):
            log_warning(logger, f"Wind speed out of range: {wind_speed} km/h")
            return False
        
        return True
    except Exception as e:
        log_error(logger, e, "Data validation error")
        return False


def fetch_weather_data(city: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
    """
    Fetch weather data from OpenWeatherMap API with retry logic
    
    Args:
        city: City name to fetch weather for
        retry_count: Current retry attempt
        
    Returns:
        Weather data dictionary or None if failed
    """
    try:
        api_url = Config.get_api_url(city)
        response = requests.get(api_url, timeout=Config.API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        # Add small random noise to simulate variation
        temp_noise = random.uniform(-0.5, 0.5)
        feels_like_noise = random.uniform(-0.5, 0.5)
        
        # Parse and structure the data
        weather_data = {
            FIELD_TIMESTAMP: datetime.now(timezone.utc).isoformat(),
            FIELD_TEMPERATURE: round(data['main']['temp'] + temp_noise, 2),
            FIELD_FEELS_LIKE: round(data['main']['feels_like'] + feels_like_noise, 2),
            FIELD_HUMIDITY: data['main']['humidity'],
            FIELD_PRESSURE: data['main']['pressure'],
            FIELD_WIND_SPEED: round(data['wind']['speed'] * 3.6, 2),  # Convert m/s to km/h
            FIELD_WIND_DIRECTION: data['wind'].get('deg', 0),
            FIELD_VISIBILITY: data.get('visibility', 10000) / 1000,  # Convert m to km
            FIELD_CONDITION: data['weather'][0]['main'],
            FIELD_DESCRIPTION: data['weather'][0]['description'],
            FIELD_LOCATION: city,
            FIELD_COUNTRY: data['sys']['country'],
            FIELD_SUNRISE: datetime.fromtimestamp(
                data['sys']['sunrise'], tz=timezone.utc
            ).isoformat(),
            FIELD_SUNSET: datetime.fromtimestamp(
                data['sys']['sunset'], tz=timezone.utc
            ).isoformat(),
            FIELD_CLOUDINESS: data['clouds']['all']
        }
        
        # Validate data before returning
        if validate_weather_data(weather_data):
            return weather_data
        else:
            log_warning(logger, f"Invalid weather data for {city}")
            return None
            
    except requests.exceptions.Timeout:
        log_warning(logger, f"API request timeout for {city}")
        if retry_count < Config.API_MAX_RETRIES:
            time.sleep(Config.API_RETRY_DELAY * (retry_count + 1))
            return fetch_weather_data(city, retry_count + 1)
        return None
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            log_error(logger, e, f"City not found: {city}")
        elif e.response.status_code == 401:
            log_error(logger, e, "Invalid API key")
        else:
            log_error(logger, e, f"HTTP error for {city}")
        return None
        
    except requests.exceptions.RequestException as e:
        log_error(logger, e, f"API request error for {city}")
        if retry_count < Config.API_MAX_RETRIES:
            time.sleep(Config.API_RETRY_DELAY * (retry_count + 1))
            return fetch_weather_data(city, retry_count + 1)
        return None
        
    except KeyError as e:
        log_error(logger, e, f"Missing data field in API response for {city}")
        return None
        
    except Exception as e:
        log_error(logger, e, f"Unexpected error fetching data for {city}")
        return None


def send_to_kafka(data: Dict[str, Any]) -> bool:
    """
    Send weather data to Kafka topic
    
    Args:
        data: Weather data dictionary
        
    Returns:
        True if successful, False otherwise
    """
    global message_count
    
    try:
        future = producer.send(Config.KAFKA_TOPIC, value=data)
        record_metadata = future.get(timeout=10)
        
        message_count += 1
        log_success(
            logger,
            f"Message #{message_count} sent",
            city=data[FIELD_LOCATION],
            temp=f"{data[FIELD_TEMPERATURE]}°C",
            partition=record_metadata.partition,
            offset=record_metadata.offset
        )
        return True
        
    except KafkaTimeoutError:
        log_warning(logger, "Kafka send timeout")
        return False
        
    except KafkaError as e:
        log_error(logger, e, "Failed to send message to Kafka")
        return False
        
    except Exception as e:
        log_error(logger, e, "Unexpected error sending to Kafka")
        return False


def initialize_producer() -> Optional[KafkaProducer]:
    """
    Initialize Kafka producer with configuration
    
    Returns:
        KafkaProducer instance or None if failed
    """
    try:
        producer = KafkaProducer(
            bootstrap_servers=[Config.KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks=Config.KAFKA_ACKS,
            retries=Config.KAFKA_RETRIES,
            max_in_flight_requests_per_connection=Config.KAFKA_MAX_IN_FLIGHT,
            request_timeout_ms=Config.KAFKA_REQUEST_TIMEOUT,
            retry_backoff_ms=Config.KAFKA_RETRY_BACKOFF
        )
        
        log_success(logger, "Kafka Producer connected", broker=Config.KAFKA_BROKER)
        logger.info(f"📡 Streaming weather data to topic '{Config.KAFKA_TOPIC}'")
        logger.info(f"⏱️  Fetch interval: ~40 seconds (10 cities)")
        logger.info(f"🌍 Rotating through {len(Config.CITIES)} cities\n")
        
        return producer
        
    except KafkaError as e:
        log_error(logger, e, "Failed to connect to Kafka")
        return None
        
    except Exception as e:
        log_error(logger, e, "Unexpected error initializing producer")
        return None


def main():
    """Main producer loop – rotates through ALL cities with real data"""
    global producer, running
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    Config.display_config()
    
    producer = initialize_producer()
    if not producer:
        logger.error("Failed to initialize producer. Exiting.")
        sys.exit(1)
    
    logger.info("Starting multi-city real data collection loop...")
    logger.info(f"Rotating through {len(Config.CITIES)} cities every ~40 seconds\n")
    
    try:
        while running:
            for city_query in Config.CITIES:
                if not running:
                    break
                
                city_name = city_query.split(',')[0]
                weather_data = fetch_weather_data(city_query)
                
                if weather_data:
                    weather_data[FIELD_LOCATION] = city_name
                    send_to_kafka(weather_data)
                else:
                    log_warning(logger, f"Failed to fetch data for {city_name}")
                
                time.sleep(3)  # Be nice to API
            
            time.sleep(10)  # Pause after full rotation
    
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        log_error(logger, e, "Unexpected error in main loop")
    finally:
        if producer:
            logger.info("Flushing remaining messages...")
            producer.flush()
            producer.close()
            log_success(logger, "Producer closed gracefully")
        
        logger.info(f"Total messages sent: {message_count}")
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
