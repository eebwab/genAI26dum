#!/usr/bin/env python3
"""
AegisDevOps Error CLI Simulator
A simple interactive command-line tool to trigger errors for Aegis agents.
"""

import requests
import time
import sys

BASE_URL = "http://localhost:5000"

def check_backend():
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        pass
    return False

def print_header(title):
    print("\n" + "=" * 60)
    print(f" 🔥 TRIGGERING: {title}")
    print("=" * 60)

def trigger_high_load():
    print_header("AWS AGENT SCENARIO: HIGH CPU/MEMORY LOAD")
    print("This will spike CPU and Memory, triggering the AWS Agent to scale ECS.")
    
    try:
        response = requests.post(
            f"{BASE_URL}/stress-test", 
            json={"duration": 15, "concurrency": 100},
            timeout=5
        )
        if response.status_code == 202:
            print("✅ High load initiated successfully.")
            print("Monitoring status for 10 seconds...")
            for i in range(5):
                time.sleep(2)
                try:
                    status = requests.get(f"{BASE_URL}/status").json()
                    cpu = status["system"]["cpu_usage_percent"]
                    mem = status["system"]["memory_usage_percent"]
                    print(f"  → CPU: {cpu}% | Memory: {mem}%")
                except:
                    pass
    except Exception as e:
        print(f"❌ Failed to trigger high load: {e}")

def trigger_dependency_error():
    print_header("GITHUB AGENT SCENARIO: DEPENDENCY ERROR")
    print("Injecting a missing module error. GitHub Agent should redockerize.")
    
    try:
        # Inject the error
        requests.post(f"{BASE_URL}/inject-error/dependency_missing")
        print("✅ Error injected.")
        
        # Trigger the failing endpoint
        print("Triggering failing endpoint...")
        response = requests.get(f"{BASE_URL}/missing-dependency")
        if response.status_code == 500:
            print(f"💥 Application Crashed: {response.json().get('error')}")
            print(f"📄 Log Output: [DEPENDENCY ERROR] No module named 'nonexistent_module'")
            print("🤖 Aegis Orchestrator should now route this to the GitHub Agent.")
    except Exception as e:
        print(f"❌ Failed: {e}")

def trigger_memory_leak():
    print_header("AWS AGENT SCENARIO: OOM / MEMORY LEAK")
    print("Inflating memory buffer rapidly. AWS agent should restart the container.")
    
    try:
        requests.post(f"{BASE_URL}/inject-error/memory_leak")
        print("✅ Error state active.")
        
        print("Triggering memory leak repeatedly...")
        for i in range(3):
            requests.get(f"{BASE_URL}/memory-leak")
            print(f"  Iteration {i+1}: Buffer filled with random data")
            
        status = requests.get(f"{BASE_URL}/status").json()
        print(f"💥 Status check shows Alert: Memory leak detected (Buffer size: {status['application']['memory_buffer_size']})")
        print("🤖 Aegis Orchestrator should route to AWS Agent for restart.")
    except Exception as e:
        print(f"❌ Failed: {e}")

def trigger_connection_timeout():
    print_header("AWS AGENT SCENARIO: DATABASE CONNECTION TIMEOUT")
    print("Simulating a hung database connection.")
    
    try:
        requests.post(f"{BASE_URL}/inject-error/connection_timeout")
        print("✅ Error state active.")
        
        print("Hitting API endpoint (expecting Gateway Timeout)...")
        response = requests.post(f"{BASE_URL}/api/process", json={"test": "data"})
        if response.status_code == 504:
            print(f"💥 API Failed: {response.json().get('error')}")
            print("🤖 Aegis Orchestrator should investigate connectivity.")
    except Exception as e:
        print(f"❌ Failed: {e}")

def clear_all_errors():
    print_header("RECOVERY: CLEARING ALL ERRORS")
    try:
        requests.post(f"{BASE_URL}/clear-error/all")
        print("✅ Backend restored to healthy state.")
    except:
        print("❌ Failed to clear errors.")

def main():
    print("""
    🛡️  AEGIS DEVOPS ERROR SIMULATOR 🛡️
    ======================================
    This CLI makes it easy to demonstrate your hackathon project.
    """)
    
    if not check_backend():
        print(f"❌ Backend not running! Please start 'python app.py' on port 5000 first.")
        sys.exit(1)
        
    while True:
        print("\nSelect a scenario to demonstrate to the Judges:")
        print("1) 📈 High Load Spike (Triggers AWS Agent Scaling)")
        print("2) 📦 Missing Dependency (Triggers GitHub Agent Redockerize)")
        print("3) 🩸 Memory Leak (Triggers AWS Agent Restart)")
        print("4) 🔌 Connection Timeout (Network failure)")
        print("5) 🧹 Clear all active errors")
        print("0) Exit")
        
        choice = input("\nEnter choice (0-5): ").strip()
        
        if choice == '1':
            trigger_high_load()
        elif choice == '2':
            trigger_dependency_error()
        elif choice == '3':
            trigger_memory_leak()
        elif choice == '4':
            trigger_connection_timeout()
        elif choice == '5':
            clear_all_errors()
        elif choice == '0':
            print("Exiting...")
            break
        else:
            print("Invalid choice.")
            
        input("\nPress Enter to return to menu...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
