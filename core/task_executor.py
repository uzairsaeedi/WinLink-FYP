"""
Task Executor - Executes tasks safely in a controlled environment
"""
import io
import time
import traceback
import threading
from typing import Callable, Optional

import psutil
from contextlib import redirect_stdout, redirect_stderr


class TaskExecutor:
    def __init__(self):
        self.max_execution_time = 300  # 5 minutes max
        self.max_memory_mb = 512  # 512MB max memory per task
        self.max_cpu_percent = 100  # 100% CPU max (no limit by default)
    
    def set_resource_limits(self, cpu_percent: int = 100, memory_mb: int = 512):
        """Set CPU and memory limits for task execution"""
        self.max_cpu_percent = max(10, min(100, cpu_percent))  # Clamp between 10-100
        self.max_memory_mb = max(256, min(8192, memory_mb))  # Clamp between 256-8192
    
    def execute_task(
        self,
        task_code: str,
        task_data: dict,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> dict:
        """
        Execute a task safely with resource monitoring
        Returns: {
            'success': bool,
            'result': any,
            'error': str,
            'execution_time': float,
            'memory_used': float
        }
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        def report_progress(value: int):
            if not progress_callback:
                return
            try:
                clamped = max(0, min(100, int(value)))
                progress_callback(clamped)
            except Exception:
                pass
        
        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Create custom print function that writes to stdout_capture
        def custom_print(*args, **kwargs):
            """Custom print function that writes to captured stdout"""
            import builtins
            kwargs['file'] = stdout_capture
            builtins.print(*args, **kwargs)
        
        # Create isolated namespace for task execution
        task_namespace = {
            'data': task_data,
            'result': None,
            'report_progress': report_progress,
            '__builtins__': {
                # Safe built-ins only
                'len': len, 'range': range, 'enumerate': enumerate,
                'zip': zip, 'map': map, 'filter': filter,
                'sum': sum, 'min': min, 'max': max, 'abs': abs,
                'round': round, 'sorted': sorted, 'reversed': reversed,
                'int': int, 'float': float, 'str': str, 'bool': bool,
                'list': list, 'dict': dict, 'set': set, 'tuple': tuple,
                'print': custom_print, 'type': type, 'isinstance': isinstance,
                'ValueError': ValueError, 'TypeError': TypeError,
                'IndexError': IndexError, 'KeyError': KeyError
            }
        }
        
        # Allow safe imports
        safe_modules = ['math', 'statistics', 'random', 'datetime', 'json', 're']
        for module in safe_modules:
            try:
                task_namespace[module] = __import__(module)
            except ImportError:
                pass
        
        try:
            # Get current process for resource limiting
            import os
            current_process = psutil.Process(os.getpid())
            
            # Set process priority based on CPU limit
            if self.max_cpu_percent <= 50:
                # Low CPU limit - use BELOW_NORMAL priority
                try:
                    current_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                except:
                    pass
            elif self.max_cpu_percent <= 75:
                # Medium CPU limit - use NORMAL priority  
                try:
                    current_process.nice(psutil.NORMAL_PRIORITY_CLASS)
                except:
                    pass
            # else: HIGH_PRIORITY_CLASS (default)
            
            # Start CPU throttling thread if limit is set
            stop_throttle = threading.Event()
            throttle_thread = None
            memory_exceeded = [False]  # Use list to allow modification in nested function
            
            if self.max_cpu_percent < 100 or self.max_memory_mb < 8192:
                def resource_monitor():
                    \"\"\"Monitor and throttle CPU and memory usage\"\"\"
                    while not stop_throttle.is_set():
                        try:
                            # Monitor CPU usage
                            if self.max_cpu_percent < 100:
                                cpu_usage = current_process.cpu_percent(interval=0.1)
                                
                                # If over limit, sleep to reduce CPU usage
                                if cpu_usage > self.max_cpu_percent:
                                    overage = (cpu_usage - self.max_cpu_percent) / 100
                                    time.sleep(0.01 * overage)
                            
                            # Monitor memory usage
                            if self.max_memory_mb < 8192:
                                memory_mb = self._get_memory_usage()
                                if memory_mb > self.max_memory_mb:
                                    memory_exceeded[0] = True
                                    stop_throttle.set()
                                    break
                            
                            time.sleep(0.05)  # Check every 50ms
                        except:
                            break
                
                throttle_thread = threading.Thread(target=resource_monitor, daemon=True)
                throttle_thread.start()
            
            # Execute the task
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(task_code, task_namespace)
            
            # Stop resource monitoring
            if throttle_thread:
                stop_throttle.set()
                throttle_thread.join(timeout=1)
            
            # Check if memory limit was exceeded
            if memory_exceeded[0]:
                return {
                    'success': False,
                    'result': None,
                    'error': f'Task exceeded memory limit of {self.max_memory_mb} MB',
                    'execution_time': time.time() - start_time,
                    'memory_used': self._get_memory_usage() - start_memory,
                    'stdout': stdout_capture.getvalue(),
                    'stderr': stderr_capture.getvalue()
                }
            
            # Restore normal priority
            try:
                current_process.nice(psutil.NORMAL_PRIORITY_CLASS)
            except:
                pass
            
            # Check if execution had an error
            stderr_content = stderr_capture.getvalue()
            result_value = task_namespace.get('result')
            
            # If there's stderr but we have a result, it might just be warnings
            if stderr_content and result_value is None:
                return {
                    'success': False,
                    'result': None,
                    'error': stderr_content,
                    'execution_time': time.time() - start_time,
                    'memory_used': self._get_memory_usage() - start_memory,
                    'stdout': stdout_capture.getvalue(),
                    'stderr': stderr_capture.getvalue()
                }
            
            # Task executed successfully
            return {
                'success': True,
                'result': result_value,
                'error': None,
                'execution_time': time.time() - start_time,
                'memory_used': self._get_memory_usage() - start_memory,
                'stdout': stdout_capture.getvalue(),
                'stderr': stderr_capture.getvalue()
            }
            
        except Exception as e:
            return {
                'success': False,
                'result': None,
                'error': str(e),
                'execution_time': time.time() - start_time,
                'memory_used': self._get_memory_usage() - start_memory,
                'stdout': stdout_capture.getvalue(),
                'stderr': stderr_capture.getvalue()
            }
    
    def _execute_with_monitoring(self, code, namespace, stdout_capture, stderr_capture):
        """Execute code with I/O redirection"""
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, namespace)
        except Exception as e:
            stderr_capture.write(f"Execution Error: {str(e)}\n{traceback.format_exc()}")
    
    def _get_memory_usage(self):
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except Exception:
            return 0
    
    def get_system_resources(self):
        """Return snapshot of current system resources with capabilities"""
        try:
            import os
            import platform
            import socket
            
            battery = psutil.sensors_battery()
            mem = psutil.virtual_memory()
            
            # Get disk usage - handle Windows vs Unix
            if platform.system() == "Windows":
                # Use the system drive (typically C:\)
                disk_path = os.getenv("SystemDrive", "C:") + "\\"
            else:
                disk_path = "/"
            
            disk = psutil.disk_usage(disk_path)
            
            # Detect GPU capability
            has_gpu = False
            gpu_info = "No GPU detected"
            try:
                import subprocess
                result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0 and result.stdout.strip():
                    has_gpu = True
                    gpu_info = result.stdout.strip()
            except:
                pass
            
            # Get CPU info
            cpu_count = psutil.cpu_count(logical=False) or psutil.cpu_count()
            cpu_threads = psutil.cpu_count(logical=True)
            
            # Get hostname for geographic awareness
            hostname = socket.gethostname()
            
            resources = {
                "cpu_percent": psutil.cpu_percent(interval=0.2),
                "memory_percent": mem.percent,
                "memory_total_mb": mem.total / (1024 * 1024),
                "memory_available_mb": mem.available / (1024 * 1024),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024 ** 3),
                "battery_percent": battery.percent if battery else None,
                "battery_plugged": battery.power_plugged if battery else None,
                # Capability detection
                "has_gpu": has_gpu,
                "gpu_info": gpu_info,
                "cpu_cores": cpu_count,
                "cpu_threads": cpu_threads,
                "hostname": hostname,
                "platform": platform.system(),
                "platform_version": platform.version(),
            }
            
            return resources
        except Exception as e:
            return {}
