"""
AegisDevOps Backend - Self-Healing DevOps Agent Test Backend
Demonstrates various failure modes that Aegis agents can fix
"""

import os
import time
import json
import logging
import random
import psutil
from datetime import datetime
from flask import Flask, jsonify, request
from threading import Thread

# ==========================================
# SETUP LOGGING
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==========================================
# GLOBAL STATE FOR ERRORS
# ==========================================
INJECTED_ERRORS = {
    "memory_leak": False,
    "dependency_missing": False,
    "out_of_memory": False,
    "connection_timeout": False
}

MEMORY_BUFFER = []  # Simulated memory leak


# ==========================================
# HEALTH CHECK
# ==========================================
@app.route('/health', methods=['GET'])
def health():
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }), 200


# ==========================================
# STRESS TEST ENDPOINT - THE MAIN DEMO
# ==========================================
@app.route('/stress-test', methods=['POST'])
def stress_test():
    """
    Triggers a stress test that intentionally causes high memory/CPU usage
    Aegis will detect this in logs and scale up ECS instances
    """
    duration = request.json.get('duration', 30) if request.json else 30
    concurrency = request.json.get('concurrency', 100) if request.json else 100
    
    logger.warning(f"[STRESS TEST] Starting: duration={duration}s, concurrency={concurrency}")
    
    # Simulate high load by spawning threads
    def high_load():
        start = time.time()
        count = 0
        while time.time() - start < duration:
            try:
                # CPU-intensive operation
                result = sum([i**2 for i in range(10000)])
                
                # Memory-intensive operation
                data = [random.random() for _ in range(10000)]
                MEMORY_BUFFER.append(data)
                
                count += 1
            except Exception as e:
                logger.error(f"Error in load simulation: {e}")
    
    # Run stress in background thread
    threads = []
    for i in range(min(concurrency, 50)):  # Cap at 50 threads for safety
        t = Thread(target=high_load, daemon=True)
        t.start()
        threads.append(t)
    
    # Log current resource usage
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event": "STRESS_TEST_STARTED",
        "cpu_usage": cpu_percent,
        "memory_usage_percent": memory_info.percent,
        "memory_available_mb": memory_info.available / (1024 * 1024),
        "duration_seconds": duration,
        "concurrency": concurrency,
        "severity": "HIGH" if cpu_percent > 80 or memory_info.percent > 80 else "MEDIUM"
    }
    
    logger.critical(json.dumps(log_entry))
    
    return jsonify({
        "message": "Stress test initiated",
        "initial_cpu": cpu_percent,
        "initial_memory_percent": memory_info.percent,
        "status": "running"
    }), 202


# ==========================================
# ERROR INJECTION ENDPOINTS (for Aegis testing)
# ==========================================
@app.route('/inject-error/<error_type>', methods=['POST'])
def inject_error(error_type):
    """Inject specific errors for testing Aegis responses"""
    if error_type not in INJECTED_ERRORS:
        return jsonify({"error": f"Unknown error type: {error_type}"}), 400
    
    INJECTED_ERRORS[error_type] = True
    logger.error(f"[INJECTED ERROR] {error_type.upper()} activated")
    
    return jsonify({
        "message": f"Error injected: {error_type}",
        "status": "active"
    }), 200


@app.route('/clear-error/<error_type>', methods=['POST'])
def clear_error(error_type):
    """Clear injected errors"""
    if error_type == 'all':
        for key in INJECTED_ERRORS:
            INJECTED_ERRORS[key] = False
        MEMORY_BUFFER.clear()
        logger.info("[CLEAR] All errors cleared")
    elif error_type in INJECTED_ERRORS:
        INJECTED_ERRORS[error_type] = False
        logger.info(f"[CLEAR] {error_type} cleared")
    else:
        return jsonify({"error": f"Unknown error type: {error_type}"}), 400
    
    return jsonify({"message": f"Error cleared: {error_type}"}), 200


# ==========================================
# MEMORY LEAK ERROR
# ==========================================
@app.route('/memory-leak', methods=['GET'])
def memory_leak_endpoint():
    """Endpoint that triggers on-demand memory leak (for testing)"""
    if INJECTED_ERRORS['memory_leak']:
        for _ in range(100):
            MEMORY_BUFFER.append([random.random() for _ in range(100000)])
        
        logger.warning(f"[MEMORY LEAK] Buffer size: {len(MEMORY_BUFFER)} items")
        return jsonify({"error": "Memory usage increased"}), 500
    
    return jsonify({"status": "ok"}), 200


# ==========================================
# DEPENDENCY ERROR
# ==========================================
@app.route('/missing-dependency', methods=['GET'])
def missing_dependency():
    """Endpoint that simulates missing dependency"""
    if INJECTED_ERRORS['dependency_missing']:
        try:
            import nonexistent_module
        except ImportError as e:
            logger.error(f"[DEPENDENCY ERROR] {str(e)}")
            return jsonify({
                "error": "Missing dependency: nonexistent_module",
                "message": "This requires rebuilding the Docker image with updated requirements.txt"
            }), 500
    
    return jsonify({"status": "ok"}), 200


# ==========================================
# CONNECTION TIMEOUT ERROR
# ==========================================
@app.route('/timeout-test', methods=['GET'])
def timeout_test():
    """Endpoint that simulates connection timeout"""
    if INJECTED_ERRORS['connection_timeout']:
        logger.warning("[TIMEOUT] Simulating connection timeout...")
        time.sleep(30)  # Simulate long-running operation
        return jsonify({"error": "Connection timeout"}), 504
    
    return jsonify({"status": "ok"}), 200


# ==========================================
# SYSTEM STATUS (for Aegis monitoring)
# ==========================================
@app.route('/status', methods=['GET'])
def status():
    """Return detailed system status"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        status_data = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory_info.percent,
                "memory_available_mb": memory_info.available / (1024 * 1024),
                "disk_usage_percent": disk_info.percent,
                "uptime_seconds": time.time()
            },
            "application": {
                "memory_buffer_size": len(MEMORY_BUFFER),
                "injected_errors": INJECTED_ERRORS,
                "version": "1.0.0"
            },
            "alerts": []
        }
        
        # Generate alerts
        if cpu_percent > 80:
            status_data["alerts"].append({
                "severity": "HIGH",
                "message": f"CPU usage critical: {cpu_percent}%",
                "recommendation": "Scale up ECS instances"
            })
        
        if memory_info.percent > 80:
            status_data["alerts"].append({
                "severity": "HIGH",
                "message": f"Memory usage critical: {memory_info.percent}%",
                "recommendation": "Restart service or scale ECS instances"
            })
        
        if any(INJECTED_ERRORS.values()):
            status_data["alerts"].append({
                "severity": "MEDIUM",
                "message": "Injected errors are active",
                "active_errors": [k for k, v in INJECTED_ERRORS.items() if v]
            })
        
        return jsonify(status_data), 200
    
    except Exception as e:
        logger.error(f"[STATUS ERROR] {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==========================================
# ERROR LOGGING (simulates various backend errors)
# ==========================================
@app.route('/api/process', methods=['POST'])
def process_request():
    """Generic endpoint that can fail in various ways"""
    try:
        data = request.json
        
        if INJECTED_ERRORS['connection_timeout']:
            logger.error("[CONNECTION ERROR] Database connection timeout")
            return jsonify({"error": "Database connection timeout"}), 504
        
        if INJECTED_ERRORS['out_of_memory']:
            logger.error("[OUT OF MEMORY] Cannot allocate memory")
            return jsonify({"error": "Out of memory"}), 500
        
        result = {"processed": True, "data": data}
        logger.info(f"Successfully processed request: {result}")
        return jsonify(result), 200
    
    except Exception as e:
        logger.exception(f"[PROCESS ERROR] {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Force output to stdout
    import sys
    print("DEBUG: App is starting...", flush=True) 
    
    port = int(os.getenv('PORT', 5000))
    
    try:
        logger.info(f"Starting AegisDevOps backend on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}", flush=True)
        sys.exit(1)
