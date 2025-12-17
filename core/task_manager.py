"""
Task Manager - Handles task distribution and execution
"""
import json
import time
import uuid
import threading
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

class TaskType(Enum):
    CUSTOM_TASK = "Custom Task"
    COMPUTATION = "Computation"
    IMAGE_PROCESSING = "Image Processing"
    DATA_ANALYSIS = "Data Analysis"
    VIDEO_PLAYBACK = "Video Playback"
    SYSTEM_CHECK = "System Check"
    NETWORK_TEST = "Network Test"
    TEXT_ANALYSIS = "Text Analysis"
    MACHINE_LEARNING = "Machine Learning"
    API_REQUEST = "API Request"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    id: str
    type: TaskType
    code: str
    data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    worker_id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress: int = 0
    output: Optional[str] = None  # Full output including stdout/stderr
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type.value,
            'code': self.code,
            'data': self.data,
            'status': self.status.value,
            'worker_id': self.worker_id,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'progress': self.progress  # <-- NEW
        }
    
    @classmethod
    def from_dict(cls, data):
        task = cls(
            id=data['id'],
            type=TaskType(data['type']),
            code=data['code'],
            data=data['data'],
            status=TaskStatus(data['status']),
            worker_id=data.get('worker_id'),
            result=data.get('result'),
            error=data.get('error'),
            created_at=data.get('created_at'),
            started_at=data.get('started_at'),
            completed_at=data.get('completed_at')
        )
        return task

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[str] = []
        self.lock = threading.Lock()
    
    # ── Task lifecycle helpers ──
    
    def create_task(self, task_type: TaskType, code: str, data: Dict[str, Any]) -> str:
        """Create a new task and add it to the queue"""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            type=task_type,
            code=code,
            data=data
        )
        
        with self.lock:
            self.tasks[task_id] = task
            self.task_queue.append(task_id)
        
        return task_id
    
    def get_next_task(self) -> Optional[Task]:
        """Get the next pending task from the queue"""
        with self.lock:
            for task_id in self.task_queue:
                task = self.tasks[task_id]
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.RUNNING
                    task.started_at = time.time()
                    return task
        return None
    
    def complete_task(self, task_id: str, result: Any = None, error: str = None):
        """Mark a task as completed or failed"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.completed_at = time.time()
                if error:
                    task.status = TaskStatus.FAILED
                    task.error = error
                else:
                    task.status = TaskStatus.COMPLETED
                    task.result = result
    
    def assign_task_to_worker(self, task_id: str, worker_id: str):
        """Assign a task to a specific worker"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].worker_id = worker_id
                if self.tasks[task_id].status == TaskStatus.PENDING:
                    self.tasks[task_id].status = TaskStatus.RUNNING
                    self.tasks[task_id].started_at = time.time()
    
    def update_task(self, task_id: str, worker_id: str, result_payload: Dict[str, Any]):
        """Update a task with result information from a worker"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return
            
            task.worker_id = worker_id
            task.completed_at = time.time()
            success = result_payload.get('success', True)
            task.result = result_payload.get('result')
            task.error = result_payload.get('error')
            task.progress = 100 if success else task.progress
            task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
    
            
            # Store full output
            output_parts = []
            if result_payload.get('stdout'):
                output_parts.append(f"STDOUT:\n{result_payload['stdout']}")
            if result_payload.get('stderr'):
                output_parts.append(f"STDERR:\n{result_payload['stderr']}")
            if result_payload.get('result') is not None:
                result_val = result_payload.get('result')
                if isinstance(result_val, dict):
                    output_parts.append(f"RESULT:\n{json.dumps(result_val, indent=2)}")
                else:
                    output_parts.append(f"RESULT:\n{result_val}")
            if result_payload.get('error'):
                output_parts.append(f"ERROR:\n{result_payload['error']}")
            
            task.output = "\n\n".join(output_parts) if output_parts else None
    
    def update_task_progress(self, task_id: str, progress: int):
        """Update progress for a specific task"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return
            task.progress = max(0, min(100, int(progress)))

    def requeue_tasks_for_worker(self, worker_id: str):
        """Reset tasks that were assigned to a worker back to pending so they can be reassigned.

        This is called when a worker disconnects unexpectedly.
        """
        with self.lock:
            for task in self.tasks.values():
                if task.worker_id == worker_id and task.status in (TaskStatus.RUNNING, TaskStatus.PENDING):
                    task.worker_id = None
                    task.status = TaskStatus.PENDING
                    task.started_at = None
                    task.progress = 0
                    # Ensure task is in the queue for scheduling
                    if task.id not in self.task_queue:
                        self.task_queue.append(task.id)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by its ID"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks"""
        return list(self.tasks.values())
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks by their status"""
        return [task for task in self.tasks.values() if task.status == status]
    
    def clear_tasks(self, status: Optional[TaskStatus] = None):
        """Remove tasks entirely or by status"""
        with self.lock:
            if status is None:
                self.tasks.clear()
                self.task_queue.clear()
                return
            
            to_remove = [task_id for task_id, task in self.tasks.items() if task.status == status]
            for task_id in to_remove:
                self.tasks.pop(task_id, None)
                if task_id in self.task_queue:
                    self.task_queue.remove(task_id)

# Predefined task templates
TASK_TEMPLATES = {
    "hello_world": {
        "type": TaskType.COMPUTATION,
        "name": "Hello World Test",
        "description": "Simple test task to verify output display",
        "code": """
# This is a simple test task
print("Hello from Worker!")
print("Task is executing...")

# Get the name from data
name = data.get('name', 'World')
message = f"Hello, {name}!"

print(f"Generated message: {message}")

# Set the result
result = {
    'message': message,
    'length': len(message),
    'uppercase': message.upper(),
    'status': 'success'
}

print("Task completed successfully!")
""",
        "sample_data": {"name": "WinLink User"}
    },
    
    "fibonacci": {
        "type": TaskType.COMPUTATION,
        "name": "Fibonacci Series",
        "description": "Generate Fibonacci series up to n terms and calculate the nth number",
        "code": """
def fibonacci_series(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    series = [0, 1]
    for i in range(2, n):
        series.append(series[i-1] + series[i-2])
    return series

def fibonacci_nth(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

n = data.get('n', 10)
series = fibonacci_series(n)
nth_value = fibonacci_nth(n)

result = {
    'series': series,
    'nth_number': nth_value,
    'count': len(series),
    'sum': sum(series)
}
""",
        "sample_data": {"n": 10}
    },
    
    "prime_check": {
        "type": TaskType.COMPUTATION,
        "name": "Prime Number Check",
        "description": "Check if a number is prime",
        "code": """
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

result = is_prime(data['number'])
""",
        "sample_data": {"number": 982451653}
    },
    
    "factorial": {
        "type": TaskType.COMPUTATION,
        "name": "Factorial Calculation",
        "description": "Calculate factorial of a number n (n!)",
        "code": """
def factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

n = data.get('n', 10)
fact = factorial(n)

result = {
    'number': n,
    'factorial': fact,
    'formula': f"{n}!"
}
""",
        "sample_data": {"n": 10}
    },
    
    "matrix_multiply": {
        "type": TaskType.COMPUTATION,
        "name": "Matrix Multiplication",
        "description": "Multiply two matrices",
        "code": """
def matrix_multiply(A, B):
    rows_A, cols_A = len(A), len(A[0])
    rows_B, cols_B = len(B), len(B[0])
    
    if cols_A != rows_B:
        raise ValueError("Cannot multiply matrices")
    
    result = [[0 for _ in range(cols_B)] for _ in range(rows_A)]
    
    for i in range(rows_A):
        for j in range(cols_B):
            for k in range(cols_A):
                result[i][j] += A[i][k] * B[k][j]
    
    return result

result = matrix_multiply(data['matrix_a'], data['matrix_b'])
""",
        "sample_data": {
            "matrix_a": [[1, 2], [3, 4]],
            "matrix_b": [[5, 6], [7, 8]]
        }
    },
    
    "data_processing": {
        "type": TaskType.DATA_ANALYSIS,
        "name": "Data Processing",
        "description": "Process and analyze numerical data",
        "code": """
import statistics

def analyze_data(numbers):
    return {
        'count': len(numbers),
        'sum': sum(numbers),
        'mean': statistics.mean(numbers),
        'median': statistics.median(numbers),
        'std_dev': statistics.stdev(numbers) if len(numbers) > 1 else 0,
        'min': min(numbers),
        'max': max(numbers)
    }

result = analyze_data(data['numbers'])
""",
        "sample_data": {"numbers": list(range(1, 10001))}
    },
    
    
    
    "image_stats": {
        "type": TaskType.IMAGE_PROCESSING,
        "name": "Image Statistics",
        "description": "Calculate statistics from image pixel data",
        "code": """
def analyze_image_data(pixels):
    if not pixels or not pixels[0]:
        return {'error': 'Invalid image data'}
    
    height = len(pixels)
    width = len(pixels[0])
    total_pixels = height * width
    
    # Flatten pixel values
    all_values = []
    for row in pixels:
        for pixel in row:
            if isinstance(pixel, (list, tuple)):
                all_values.extend(pixel)
            else:
                all_values.append(pixel)
    
    if not all_values:
        return {'error': 'No pixel data'}
    
    return {
        'width': width,
        'height': height,
        'total_pixels': total_pixels,
        'min_value': min(all_values),
        'max_value': max(all_values),
        'avg_value': sum(all_values) / len(all_values),
        'total_values': len(all_values)
    }

result = analyze_image_data(data['pixels'])
""",
        "sample_data": {
            "pixels": [
                [[255, 0, 0], [0, 255, 0], [0, 0, 255]],
                [[128, 128, 128], [200, 200, 200], [50, 50, 50]]
            ]
        }
    },
    
    "color_histogram": {
        "type": TaskType.IMAGE_PROCESSING,
        "name": "Color Histogram",
        "description": "Generate color histogram from image data",
        "code": """
def generate_histogram(pixels):
    histogram = {}
    pixel_count = 0
    
    for row in pixels:
        for pixel in row:
            if isinstance(pixel, (list, tuple)) and len(pixel) >= 3:
                # RGB color
                r, g, b = pixel[0], pixel[1], pixel[2]
                color_key = f"RGB({r},{g},{b})"
                histogram[color_key] = histogram.get(color_key, 0) + 1
                pixel_count += 1
            elif isinstance(pixel, (int, float)):
                # Grayscale
                histogram[pixel] = histogram.get(pixel, 0) + 1
                pixel_count += 1
    
    # Convert to percentages
    histogram_percent = {k: (v / pixel_count * 100) if pixel_count > 0 else 0 
                         for k, v in histogram.items()}
    
    return {
        'total_pixels': pixel_count,
        'unique_colors': len(histogram),
        'histogram': histogram,
        'histogram_percent': histogram_percent
    }

result = generate_histogram(data['pixels'])
""",
        "sample_data": {
            "pixels": [
                [[255, 0, 0], [0, 255, 0], [0, 0, 255]],
                [[255, 0, 0], [0, 255, 0], [128, 128, 128]]
            ]
        }
    },
    
    "video_playback": {
        "type": TaskType.VIDEO_PLAYBACK,
        "name": "Stream Video from URL",
        "description": "Play video from internet URL in a new window",
        "code": """
# This task will be handled specially by the worker UI
# The video URL will be passed in the data
video_url = data.get('video_url', '')
title = data.get('title', 'Video Player')

if not video_url:
    result = {'error': 'No video URL provided'}
else:
    result = {
        'video_url': video_url,
        'title': title,
        'action': 'play_video',
        'status': 'playing'
    }
""",
        "sample_data": {
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Sample Video"
        }
    },
    
    "system_health_check": {
        "type": TaskType.SYSTEM_CHECK,
        "name": "System Health Check",
        "description": "Comprehensive system health monitoring including CPU, memory, disk, and network",
        "code": """
import psutil
import platform
import datetime

def get_system_health():
    health = {
        'timestamp': datetime.datetime.now().isoformat(),
        'platform': {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        },
        'cpu': {
            'physical_cores': psutil.cpu_count(logical=False),
            'logical_cores': psutil.cpu_count(logical=True),
            'usage_percent': psutil.cpu_percent(interval=1),
            'frequency_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else 0
        },
        'memory': {
            'total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
            'used_gb': round(psutil.virtual_memory().used / (1024**3), 2),
            'percent': psutil.virtual_memory().percent
        },
        'disk': {
            'total_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
            'used_gb': round(psutil.disk_usage('/').used / (1024**3), 2),
            'free_gb': round(psutil.disk_usage('/').free / (1024**3), 2),
            'percent': psutil.disk_usage('/').percent
        },
        'network': {
            'bytes_sent': psutil.net_io_counters().bytes_sent,
            'bytes_recv': psutil.net_io_counters().bytes_recv,
            'packets_sent': psutil.net_io_counters().packets_sent,
            'packets_recv': psutil.net_io_counters().packets_recv
        }
    }
    
    # Determine overall health status
    issues = []
    if health['cpu']['usage_percent'] > 80:
        issues.append('High CPU usage')
    if health['memory']['percent'] > 85:
        issues.append('High memory usage')
    if health['disk']['percent'] > 90:
        issues.append('Low disk space')
    
    health['status'] = 'HEALTHY' if not issues else 'WARNING'
    health['issues'] = issues
    
    return health

result = get_system_health()
""",
        "sample_data": {}
    },
    
    "network_ping_test": {
        "type": TaskType.NETWORK_TEST,
        "name": "Network Ping Test",
        "description": "Test network connectivity and measure latency to multiple hosts",
        "code": """
import subprocess
import platform
import time

def ping_host(host, count=4):
    # Determine ping command based on OS
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    
    try:
        # Execute ping command
        cmd = ['ping', param, str(count), host]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Parse output for basic stats
        success = output.returncode == 0
        output_text = output.stdout
        
        # Try to extract average time (this is OS-dependent)
        avg_time = None
        if 'Average' in output_text:
            # Windows format
            parts = output_text.split('Average = ')
            if len(parts) > 1:
                avg_time = parts[1].split('ms')[0].strip()
        elif 'avg' in output_text:
            # Linux format
            parts = output_text.split('/')
            if len(parts) >= 5:
                avg_time = parts[4].strip()
        
        return {
            'host': host,
            'reachable': success,
            'average_ms': avg_time,
            'output_preview': output_text[:200]
        }
    except Exception as e:
        return {
            'host': host,
            'reachable': False,
            'error': str(e)
        }

hosts = data.get('hosts', ['8.8.8.8', 'google.com', '1.1.1.1'])
results = {}

for host in hosts:
    results[host] = ping_host(host, count=data.get('ping_count', 4))
    time.sleep(0.5)  # Small delay between pings

result = {
    'tested_hosts': len(hosts),
    'reachable_hosts': sum(1 for r in results.values() if r.get('reachable')),
    'results': results
}
""",
        "sample_data": {
            "hosts": ["8.8.8.8", "google.com", "1.1.1.1"],
            "ping_count": 4
        }
    },
    
    "text_sentiment_analysis": {
        "type": TaskType.TEXT_ANALYSIS,
        "name": "Text Sentiment Analysis",
        "description": "Analyze sentiment and extract key metrics from text",
        "code": """
import re
from collections import Counter

def analyze_sentiment(text):
    # Simple sentiment word lists
    positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 
                     'love', 'best', 'perfect', 'happy', 'beautiful', 'awesome'}
    negative_words = {'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 
                     'poor', 'sad', 'disappointing', 'wrong', 'failed', 'error'}
    
    # Convert to lowercase and split into words
    words = re.findall(r'\\b\\w+\\b', text.lower())
    
    # Count sentiments
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)
    
    # Calculate sentiment score (-1 to 1)
    total_sentiment_words = positive_count + negative_count
    if total_sentiment_words > 0:
        sentiment_score = (positive_count - negative_count) / total_sentiment_words
    else:
        sentiment_score = 0
    
    # Determine sentiment
    if sentiment_score > 0.2:
        sentiment = 'POSITIVE'
    elif sentiment_score < -0.2:
        sentiment = 'NEGATIVE'
    else:
        sentiment = 'NEUTRAL'
    
    # Additional text analysis
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    word_freq = Counter(words)
    
    return {
        'sentiment': sentiment,
        'sentiment_score': round(sentiment_score, 3),
        'positive_words_count': positive_count,
        'negative_words_count': negative_count,
        'total_words': len(words),
        'total_sentences': len(sentences),
        'avg_words_per_sentence': len(words) / len(sentences) if sentences else 0,
        'most_common_words': dict(word_freq.most_common(10)),
        'text_preview': text[:100] + '...' if len(text) > 100 else text
    }

text = data.get('text', '')
result = analyze_sentiment(text)
""",
        "sample_data": {
            "text": "This is a great product! I love it. The quality is excellent and the service was amazing. Highly recommended!"
        }
    },
    
    "base64_encoder": {
        "type": TaskType.CUSTOM_TASK,
        "name": "Base64 Encode/Decode",
        "description": "Encode or decode text using Base64",
        "code": """
import base64

operation = data.get('operation', 'encode')
text = data.get('text', '')

if operation == 'encode':
    # Encode to Base64
    encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    result = {
        'operation': 'encode',
        'original_text': text,
        'encoded_text': encoded,
        'original_length': len(text),
        'encoded_length': len(encoded)
    }
elif operation == 'decode':
    # Decode from Base64
    try:
        decoded = base64.b64decode(text.encode('utf-8')).decode('utf-8')
        result = {
            'operation': 'decode',
            'encoded_text': text,
            'decoded_text': decoded,
            'success': True
        }
    except Exception as e:
        result = {
            'operation': 'decode',
            'success': False,
            'error': str(e)
        }
else:
    result = {'error': 'Invalid operation. Use "encode" or "decode".'}
""",
        "sample_data": {
            "operation": "encode",
            "text": "Hello, World!"
        }
    },
    
    "hash_generator": {
        "type": TaskType.CUSTOM_TASK,
        "name": "Generate File Hashes",
        "description": "Generate multiple hash values (MD5, SHA1, SHA256) for data",
        "code": """
import hashlib

def generate_hashes(data_str):
    data_bytes = data_str.encode('utf-8')
    
    hashes = {
        'md5': hashlib.md5(data_bytes).hexdigest(),
        'sha1': hashlib.sha1(data_bytes).hexdigest(),
        'sha256': hashlib.sha256(data_bytes).hexdigest(),
        'sha512': hashlib.sha512(data_bytes).hexdigest()
    }
    
    return hashes

input_data = data.get('data', 'Hello, World!')

result = {
    'input_data': input_data,
    'input_length': len(input_data),
    'hashes': generate_hashes(input_data)
}
""",
        "sample_data": {
            "data": "Hello, World!"
        }
    },
    
    "simple_ml_prediction": {
        "type": TaskType.MACHINE_LEARNING,
        "name": "Simple Linear Regression",
        "description": "Train a simple linear regression model and make predictions",
        "code": """
def simple_linear_regression(X, y):
    n = len(X)
    
    # Calculate means
    mean_x = sum(X) / n
    mean_y = sum(y) / n
    
    # Calculate slope (m) and intercept (b)
    numerator = sum((X[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((X[i] - mean_x) ** 2 for i in range(n))
    
    m = numerator / denominator if denominator != 0 else 0
    b = mean_y - m * mean_x
    
    return m, b

def predict(X, m, b):
    return [m * x + b for x in X]

# Training data
X_train = data.get('X_train', [1, 2, 3, 4, 5])
y_train = data.get('y_train', [2, 4, 6, 8, 10])

# Train model
m, b = simple_linear_regression(X_train, y_train)

# Make predictions on test data
X_test = data.get('X_test', [6, 7, 8])
predictions = predict(X_test, m, b)

# Calculate training accuracy (R-squared)
y_pred_train = predict(X_train, m, b)
ss_res = sum((y_train[i] - y_pred_train[i]) ** 2 for i in range(len(y_train)))
ss_tot = sum((y_train[i] - sum(y_train)/len(y_train)) ** 2 for i in range(len(y_train)))
r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

result = {
    'model': {
        'slope': round(m, 4),
        'intercept': round(b, 4),
        'equation': f'y = {round(m, 4)}x + {round(b, 4)}'
    },
    'training': {
        'samples': len(X_train),
        'r_squared': round(r_squared, 4)
    },
    'predictions': {
        'X_test': X_test,
        'y_predicted': [round(p, 2) for p in predictions]
    }
}
""",
        "sample_data": {
            "X_train": [1, 2, 3, 4, 5],
            "y_train": [2, 4, 6, 8, 10],
            "X_test": [6, 7, 8]
        }
    },
    
    "json_validator": {
        "type": TaskType.DATA_ANALYSIS,
        "name": "JSON Validation & Analysis",
        "description": "Validate JSON structure and analyze its contents",
        "code": """
import json

def analyze_json(json_str):
    try:
        # Parse JSON
        data = json.loads(json_str)
        
        # Analyze structure
        def count_elements(obj, depth=0):
            counts = {
                'objects': 0,
                'arrays': 0,
                'strings': 0,
                'numbers': 0,
                'booleans': 0,
                'nulls': 0,
                'max_depth': depth
            }
            
            if isinstance(obj, dict):
                counts['objects'] += 1
                for value in obj.values():
                    sub_counts = count_elements(value, depth + 1)
                    for key in counts:
                        if key == 'max_depth':
                            counts[key] = max(counts[key], sub_counts[key])
                        else:
                            counts[key] += sub_counts[key]
            elif isinstance(obj, list):
                counts['arrays'] += 1
                for item in obj:
                    sub_counts = count_elements(item, depth + 1)
                    for key in counts:
                        if key == 'max_depth':
                            counts[key] = max(counts[key], sub_counts[key])
                        else:
                            counts[key] += sub_counts[key]
            elif isinstance(obj, str):
                counts['strings'] += 1
            elif isinstance(obj, (int, float)):
                counts['numbers'] += 1
            elif isinstance(obj, bool):
                counts['booleans'] += 1
            elif obj is None:
                counts['nulls'] += 1
            
            return counts
        
        stats = count_elements(data)
        
        return {
            'valid': True,
            'size_bytes': len(json_str),
            'size_kb': round(len(json_str) / 1024, 2),
            'structure': stats,
            'pretty_printed': json.dumps(data, indent=2)[:500]
        }
    except json.JSONDecodeError as e:
        return {
            'valid': False,
            'error': str(e),
            'error_line': e.lineno if hasattr(e, 'lineno') else None,
            'error_column': e.colno if hasattr(e, 'colno') else None
        }

json_string = data.get('json_string', '{}')
result = analyze_json(json_string)
""",
        "sample_data": {
            "json_string": '{"name": "John", "age": 30, "hobbies": ["reading", "gaming"], "active": true}'
        }
    },
    
    "api_weather_fetch": {
        "type": TaskType.API_REQUEST,
        "name": "Fetch Weather Data (Mock)",
        "description": "Simulate fetching weather data from an API",
        "code": """
import random
import datetime

def mock_weather_api(city):
    # Simulate API response with mock data
    weather_conditions = ['Sunny', 'Cloudy', 'Rainy', 'Partly Cloudy', 'Stormy', 'Foggy']
    
    temperature = random.randint(-10, 40)
    condition = random.choice(weather_conditions)
    humidity = random.randint(30, 90)
    wind_speed = random.randint(0, 50)
    
    return {
        'city': city,
        'temperature_celsius': temperature,
        'temperature_fahrenheit': round(temperature * 9/5 + 32, 1),
        'condition': condition,
        'humidity_percent': humidity,
        'wind_speed_kmh': wind_speed,
        'timestamp': datetime.datetime.now().isoformat(),
        'feels_like': temperature - 2 if wind_speed > 20 else temperature,
        'uv_index': random.randint(1, 11),
        'note': 'This is mock data for demonstration purposes'
    }

city = data.get('city', 'New York')
result = mock_weather_api(city)
""",
        "sample_data": {
            "city": "New York"
        }
    },
    
    "performance_benchmark": {
        "type": TaskType.CUSTOM_TASK,
        "name": "CPU Performance Benchmark",
        "description": "Run various performance benchmarks to test CPU speed",
        "code": """
import time
import math

def benchmark_integer_operations(iterations=1000000):
    start = time.time()
    total = 0
    for i in range(iterations):
        total += i * 2
    elapsed = time.time() - start
    return {
        'test': 'Integer Operations',
        'iterations': iterations,
        'time_seconds': round(elapsed, 4),
        'operations_per_second': round(iterations / elapsed, 0)
    }

def benchmark_floating_point(iterations=1000000):
    start = time.time()
    total = 0.0
    for i in range(iterations):
        total += math.sqrt(i) * 1.5
    elapsed = time.time() - start
    return {
        'test': 'Floating Point Operations',
        'iterations': iterations,
        'time_seconds': round(elapsed, 4),
        'operations_per_second': round(iterations / elapsed, 0)
    }

def benchmark_string_operations(iterations=100000):
    start = time.time()
    result = ""
    for i in range(iterations):
        result = f"String_{i}"
    elapsed = time.time() - start
    return {
        'test': 'String Operations',
        'iterations': iterations,
        'time_seconds': round(elapsed, 4),
        'operations_per_second': round(iterations / elapsed, 0)
    }

def benchmark_list_operations(size=100000):
    start = time.time()
    test_list = list(range(size))
    test_list.sort(reverse=True)
    test_list.reverse()
    elapsed = time.time() - start
    return {
        'test': 'List Operations',
        'list_size': size,
        'time_seconds': round(elapsed, 4),
        'operations_per_second': round(size / elapsed, 0)
    }

iterations = data.get('iterations', 100000)

benchmarks = [
    benchmark_integer_operations(iterations),
    benchmark_floating_point(iterations),
    benchmark_string_operations(iterations // 10),
    benchmark_list_operations(iterations // 10)
]

total_time = sum(b['time_seconds'] for b in benchmarks)

result = {
    'total_time_seconds': round(total_time, 4),
    'benchmarks': benchmarks,
    'system_performance_score': round(1000000 / total_time, 0)
}
""",
        "sample_data": {
            "iterations": 100000
        }
    },
    
    
}
