# 🌤️ Weather Reporting System - Real-time Data Streaming Dashboard

A comprehensive big data streaming application that collects, processes, and visualizes real-time weather data using **MongoDB-Kafka-Streamlit** pipeline.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![Kafka](https://img.shields.io/badge/Apache%20Kafka-3.8-black.svg)](https://kafka.apache.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://www.mongodb.com/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

This project implements a **real-time weather monitoring system** that demonstrates big data streaming concepts using industry-standard tools. It fetches weather data from the OpenWeatherMap API, streams it through Apache Kafka, stores it in MongoDB, and visualizes it in an interactive Streamlit dashboard.

### Key Highlights

- ✅ **Real-time Data Streaming**: 15-second refresh intervals
- ✅ **Scalable Architecture**: MongoDB-Kafka pipeline
- ✅ **Interactive Dashboard**: Live and historical data views
- ✅ **Data Aggregation**: Hourly, daily, and custom time ranges
- ✅ **Multiple Export Formats**: CSV, Excel, PDF
- ✅ **Weather Forecasting**: Linear regression-based predictions
- ✅ **Multi-city Support**: Track weather across multiple locations
- ✅ **Robust Error Handling**: Comprehensive logging and validation

---

## 🏗️ Architecture

```
┌─────────────────┐
│ OpenWeatherMap  │
│      API        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Producer     │ ◄── Fetches weather data every 15s
│   (producer.py) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Apache Kafka   │ ◄── Message broker for streaming
│     Topic       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Consumer     │ ◄── Consumes and validates data
│(mongo_consumer) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MongoDB Atlas  │ ◄── Persistent storage with indexes
│   (Database)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Streamlit     │ ◄── Interactive web dashboard
│   Dashboard     │
│    (app.py)     │
└─────────────────┘
```

### Pipeline Flow

1. **Data Collection**: Producer fetches weather data from OpenWeatherMap API
2. **Streaming**: Data is published to Kafka topic
3. **Processing**: Consumer validates and processes messages
4. **Storage**: Validated data is stored in MongoDB with proper indexing
5. **Visualization**: Streamlit dashboard queries and displays data in real-time

---

## ✨ Features

### Core Features

- 🔴 **Live Dashboard**: Real-time weather monitoring with auto-refresh
- 📊 **Historical Analysis**: View trends over custom time ranges
- 🌍 **Multi-city Support**: Track weather across multiple Philippine cities
- 📈 **Data Aggregation**: Hourly statistics (min, max, average)
- 🔮 **Weather Forecasting**: Predict temperature for next 3 hours
- 📥 **Data Export**: Download data in CSV, Excel, or PDF formats
- ⚠️ **Smart Alerts**: Temperature-based warnings and notifications
- 🎨 **Theme Support**: Dark and light mode options

### Technical Features

- ✅ **Secure Configuration**: Environment-based credential management
- ✅ **Data Validation**: Schema validation before storage
- ✅ **Duplicate Detection**: Prevents redundant data insertion
- ✅ **Connection Pooling**: Optimized database connections
- ✅ **Indexed Queries**: Fast data retrieval with MongoDB indexes
- ✅ **Graceful Shutdown**: Proper cleanup on termination
- ✅ **Comprehensive Logging**: Detailed logs for debugging
- ✅ **Error Recovery**: Retry logic for transient failures

---

## 📋 Prerequisites

### Required Software

1. **Python 3.8+**
   - Download: https://www.python.org/downloads/

2. **Java Development Kit (JDK) 17+**
   - Required for Apache Kafka
   - Download: https://adoptium.net/

3. **Apache Kafka 3.8+**
   - Included in the `kafka/` directory
   - Or download: https://kafka.apache.org/downloads

4. **MongoDB Atlas Account** (Free Tier)
   - Sign up: https://www.mongodb.com/cloud/atlas/register

5. **OpenWeatherMap API Key** (Free)
   - Sign up: https://openweathermap.org/api

### System Requirements

- **OS**: Windows 10+, macOS 10.14+, or Linux
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: 2GB free space
- **Network**: Stable internet connection

---

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/weather-reporting-system.git
cd weather-reporting-system
```

### Step 2: Set Up Python Environment

**Using Conda (Recommended):**

```bash
# Create environment
conda create -n weather python=3.10
conda activate weather

# Install dependencies
pip install -r requirements.txt
```

**Using venv:**

```bash
# Create environment
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Set Up MongoDB Atlas

1. **Create a MongoDB Atlas Account**
   - Go to https://www.mongodb.com/cloud/atlas/register
   - Sign up for a free account

2. **Create a Cluster**
   - Click "Build a Database"
   - Choose "Free" tier (M0)
   - Select your preferred region
   - Click "Create Cluster"

3. **Create Database User**
   - Go to "Database Access"
   - Click "Add New Database User"
   - Choose "Password" authentication
   - Set username and password
   - Grant "Read and write to any database" role

4. **Configure Network Access**
   - Go to "Network Access"
   - Click "Add IP Address"
   - Click "Allow Access from Anywhere" (for development)
   - Or add your specific IP address

5. **Get Connection String**
   - Go to "Database" → "Connect"
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password

### Step 4: Get OpenWeatherMap API Key

1. Go to https://openweathermap.org/api
2. Sign up for a free account
3. Navigate to "API keys" section
4. Copy your API key

### Step 5: Configure Environment Variables

1. **Copy the example environment file:**

```bash
cp .env.example .env
```

2. **Edit `.env` file with your credentials:**

```env
# Kafka Configuration
KAFKA_BROKER=localhost:9092
KAFKA_TOPIC=weather-data

# MongoDB Configuration
MONGO_URI=mongodb+srv://your_username:your_password@your-cluster.mongodb.net/weather_db?retryWrites=true&w=majority
MONGO_DB_NAME=weather_db
MONGO_COLLECTION_NAME=weather_data

# OpenWeatherMap API
OPENWEATHERMAP_API_KEY=your_api_key_here

# Producer Configuration
DEFAULT_CITY=Quezon City
FETCH_INTERVAL=15

# Dashboard Configuration
AUTO_REFRESH_INTERVAL=15000
```

### Step 6: Start Apache Kafka

**Windows:**

```bash
# Start Zookeeper
cd kafka
bin\windows\zookeeper-server-start.bat config\zookeeper.properties

# In a new terminal, start Kafka
cd kafka
bin\windows\kafka-server-start.bat config\server.properties
```

**macOS/Linux:**

```bash
# Start Zookeeper
cd kafka
bin/zookeeper-server-start.sh config/zookeeper.properties

# In a new terminal, start Kafka
cd kafka
bin/kafka-server-start.sh config/server.properties
```

### Step 7: Create Kafka Topic

**Windows:**

```bash
cd kafka
bin\windows\kafka-topics.bat --create --topic weather-data --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

**macOS/Linux:**

```bash
cd kafka
bin/kafka-topics.sh --create --topic weather-data --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

---

## 🎮 Usage

### Running the Complete System

You need **three separate terminal windows**:

#### Terminal 1: Start the Producer

```bash
# Activate environment
conda activate weather
# or: source venv/bin/activate

# Run producer
python producer.py
```

**Expected Output:**
```
============================================================
WEATHER REPORTING SYSTEM - CONFIGURATION
============================================================
Kafka Broker: localhost:9092
Kafka Topic: weather-data
MongoDB Database: weather_db
...
✅ Kafka Producer connected | broker=localhost:9092
📡 Streaming weather data to topic 'weather-data'
⏱️  Fetch interval: 15 seconds
🌍 Default city: Quezon City

✅ Message #1 sent | city=Quezon City | temp=28.5°C | partition=0 | offset=0
```

#### Terminal 2: Start the Consumer

```bash
# Activate environment
conda activate weather
# or: source venv/bin/activate

# Run consumer
python mongo_consumer.py
```

**Expected Output:**
```
============================================================
WEATHER REPORTING SYSTEM - CONFIGURATION
============================================================
...
🔧 Starting MongoDB Consumer...
✅ MongoDB connected | database=weather_db | collection=weather_data | documents=0
Created index: timestamp
Created index: location
Created compound index: timestamp_location
✅ All indexes created successfully
✅ Kafka Consumer connected | broker=localhost:9092 | topic=weather-data
Waiting for messages...

✅ Message #1 saved | timestamp=2024-01-15T10:30:00Z | location=Quezon City | temp=28.5°C | total=1
```

#### Terminal 3: Start the Dashboard

```bash
# Activate environment
conda activate weather
# or: source venv/bin/activate

# Run dashboard
streamlit run app.py
```

**Expected Output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

The dashboard will automatically open in your default web browser at `http://localhost:8501`.

---

## 📁 Project Structure

```
weather-reporting-system/
│
├── app.py                  # Streamlit dashboard (main UI)
├── producer.py             # Kafka producer (data collection)
├── mongo_consumer.py       # Kafka consumer (data storage)
├── config.py               # Configuration management
├── constants.py            # Application constants
├── logger.py               # Logging utilities
│
├── .env                    # Environment variables (create from .env.example)
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── TODO.md                 # Development roadmap
│
├── kafka/                  # Apache Kafka installation
│   ├── bin/                # Kafka executables
│   ├── config/             # Kafka configuration
│   └── libs/               # Kafka libraries
│
└── tests/                  # Unit and integration tests (future)
```

---

## 📚 API Documentation

### OpenWeatherMap API

**Endpoint:** `http://api.openweathermap.org/data/2.5/weather`

**Parameters:**
- `q`: City name (e.g., "Quezon City")
- `appid`: Your API key
- `units`: "metric" for Celsius

**Response Fields Used:**
- `main.temp`: Temperature
- `main.feels_like`: Feels like temperature
- `main.humidity`: Humidity percentage
- `main.pressure`: Atmospheric pressure
- `wind.speed`: Wind speed
- `weather[0].main`: Weather condition
- `weather[0].description`: Detailed description

**Rate Limits:**
- Free tier: 60 calls/minute, 1,000,000 calls/month

---

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `KAFKA_BROKER` | Kafka broker address | `localhost:9092` | No |
| `KAFKA_TOPIC` | Kafka topic name | `weather-data` | No |
| `MONGO_URI` | MongoDB connection string | - | **Yes** |
| `MONGO_DB_NAME` | Database name | `weather_db` | No |
| `MONGO_COLLECTION_NAME` | Collection name | `weather_data` | No |
| `OPENWEATHERMAP_API_KEY` | API key | - | **Yes** |
| `DEFAULT_CITY` | Default city to monitor | `Quezon City` | No |
| `FETCH_INTERVAL` | Data fetch interval (seconds) | `15` | No |
| `AUTO_REFRESH_INTERVAL` | Dashboard refresh (ms) | `15000` | No |

### Supported Cities

- Quezon City
- Manila
- Cebu City
- Davao City
- Makati
- Pasig
- Taguig
- Caloocan

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Kafka Connection Error

**Error:** `Failed to connect to Kafka`

**Solutions:**
- Ensure Kafka and Zookeeper are running
- Check if port 9092 is available
- Verify `KAFKA_BROKER` in `.env` file
- Check firewall settings

#### 2. MongoDB Connection Error

**Error:** `Failed to connect to MongoDB`

**Solutions:**
- Verify MongoDB URI in `.env` file
- Check network access settings in MongoDB Atlas
- Ensure database user has correct permissions
- Test connection using MongoDB Compass

#### 3. API Key Invalid

**Error:** `Invalid API key`

**Solutions:**
- Verify API key in `.env` file
- Check if API key is activated (may take a few hours)
- Ensure no extra spaces in the key
- Generate a new API key if needed

#### 4. Module Not Found

**Error:** `ModuleNotFoundError: No module named 'xxx'`

**Solutions:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install specific package
pip install package-name
```

#### 5. Port Already in Use

**Error:** `Address already in use`

**Solutions:**
```bash
# Windows - Find and kill process
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8501 | xargs kill -9
```

### Logging

Check logs for detailed error information:
- Producer logs: Console output from `producer.py`
- Consumer logs: Console output from `mongo_consumer.py`
- Dashboard logs: Streamlit console output

---

## 📊 Data Schema

### Weather Data Document

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "temperature": 28.5,
  "feels_like": 30.2,
  "humidity": 75,
  "pressure": 1013,
  "wind_speed": 12.5,
  "wind_direction": 180,
  "visibility": 10.0,
  "condition": "Clouds",
  "description": "scattered clouds",
  "location": "Quezon City",
  "country": "PH",
  "sunrise": "2024-01-15T22:30:00.000Z",
  "sunset": "2024-01-15T10:45:00.000Z",
  "cloudiness": 40
}
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to functions
- Write docstrings for all functions
- Add unit tests for new features
- Update documentation as needed

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👥 Author and Manager

- **Alastair N. De Guzman** - *College Student*

---

## 👥 Teammates
- **Andrei Nycole So Bona** - *College Student*
- **Danica Guariño** - *College Student*
- **Andrei Santos** - *College Student*

---

## 👥 Adivser
- **Neal Barton James Matira** - *Professor*

---

## 🙏 Acknowledgments

- OpenWeatherMap for providing free weather API
- Apache Kafka for streaming infrastructure
- MongoDB for database services
- Streamlit for dashboard framework
- Python community for excellent libraries

