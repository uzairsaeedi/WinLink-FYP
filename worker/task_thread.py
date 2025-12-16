"""
Background Task Execution Thread
Prevents UI freezing during long-running tasks
"""
import time
import json
import socket
from PyQt5.QtCore import QThread, pyqtSignal


class TaskExecutionThread(QThread):
    """
    QThread for executing tasks in background without blocking UI
    """
    # Signals for thread-safe communication with UI
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(str, int)  # task_id, progress
    state_update_signal = pyqtSignal(str, dict)  # task_id, state_dict
    refresh_display_signal = pyqtSignal()
    task_complete_signal = pyqtSignal(str, dict, float, float)  # task_id, result, exec_time, memory_used
    
    def __init__(self, task_id, task_name, code, payload, task_executor, network, worker_ip):
        super().__init__()
        self.task_id = task_id
        self.task_name = task_name
        self.code = code
        self.payload = payload
        self.task_executor = task_executor
        self.network = network
        self.worker_ip = worker_ip
        self._is_running = True
    
    def run(self):
        """Execute task in background thread"""
        if not self._is_running:
            return
        
        # Small delay to allow UI to update
        time.sleep(0.1)
        
        start_time = time.time()
        start_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))
        
        # Update task state to executing
        self.state_update_signal.emit(self.task_id, {
            "status": "executing",
            "progress": 0,
            "started_at": start_time
        })
        
        # Log execution start
        self.log_signal.emit("─" * 60)
        self.log_signal.emit(f"▶️  TASK EXECUTION STARTED")
        self.log_signal.emit(f"   📋 Task: '{self.task_name}'")
        self.log_signal.emit(f"   🆔 ID: {self.task_id[:8]}...")
        self.log_signal.emit(f"   ⏰ Start Time: {start_time_str}")
        self.log_signal.emit(f"   🖥️  Worker: {socket.gethostname()} [{self.worker_ip}]")
        self.log_signal.emit(f"   ⚙️  Status: EXECUTING")
        self.log_signal.emit("─" * 60)
        
        self.refresh_display_signal.emit()
        self.progress_signal.emit(self.task_id, 0)
        
        # Progress callback with logging
        def progress_with_log(pct):
            if not self._is_running:
                return
            
            # Log at milestones
            if pct in [25, 50, 75, 100]:
                self.log_signal.emit(f"⏳ Task '{self.task_name}' [{self.task_id[:8]}...] progress: {pct}%")
            
            self.progress_signal.emit(self.task_id, pct)
            self.refresh_display_signal.emit()
        
        # Execute the task
        result = self.task_executor.execute_task(
            self.code,
            self.payload,
            progress_callback=progress_with_log
        )
        
        if not self._is_running:
            return
        
        # Determine final status
        status = "done" if result.get("success") else "failed"
        progress_final = 100 if result.get("success") else 99
        
        self.progress_signal.emit(self.task_id, progress_final)
        
        end_time = time.time()
        end_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
        execution_time = result.get("execution_time", end_time - start_time)
        memory_used = result.get("memory_used", 0)
        
        # Log completion
        if result.get("success"):
            self.log_signal.emit(f"✅ Task completed: '{self.task_name}' [ID: {self.task_id[:8]}...]")
            self.log_signal.emit(f"   ⏱️  Ended at: {end_time_str}")
            self.log_signal.emit(f"   ⏱️  Execution time: {execution_time:.2f}s")
            self.log_signal.emit(f"   💾 Memory used: {memory_used:.2f} MB")
            self.log_signal.emit(f"   ✓ Status: SUCCESS (100%)")
        else:
            error_msg = result.get("error", "Unknown error")
            self.log_signal.emit(f"❌ Task failed: '{self.task_name}' [ID: {self.task_id[:8]}...]")
            self.log_signal.emit(f"   ⏱️  Ended at: {end_time_str}")
            self.log_signal.emit(f"   ⏱️  Execution time: {execution_time:.2f}s")
            self.log_signal.emit(f"   💾 Memory used: {memory_used:.2f} MB")
            self.log_signal.emit(f"   ✗ Error: {error_msg[:100]}")
        
        self.log_signal.emit("─" * 60)
        
        # Build output text
        output_parts = []
        if result.get("stdout"):
            output_parts.append(f"STDOUT:\n{result['stdout']}")
        if result.get("stderr"):
            output_parts.append(f"STDERR:\n{result['stderr']}")
        
        result_val = result.get("result")
        if result_val is not None:
            try:
                if isinstance(result_val, dict):
                    output_parts.append(f"RESULT:\n{json.dumps(result_val, indent=2)}")
                elif isinstance(result_val, (list, tuple)):
                    output_parts.append(f"RESULT:\n{json.dumps(result_val, indent=2)}")
                elif isinstance(result_val, str):
                    if result_val:
                        output_parts.append(f"RESULT:\n{result_val}")
                    else:
                        output_parts.append(f"RESULT:\n(empty string)")
                elif isinstance(result_val, bool):
                    output_parts.append(f"RESULT:\n{result_val}")
                elif isinstance(result_val, (int, float)):
                    output_parts.append(f"RESULT:\n{result_val}")
                else:
                    output_parts.append(f"RESULT:\n{str(result_val)}")
            except Exception:
                output_parts.append(f"RESULT:\n{str(result_val)}")
        else:
            if result.get("success") and not result.get("error"):
                output_parts.append("RESULT:\n(Task completed but returned None)")
        
        if result.get("error"):
            output_parts.append(f"ERROR:\n{result['error']}")
        
        output_text = "\n\n".join(output_parts) if output_parts else "No output generated."
        
        # Send result to master (in background thread, won't block UI)
        result_payload = {
            "success": result.get("success"),
            "result": result.get("result"),
            "error": result.get("error"),
            "stdout": result.get("stdout"),
            "stderr": result.get("stderr"),
            "execution_time": result.get("execution_time"),
            "memory_used": memory_used
        }
        
        try:
            self.network.send_task_result(self.task_id, result_payload)
        except Exception as e:
            self.log_signal.emit(f"⚠️  Warning: Failed to send result to master: {str(e)}")
        
        # Update final task state
        self.state_update_signal.emit(self.task_id, {
            "status": status,
            "progress": progress_final,
            "completed_at": time.time(),
            "memory_used_mb": memory_used,
            "output": output_text
        })
        
        # Signal completion
        self.task_complete_signal.emit(self.task_id, result, execution_time, memory_used)
        self.refresh_display_signal.emit()
    
    def stop(self):
        """Stop the thread gracefully"""
        self._is_running = False
        self.quit()
