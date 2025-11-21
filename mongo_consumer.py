"""
Weather Data Consumer
Consumes weather data from Kafka and stores in MongoDB
"""

import json
import signal
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import (
    ConnectionFailure, 
    DuplicateKeyError,
    PyMongoError
)

from config import Config
from logger import setup_logger, log_error, log_success, log_warning
from constants import (
    FIELD_TIMESTAMP, FIELD_LOCATION, FIELD_TEMPERATURE,
    INDEX_TIMESTAMP, INDEX_LOCATION, INDEX_TIMESTAMP_LOCATION
)

# Setup logger
logger = setup_logger(__name__)

# Global variables
consumer: Optional[KafkaConsumer] = None
mongo_client: Optional[MongoClient] = None
collection = None
running = True
message_count = 0
batch_buffer: List[Dict[str, Any]] = []


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    running = False


def create_indexes():
    """Create MongoDB indexes for better query performance"""
    try:
        collection.create_index(
            [(FIELD_TIMESTAMP, DESCENDING)],
            name=INDEX_TIMESTAMP,
            background=True
        )
        logger.info(f"Created index: {INDEX_TIMESTAMP}")
        
        collection.create_index(
            [(FIELD_LOCATION, ASCENDING)],
            name=INDEX_LOCATION,
            background=True
        )
        logger.info(f"Created index: {INDEX_LOCATION}")
        
        collection.create_index(
            [(FIELD_TIMESTAMP, DESCENDING), (FIELD_LOCATION, ASCENDING)],
            name=INDEX_TIMESTAMP_LOCATION,
            background=True
        )
        logger.info(f"Created compound index: {INDEX_TIMESTAMP_LOCATION}")
        
        log_success(logger, "All indexes created successfully")
        
    except PyMongoError as e:
        log_error(logger, e, "Failed to create indexes")


# NEW — convert timestamp from string → datetime.utc
def fix_timestamp_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures the timestamp is stored as a datetime object in UTC.
    Producer sends ISO8601 string timestamps, but MongoDB must store datetime.
    """
    if FIELD_TIMESTAMP in data:
        try:
            # Example input: "2025-01-15T12:00:02Z"
            parsed = datetime.fromisoformat(data[FIELD_TIMESTAMP].replace("Z", "+00:00"))
            data[FIELD_TIMESTAMP] = parsed.astimezone(timezone.utc)
        except Exception:
            log_warning(logger, f"Invalid timestamp format: {data[FIELD_TIMESTAMP]}")
    return data


def validate_message(data: Dict[str, Any]) -> bool:
    required_fields = [
        FIELD_TIMESTAMP,
        FIELD_TEMPERATURE,
        FIELD_LOCATION
    ]
    
    for field in required_fields:
        if field not in data:
            log_warning(logger, f"Missing required field: {field}")
            return False
    
    return True


def check_duplicate(data: Dict[str, Any]) -> bool:
    try:
        existing = collection.find_one({
            FIELD_TIMESTAMP: data[FIELD_TIMESTAMP],
            FIELD_LOCATION: data[FIELD_LOCATION]
        })
        return existing is not None
    except PyMongoError as e:
        log_error(logger, e, "Error checking for duplicates")
        return False


def insert_data(data: Dict[str, Any]) -> bool:
    global message_count
    
    try:
        # FIX APPLIED HERE
        data = fix_timestamp_format(data)

        if not validate_message(data):
            log_warning(logger, "Invalid message data, skipping")
            return False
        
        if check_duplicate(data):
            log_warning(
                logger,
                "Duplicate record detected, skipping",
                timestamp=data[FIELD_TIMESTAMP],
                location=data[FIELD_LOCATION]
            )
            return False
        
        result = collection.insert_one(data)
        
        if result.inserted_id:
            message_count += 1
            log_success(
                logger,
                f"Message #{message_count} saved",
                timestamp=data[FIELD_TIMESTAMP],
                location=data[FIELD_LOCATION],
                temp=f"{data[FIELD_TEMPERATURE]}°C",
                total=collection.count_documents({})
            )
            return True
        else:
            log_warning(logger, "Insert failed, no ID returned")
            return False
            
    except DuplicateKeyError:
        log_warning(logger, "Duplicate key error, skipping")
        return False
        
    except PyMongoError as e:
        log_error(logger, e, "MongoDB insert error")
        return False
        
    except Exception as e:
        log_error(logger, e, "Unexpected error during insert")
        return False


def batch_insert_data(batch: List[Dict[str, Any]]) -> int:
    if not batch:
        return 0
    
    try:
        valid_records = []
        for data in batch:
            # FIX APPLIED HERE ALSO
            data = fix_timestamp_format(data)

            if validate_message(data) and not check_duplicate(data):
                valid_records.append(data)
        
        if not valid_records:
            return 0
        
        result = collection.insert_many(valid_records, ordered=False)
        inserted_count = len(result.inserted_ids)
        
        log_success(
            logger,
            f"Batch insert completed",
            inserted=inserted_count,
            total=collection.count_documents({})
        )
        
        return inserted_count
        
    except PyMongoError as e:
        log_error(logger, e, "Batch insert error")
        return 0
        
    except Exception as e:
        log_error(logger, e, "Unexpected error during batch insert")
        return 0


def initialize_mongodb() -> bool:
    global mongo_client, collection
    
    try:
        mongo_client = MongoClient(
            Config.MONGO_URI,
            maxPoolSize=Config.MONGO_MAX_POOL_SIZE,
            minPoolSize=Config.MONGO_MIN_POOL_SIZE,
            serverSelectionTimeoutMS=Config.MONGO_SERVER_SELECTION_TIMEOUT,
            connectTimeoutMS=Config.MONGO_CONNECT_TIMEOUT,
            socketTimeoutMS=Config.MONGO_SOCKET_TIMEOUT
        )
        
        mongo_client.admin.command('ping')
        
        db = mongo_client[Config.MONGO_DB_NAME]
        collection = db[Config.MONGO_COLLECTION_NAME]
        
        initial_count = collection.count_documents({})
        
        log_success(
            logger,
            "MongoDB connected",
            database=Config.MONGO_DB_NAME,
            collection=Config.MONGO_COLLECTION_NAME,
            documents=initial_count
        )
        
        create_indexes()
        
        return True
        
    except ConnectionFailure as e:
        log_error(logger, e, "MongoDB connection failed")
        return False
        
    except PyMongoError as e:
        log_error(logger, e, "MongoDB initialization error")
        return False
        
    except Exception as e:
        log_error(logger, e, "Unexpected error initializing MongoDB")
        return False


def initialize_consumer() -> Optional[KafkaConsumer]:
    try:
        consumer = KafkaConsumer(
            Config.KAFKA_TOPIC,
            bootstrap_servers=[Config.KAFKA_BROKER],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset=Config.KAFKA_AUTO_OFFSET_RESET,
            enable_auto_commit=Config.KAFKA_ENABLE_AUTO_COMMIT,
            group_id=Config.KAFKA_GROUP_ID
        )
        
        log_success(
            logger,
            "Kafka Consumer connected",
            broker=Config.KAFKA_BROKER,
            topic=Config.KAFKA_TOPIC,
            group=Config.KAFKA_GROUP_ID
        )
        
        return consumer
        
    except KafkaError as e:
        log_error(logger, e, "Failed to connect to Kafka")
        return None
        
    except Exception as e:
        log_error(logger, e, "Unexpected error initializing consumer")
        return None


def main():
    global consumer, running, batch_buffer
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    Config.display_config()
    
    logger.info("🔧 Starting MongoDB Consumer...")
    
    if not initialize_mongodb():
        logger.error("Failed to initialize MongoDB. Exiting.")
        sys.exit(1)
    
    consumer = initialize_consumer()
    if not consumer:
        logger.error("Failed to initialize Kafka consumer. Exiting.")
        sys.exit(1)
    
    logger.info("Waiting for messages...\n")
    
    try:
        for message in consumer:
            if not running:
                break
            
            try:
                data = message.value
                
                if Config.BATCH_SIZE > 1:
                    batch_buffer.append(data)
                    
                    if len(batch_buffer) >= Config.BATCH_SIZE:
                        batch_insert_data(batch_buffer)
                        batch_buffer.clear()
                else:
                    insert_data(data)
                    
            except json.JSONDecodeError as e:
                log_error(logger, e, "Failed to decode message")
                continue
                
            except Exception as e:
                log_error(logger, e, "Error processing message")
                continue
        
        if batch_buffer:
            logger.info("Inserting remaining batch items...")
            batch_insert_data(batch_buffer)
            batch_buffer.clear()
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        
    except Exception as e:
        log_error(logger, e, "Unexpected error in main loop")
        
    finally:
        if consumer:
            logger.info("Closing Kafka consumer...")
            consumer.close()
            log_success(logger, "Consumer closed")
        
        if mongo_client:
            logger.info("Closing MongoDB connection...")
            mongo_client.close()
            log_success(logger, "MongoDB connection closed")
        
        logger.info(f"Total messages processed: {message_count}")
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
