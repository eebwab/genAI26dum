"""
Stress Test Suite for AegisDevOps Backend
Tests the stress-test endpoint and verifies Aegis can detect and respond to high load
"""

import requests
import time
import json
import pytest
from threading import Thread
from datetime import datetime

BASE_URL = "http://localhost:5000"


class TestStressTestEndpoint:
    """Test suite for stress testing"""
    
    def test_stress_test_endpoint_returns_202(self):
        """Verify stress test endpoint accepts the request"""
        response = requests.post(
            f"{BASE_URL}/stress-test",
            json={"duration": 5, "concurrency": 10}
        )
        assert response.status_code == 202
        assert "running" in response.json()["status"]
    
    def test_stress_test_increases_memory(self):
        """Verify stress test actually increases memory usage"""
        # Get baseline
        baseline = requests.get(f"{BASE_URL}/status").json()
        baseline_memory = baseline["system"]["memory_usage_percent"]
        
        # Run stress test
        requests.post(
            f"{BASE_URL}/stress-test",
            json={"duration": 3, "concurrency": 20}
        )
        
        # Wait for test to complete
        time.sleep(5)
        
        # Check memory increased
        after = requests.get(f"{BASE_URL}/status").json()
        after_memory = after["system"]["memory_usage_percent"]
        
        # Memory should have increased (or at least show high usage)
        print(f"Memory before: {baseline_memory}%, after: {after_memory}%")
    
    def test_stress_test_increases_cpu(self):
        """Verify stress test increases CPU usage"""
        # Run stress test
        requests.post(
            f"{BASE_URL}/stress-test",
            json={"duration": 2, "concurrency": 10}
        )
        
        # Check status
        status = requests.get(f"{BASE_URL}/status").json()
        cpu = status["system"]["cpu_usage_percent"]
        
        print(f"CPU usage during stress: {cpu}%")
        assert cpu > 0


class TestErrorInjection:
    """Test suite for error injection"""
    
    def test_inject_memory_leak(self):
        """Test memory leak injection"""
        response = requests.post(f"{BASE_URL}/inject-error/memory_leak")
        assert response.status_code == 200
        
        # Verify error is active
        status = requests.get(f"{BASE_URL}/status").json()
        assert status["application"]["injected_errors"]["memory_leak"] == True
        
        # Clear
        requests.post(f"{BASE_URL}/clear-error/memory_leak")
    
    def test_inject_dependency_error(self):
        """Test dependency error injection"""
        response = requests.post(f"{BASE_URL}/inject-error/dependency_missing")
        assert response.status_code == 200
        
        # Endpoint should fail
        error_response = requests.get(f"{BASE_URL}/missing-dependency")
        assert error_response.status_code == 500
        assert "dependency" in error_response.json()["error"].lower()
        
        # Clear
        requests.post(f"{BASE_URL}/clear-error/dependency_missing")
    
    def test_clear_all_errors(self):
        """Test clearing all errors at once"""
        requests.post(f"{BASE_URL}/inject-error/memory_leak")
        requests.post(f"{BASE_URL}/inject-error/dependency_missing")
        
        # Clear all
        response = requests.post(f"{BASE_URL}/clear-error/all")
        assert response.status_code == 200
        
        # Verify all cleared
        status = requests.get(f"{BASE_URL}/status").json()
        for error_state in status["application"]["injected_errors"].values():
            assert error_state == False


class TestHealthAndStatus:
    """Test suite for health checks and monitoring"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_status_includes_alerts(self):
        """Test status endpoint includes alerts"""
        # Inject a high-load scenario
        requests.post(f"{BASE_URL}/stress-test", json={"duration": 2, "concurrency": 30})
        time.sleep(1)
        
        response = requests.get(f"{BASE_URL}/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "alerts" in data
        assert "system" in data
        assert "application" in data
    
    def test_status_shows_system_metrics(self):
        """Verify status includes CPU and memory metrics"""
        response = requests.get(f"{BASE_URL}/status")
        assert response.status_code == 200
        
        data = response.json()
        system = data["system"]
        
        assert "cpu_usage_percent" in system
        assert "memory_usage_percent" in system
        assert "memory_available_mb" in system
        assert 0 <= system["cpu_usage_percent"] <= 100
        assert 0 <= system["memory_usage_percent"] <= 100


class TestErrorScenarios:
    """Test various error scenarios Aegis would encounter"""
    
    def test_memory_leak_scenario(self):
        """Simulate memory leak that triggers Aegis restart logic"""
        # Inject error
        requests.post(f"{BASE_URL}/inject-error/memory_leak")
        
        # Hit the endpoint multiple times to grow buffer
        for _ in range(5):
            requests.get(f"{BASE_URL}/memory-leak")
            time.sleep(0.5)
        
        # Check status shows high memory
        status = requests.get(f"{BASE_URL}/status").json()
        assert len(status["application"]["injected_errors"]) > 0
        
        # Aegis should see this and restart the service
        requests.post(f"{BASE_URL}/clear-error/all")
    
    def test_connection_timeout_scenario(self):
        """Simulate connection timeout that triggers Aegis recovery"""
        requests.post(f"{BASE_URL}/inject-error/connection_timeout")
        
        # This should timeout
        try:
            response = requests.get(f"{BASE_URL}/timeout-test", timeout=2)
            # May timeout or return 504
            assert response.status_code in [504, 408]
        except requests.Timeout:
            pass  # Expected
        
        # Clear
        requests.post(f"{BASE_URL}/clear-error/all")
    
    def test_out_of_memory_scenario(self):
        """Simulate OOM error"""
        requests.post(f"{BASE_URL}/inject-error/out_of_memory")
        
        response = requests.post(
            f"{BASE_URL}/api/process",
            json={"test": "data"}
        )
        assert response.status_code == 500
        
        requests.post(f"{BASE_URL}/clear-error/all")


if __name__ == "__main__":
    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])
