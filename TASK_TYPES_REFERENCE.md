# 📋 Complete Task Types Reference - WinLink

## Overview
WinLink now supports **17 different task types** covering computation, data processing, networking, machine learning, and more. Each task type comes with ready-to-use templates and extensive capabilities.

---

## 🎯 Task Type Categories

### 1. Computation Tasks
- **COMPUTATION** - Mathematical calculations and algorithms
- **BENCHMARK** - Performance testing and benchmarking

### 2. Data Processing Tasks
- **DATA_ANALYSIS** - Statistical analysis and data insights
- **FILE_PROCESSING** - File operations and transformations
- **TEXT_PROCESSING** - Advanced text analysis and manipulation

### 3. Media & Content Tasks
- **IMAGE_PROCESSING** - Image manipulation and analysis
- **VIDEO_PLAYBACK** - Video streaming and playback

### 4. Network Tasks
- **NETWORK_DIAGNOSTICS** - Network testing and troubleshooting
- **API_REQUEST** - External API interactions
- **WEB_SCRAPING** - Web data extraction

### 5. System Tasks
- **SYSTEM_MONITORING** - System health and resource monitoring
- **BACKUP** - Backup and restore operations

### 6. Security & Encryption Tasks
- **ENCRYPTION** - Data encryption, hashing, encoding

### 7. Advanced Tasks
- **MACHINE_LEARNING** - ML model training and predictions
- **DATABASE_QUERY** - Database operations
- **COMPRESSION** - File compression and decompression
- **CUSTOM** - User-defined custom tasks

---

## 📊 Task Type Details

### 🔢 COMPUTATION

**Purpose**: Mathematical computations and algorithm execution

**Available Templates**:

#### 1. **Hello World Test**
- Simple test task to verify system
- Returns formatted message
- Good for testing connectivity

```python
# Sample Data
{"name": "WinLink User"}

# Returns
{
  "message": "Hello, WinLink User!",
  "length": 20,
  "uppercase": "HELLO, WINLINK USER!",
  "status": "success"
}
```

#### 2. **Fibonacci Series**
- Generate Fibonacci sequence
- Calculate nth Fibonacci number
- Includes series statistics

```python
# Sample Data
{"n": 10}

# Returns
{
  "series": [0, 1, 1, 2, 3, 5, 8, 13, 21, 34],
  "nth_number": 55,
  "count": 10,
  "sum": 88
}
```

#### 3. **Prime Number Check**
- Verify if number is prime
- Efficient algorithm
- Large number support

```python
# Sample Data
{"number": 982451653}

# Returns
true  // or false
```

#### 4. **Factorial Calculation**
- Calculate n! (factorial)
- Includes formula display
- Error handling for negative numbers

```python
# Sample Data
{"n": 10}

# Returns
{
  "number": 10,
  "factorial": 3628800,
  "formula": "10!"
}
```

#### 5. **Matrix Multiplication**
- Multiply two matrices
- Validates dimensions
- Efficient computation

```python
# Sample Data
{
  "matrix_a": [[1, 2], [3, 4]],
  "matrix_b": [[5, 6], [7, 8]]
}

# Returns
[[19, 22], [43, 50]]
```

---

### 📊 DATA_ANALYSIS

**Purpose**: Statistical analysis and data insights

**Available Templates**:

#### 1. **Data Processing**
- Calculate statistical measures
- Mean, median, standard deviation
- Min/max values

```python
# Sample Data
{"numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}

# Returns
{
  "count": 10,
  "sum": 55,
  "mean": 5.5,
  "median": 5.5,
  "std_dev": 2.87,
  "min": 1,
  "max": 10
}
```

#### 2. **JSON Validation & Analysis**
- Validate JSON structure
- Analyze JSON contents
- Count elements by type
- Calculate depth

```python
# Sample Data
{
  "json_string": '{"name": "John", "age": 30, "hobbies": ["reading"]}'
}

# Returns
{
  "valid": true,
  "size_bytes": 59,
  "size_kb": 0.06,
  "structure": {
    "objects": 1,
    "arrays": 1,
    "strings": 3,
    "numbers": 1,
    "max_depth": 2
  }
}
```

---

### 📁 FILE_PROCESSING

**Purpose**: File operations and analysis

**Available Templates**:

#### 1. **Text File Analysis**
- Count lines, words, characters
- Calculate averages
- Text statistics

```python
# Sample Data
{
  "text": "This is a sample text.\nIt has multiple lines."
}

# Returns
{
  "line_count": 2,
  "word_count": 9,
  "char_count": 44,
  "char_count_no_spaces": 37,
  "avg_words_per_line": 4.5
}
```

#### 2. **CSV Data Processing**
- Process CSV-like data
- Calculate numeric statistics
- Column analysis

```python
# Sample Data
{
  "rows": [
    ["Name", "Age", "Score"],
    ["Alice", "25", "85"],
    ["Bob", "30", "92"]
  ]
}

# Returns
{
  "total_rows": 2,
  "columns": 3,
  "numeric_columns": {
    "Age": {"min": 25, "max": 30, "avg": 27.5},
    "Score": {"min": 85, "max": 92, "avg": 88.5}
  }
}
```

#### 3. **File Size Analyzer**
- Calculate file sizes in multiple units
- Estimate download times
- Bandwidth calculations

```python
# Sample Data
{
  "size_bytes": 1073741824,  # 1 GB
  "bandwidth_mbps": 100
}

# Returns
{
  "size": {
    "bytes": 1073741824,
    "formatted": "1.00 GB",
    "megabytes": 1024.00
  },
  "download_estimates": {
    "100_mbps": {
      "time_seconds": 85.9,
      "time_formatted": "1m 26s"
    }
  }
}
```

---

### 🖼️ IMAGE_PROCESSING

**Purpose**: Image analysis and manipulation

**Available Templates**:

#### 1. **Image Statistics**
- Analyze pixel data
- Calculate min/max/average values
- Image dimensions

```python
# Sample Data
{
  "pixels": [
    [[255, 0, 0], [0, 255, 0]],
    [[0, 0, 255], [128, 128, 128]]
  ]
}

# Returns
{
  "width": 2,
  "height": 2,
  "total_pixels": 4,
  "min_value": 0,
  "max_value": 255,
  "avg_value": 112.5
}
```

#### 2. **Color Histogram**
- Generate color distribution
- Count unique colors
- Percentage breakdown

```python
# Sample Data
{
  "pixels": [
    [[255, 0, 0], [0, 255, 0], [0, 0, 255]]
  ]
}

# Returns
{
  "total_pixels": 3,
  "unique_colors": 3,
  "histogram": {
    "RGB(255,0,0)": 1,
    "RGB(0,255,0)": 1,
    "RGB(0,0,255)": 1
  }
}
```

---

### 🎬 VIDEO_PLAYBACK

**Purpose**: Stream and play videos from URLs

**Available Templates**:

#### 1. **Stream Video from URL**
- Play videos on worker PC
- Internet URL support
- Dedicated player window

```python
# Sample Data
{
  "video_url": "https://example.com/video.mp4",
  "title": "My Video"
}

# Special handling - opens video player window
```

**Supported Formats**:
- MP4, AVI, MKV, MOV
- Streaming URLs (M3U8)
- Direct video links

---

### 🖥️ SYSTEM_MONITORING

**Purpose**: Monitor system health and resources

**Available Templates**:

#### 1. **System Health Check**
- Comprehensive system analysis
- CPU, memory, disk, network stats
- Platform information
- Health status determination

```python
# Sample Data
{}  # No input needed

# Returns
{
  "timestamp": "2025-12-15T10:30:00",
  "platform": {
    "system": "Windows",
    "release": "10",
    "machine": "AMD64"
  },
  "cpu": {
    "physical_cores": 4,
    "logical_cores": 8,
    "usage_percent": 45.2
  },
  "memory": {
    "total_gb": 16.00,
    "available_gb": 8.50,
    "percent": 46.9
  },
  "status": "HEALTHY",
  "issues": []
}
```

---

### 🌐 NETWORK_DIAGNOSTICS

**Purpose**: Network testing and troubleshooting

**Available Templates**:

#### 1. **Network Ping Test**
- Test connectivity to multiple hosts
- Measure latency
- OS-agnostic implementation

```python
# Sample Data
{
  "hosts": ["8.8.8.8", "google.com", "1.1.1.1"],
  "ping_count": 4
}

# Returns
{
  "tested_hosts": 3,
  "reachable_hosts": 3,
  "results": {
    "8.8.8.8": {
      "reachable": true,
      "average_ms": "25"
    },
    "google.com": {
      "reachable": true,
      "average_ms": "18"
    }
  }
}
```

---

### 🕸️ WEB_SCRAPING

**Purpose**: Extract data from web pages

**Available Templates**:

#### 1. **Web Page Scraper**
- Fetch and parse HTML
- Extract titles, links, images
- Meta description extraction
- Page statistics

```python
# Sample Data
{
  "url": "https://example.com"
}

# Returns
{
  "url": "https://example.com",
  "success": true,
  "title": "Example Domain",
  "total_links": 15,
  "total_images": 5,
  "page_size_kb": 12.5,
  "sample_links": ["link1", "link2", ...]
}
```

**Features**:
- Custom User-Agent
- Timeout protection
- Error handling
- Link and image counting

---

### 📝 TEXT_PROCESSING

**Purpose**: Advanced text analysis and manipulation

**Available Templates**:

#### 1. **Text Sentiment Analysis**
- Analyze sentiment (Positive/Negative/Neutral)
- Count sentiment words
- Calculate sentiment score
- Word frequency analysis

```python
# Sample Data
{
  "text": "This is a great product! I love it. Excellent quality!"
}

# Returns
{
  "sentiment": "POSITIVE",
  "sentiment_score": 0.667,
  "positive_words_count": 3,
  "negative_words_count": 0,
  "total_words": 10,
  "total_sentences": 3,
  "most_common_words": {
    "great": 1,
    "love": 1,
    "excellent": 1
  }
}
```

**Capabilities**:
- Sentiment detection
- Word frequency analysis
- Sentence counting
- Text statistics

---

### 🔐 ENCRYPTION

**Purpose**: Data encryption, encoding, and hashing

**Available Templates**:

#### 1. **Base64 Encode/Decode**
- Encode text to Base64
- Decode Base64 to text
- Length comparison

```python
# Sample Data (Encode)
{
  "operation": "encode",
  "text": "Hello, World!"
}

# Returns
{
  "operation": "encode",
  "original_text": "Hello, World!",
  "encoded_text": "SGVsbG8sIFdvcmxkIQ==",
  "original_length": 13,
  "encoded_length": 20
}

# Sample Data (Decode)
{
  "operation": "decode",
  "text": "SGVsbG8sIFdvcmxkIQ=="
}

# Returns
{
  "operation": "decode",
  "decoded_text": "Hello, World!",
  "success": true
}
```

#### 2. **Hash Generator**
- Generate MD5, SHA1, SHA256, SHA512 hashes
- Multiple hash algorithms at once
- Hexadecimal output

```python
# Sample Data
{
  "data": "Hello, World!"
}

# Returns
{
  "input_data": "Hello, World!",
  "input_length": 13,
  "hashes": {
    "md5": "65a8e27d8879283831b664bd8b7f0ad4",
    "sha1": "0a0a9f2a6772942557ab5355d76af442f8f65e01",
    "sha256": "dffd6021bb2bd5b0af676290809ec3a5...",
    "sha512": "374d794a95cdcfd8b35993185fef9ba3..."
  }
}
```

---

### 🤖 MACHINE_LEARNING

**Purpose**: ML model training and predictions

**Available Templates**:

#### 1. **Simple Linear Regression**
- Train linear regression model
- Make predictions
- Calculate R-squared
- Generate equation

```python
# Sample Data
{
  "X_train": [1, 2, 3, 4, 5],
  "y_train": [2, 4, 6, 8, 10],
  "X_test": [6, 7, 8]
}

# Returns
{
  "model": {
    "slope": 2.0,
    "intercept": 0.0,
    "equation": "y = 2.0x + 0.0"
  },
  "training": {
    "samples": 5,
    "r_squared": 1.0
  },
  "predictions": {
    "X_test": [6, 7, 8],
    "y_predicted": [12.0, 14.0, 16.0]
  }
}
```

**Features**:
- Training from data
- Prediction on new data
- Model accuracy metrics
- Human-readable equation

---

### 🌐 API_REQUEST

**Purpose**: Interact with external APIs

**Available Templates**:

#### 1. **Fetch Weather Data (Mock)**
- Simulate weather API calls
- Generate realistic weather data
- Multiple metrics

```python
# Sample Data
{
  "city": "New York"
}

# Returns
{
  "city": "New York",
  "temperature_celsius": 22,
  "temperature_fahrenheit": 71.6,
  "condition": "Partly Cloudy",
  "humidity_percent": 65,
  "wind_speed_kmh": 15,
  "feels_like": 22,
  "uv_index": 6,
  "timestamp": "2025-12-15T10:30:00"
}
```

---

### ⚡ BENCHMARK

**Purpose**: Performance testing and benchmarking

**Available Templates**:

#### 1. **CPU Performance Benchmark**
- Test integer operations
- Test floating-point operations
- Test string operations
- Test list operations
- Overall performance score

```python
# Sample Data
{
  "iterations": 100000
}

# Returns
{
  "total_time_seconds": 2.5,
  "system_performance_score": 400000,
  "benchmarks": [
    {
      "test": "Integer Operations",
      "iterations": 100000,
      "time_seconds": 0.45,
      "operations_per_second": 222222
    },
    {
      "test": "Floating Point Operations",
      "iterations": 100000,
      "time_seconds": 0.78,
      "operations_per_second": 128205
    }
  ]
}
```

**Test Categories**:
- Integer arithmetic
- Floating-point math
- String manipulation
- List sorting/operations

---

## 🎯 Task Type Usage Guide

### Creating Tasks in Master UI

1. **Select Task Type** from dropdown
2. **Choose Template** from available options
3. **View Description** to understand task purpose
4. **Review Code** (editable for customization)
5. **Modify Data** (JSON format)
6. **Submit Task** to worker

### Task Execution Flow

```
Master PC                    Worker PC
    │                            │
    ├─ Create Task              │
    ├─ Select Type & Template   │
    ├─ Configure Data           │
    ├─ Submit to Worker ────────>│
    │                            ├─ Receive Task
    │                            ├─ Execute Code
    │                            ├─ Generate Result
    │<──── Send Result ──────────┤
    ├─ Display in Task Queue    │
    └─ Show Output              │
```

---

## 💡 Best Practices

### 1. **Choosing the Right Task Type**
- Use **COMPUTATION** for math/algorithms
- Use **DATA_ANALYSIS** for statistics
- Use **NETWORK_DIAGNOSTICS** for connectivity issues
- Use **SYSTEM_MONITORING** for health checks
- Use **CUSTOM** for unique requirements

### 2. **Data Preparation**
- Ensure JSON is valid
- Provide all required fields
- Use appropriate data types
- Test with sample data first

### 3. **Performance Optimization**
- Start with smaller datasets
- Monitor resource usage
- Use appropriate task types
- Consider task priority

### 4. **Error Handling**
- Review error messages in task log
- Validate input data format
- Check worker connectivity
- Test templates before customization

---

## 🔧 Customization

### Modifying Templates

All templates can be customized:

1. **Edit Code**: Modify Python code in editor
2. **Change Data**: Update JSON data structure
3. **Add Logic**: Include custom algorithms
4. **Import Modules**: Use Python standard library

### Creating Custom Tasks

```python
# Example: Custom Task
{
  "type": "CUSTOM",
  "code": """
def my_custom_function(x, y):
    return x * y + (x ** 2)

a = data.get('a', 5)
b = data.get('b', 10)
result = my_custom_function(a, b)
  """,
  "data": {"a": 5, "b": 10}
}
```

---

## 📊 Task Statistics

| Category | Task Types | Templates | Use Cases |
|----------|------------|-----------|-----------|
| Computation | 2 | 5 | Math, algorithms |
| Data | 2 | 3 | Statistics, analysis |
| Files | 1 | 3 | Text, CSV processing |
| Images | 1 | 2 | Image analysis |
| Media | 1 | 1 | Video streaming |
| System | 1 | 1 | Health monitoring |
| Network | 2 | 2 | Diagnostics, APIs |
| Security | 1 | 2 | Encryption, hashing |
| ML | 1 | 1 | Predictions |
| Benchmarks | 1 | 1 | Performance testing |
| **Total** | **17** | **31** | **All scenarios** |

---

## 🚀 Quick Reference

### Most Common Tasks

1. **System Check**: `system_health_check` - Monitor worker health
2. **Network Test**: `network_ping_test` - Test connectivity
3. **Data Stats**: `data_processing` - Analyze numbers
4. **Text Analysis**: `text_sentiment_analysis` - Process text
5. **Benchmarking**: `performance_benchmark` - Test performance

### Task Type Icons

- 🔢 COMPUTATION
- 📊 DATA_ANALYSIS
- 📁 FILE_PROCESSING
- 🖼️ IMAGE_PROCESSING
- 🎬 VIDEO_PLAYBACK
- 🖥️ SYSTEM_MONITORING
- 🌐 NETWORK_DIAGNOSTICS
- 🕸️ WEB_SCRAPING
- 📝 TEXT_PROCESSING
- 🔐 ENCRYPTION
- 🤖 MACHINE_LEARNING
- 🌐 API_REQUEST
- ⚡ BENCHMARK
- 💾 BACKUP
- 🗜️ COMPRESSION
- 💾 DATABASE_QUERY
- ⚙️ CUSTOM

---

## 📚 Additional Resources

- **VIDEO_STREAMING_GUIDE.md** - Video playback details
- **ENHANCEMENT_SUMMARY.md** - Feature overview
- **README.md** - General documentation

---

**Last Updated**: December 15, 2025  
**Version**: 2.0  
**Total Task Types**: 17  
**Total Templates**: 31+
