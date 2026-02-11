"""
Mock EEG Data Sender
Simulates Python LSL middleware sending EEG data via HTTP

This script is for testing the EEG data relay system without real hardware.
Week 3, Monday - Testing Tool
"""

import requests
import time
import random
from datetime import datetime
from uuid import uuid4


# Configuration
BASE_URL = "http://localhost:8000"
SESSION_ID = str(uuid4())  # Replace with real session ID from database
SAMPLE_RATE = 256  # Hz (Muse 2 default)
SEND_INTERVAL = 1.0 / SAMPLE_RATE  # Send every ~4ms for 256 Hz


def generate_mock_eeg_sample():
    """
    Generate realistic mock EEG data
    
    Simulates different states: alert, drowsy, fatigued
    """
    state = random.choice(["alert", "alert", "drowsy", "fatigued"])
    
    # Base channel values (simulated microvolts)
    base_tp9 = random.uniform(0.1, 0.5)
    base_af7 = random.uniform(0.1, 0.5)
    base_af8 = random.uniform(0.1, 0.5)
    base_tp10 = random.uniform(0.1, 0.5)
    
    # Processed metrics based on state
    if state == "alert":
        theta_power = random.uniform(0.2, 0.4)
        alpha_power = random.uniform(0.5, 0.7)
        theta_alpha_ratio = theta_power / alpha_power
        fatigue_score = random.uniform(0, 30)
    elif state == "drowsy":
        theta_power = random.uniform(0.5, 0.7)
        alpha_power = random.uniform(0.4, 0.6)
        theta_alpha_ratio = theta_power / alpha_power
        fatigue_score = random.uniform(40, 70)
    else:  # fatigued
        theta_power = random.uniform(0.7, 0.9)
        alpha_power = random.uniform(0.2, 0.4)
        theta_alpha_ratio = theta_power / alpha_power
        fatigue_score = random.uniform(70, 95)
    
    return {
        "session_id": SESSION_ID,
        "timestamp": datetime.now().isoformat() + "Z",
        "sample_rate": SAMPLE_RATE,
        "channels": {
            "TP9": round(base_tp9, 3),
            "AF7": round(base_af7, 3),
            "AF8": round(base_af8, 3),
            "TP10": round(base_tp10, 3)
        },
        "processed": {
            "theta_power": round(theta_power, 2),
            "alpha_power": round(alpha_power, 2),
            "theta_alpha_ratio": round(theta_alpha_ratio, 2),
            "fatigue_score": round(fatigue_score, 2)
        },
        "save_to_db": False  # Set to True to save to database
    }


def send_eeg_stream(duration_seconds=30):
    """
    Send continuous EEG stream for testing
    
    Args:
        duration_seconds: How long to stream data
    """
    endpoint = f"{BASE_URL}/api/v1/eeg/stream"
    
    print(f"🧪 Starting Mock EEG Stream")
    print(f"📡 Endpoint: {endpoint}")
    print(f"🆔 Session ID: {SESSION_ID}")
    print(f"⏱️  Duration: {duration_seconds} seconds")
    print(f"📊 Sample Rate: {SAMPLE_RATE} Hz")
    print("-" * 60)
    
    samples_sent = 0
    errors = 0
    start_time = time.time()
    
    try:
        while (time.time() - start_time) < duration_seconds:
            # Generate mock data
            eeg_data = generate_mock_eeg_sample()
            
            # Send to backend
            try:
                response = requests.post(endpoint, json=eeg_data, timeout=0.5)
                
                if response.status_code == 200:
                    samples_sent += 1
                    result = response.json()
                    clients = result.get("clients_notified", 0)
                    
                    # Print progress every 256 samples (1 second)
                    if samples_sent % 256 == 0:
                        elapsed = time.time() - start_time
                        print(
                            f"✅ Sent {samples_sent} samples | "
                            f"Clients: {clients} | "
                            f"Fatigue: {eeg_data['processed']['fatigue_score']:.1f}% | "
                            f"Elapsed: {elapsed:.1f}s"
                        )
                else:
                    errors += 1
                    print(f"❌ Error: {response.status_code} - {response.text}")
                
            except requests.exceptions.RequestException as e:
                errors += 1
                if errors < 5:  # Only show first few errors
                    print(f"❌ Request failed: {e}")
            
            # Wait for next sample
            time.sleep(SEND_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n⚠️  Stream interrupted by user")
    
    finally:
        elapsed_time = time.time() - start_time
        actual_rate = samples_sent / elapsed_time if elapsed_time > 0 else 0
        
        print("-" * 60)
        print(f"📊 Stream Summary:")
        print(f"   Samples sent: {samples_sent}")
        print(f"   Errors: {errors}")
        print(f"   Duration: {elapsed_time:.2f}s")
        print(f"   Actual rate: {actual_rate:.1f} Hz")
        print(f"   Success rate: {((samples_sent / (samples_sent + errors)) * 100) if (samples_sent + errors) > 0 else 0:.1f}%")


def check_eeg_status():
    """Check EEG streaming status"""
    endpoint = f"{BASE_URL}/api/v1/eeg/status"
    
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            status = response.json()
            print("📊 EEG Status:")
            print(f"   Status: {status['status']}")
            print(f"   Active sessions: {status['active_eeg_sessions']}")
            print(f"   WebSocket connections: {status['websocket']['total_connections']}")
            return True
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Could not connect to backend: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🧠 Fumorive Mock EEG Data Sender")
    print("=" * 60)
    print()
    
    # Check if backend is running
    if not check_eeg_status():
        print("\n⚠️  Backend not running or EEG endpoints not available")
        print("💡 Start backend: python main.py")
        exit(1)
    
    print()
    print("📝 Instructions:")
    print("   1. Create a session in the backend")
    print("   2. Update SESSION_ID variable with real session ID")
    print("   3. Open WebSocket client to connect to session")
    print("   4. Run this script to send mock EEG data")
    print()
    print("🎯 Press Ctrl+C to stop streaming")
    print("=" * 60)
    print()
    
    # Start streaming
    send_eeg_stream(duration_seconds=60)  # Stream for 60 seconds
