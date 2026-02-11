"""
Mock Face Detection Data Sender
Simulates MediaPipe Face Mesh sending face detection events

This script is for testing the face detection API endpoints
Week 3, Wednesday - Testing Tool
"""

import requests
import time
import random
from datetime import datetime
from uuid import uuid4


# Configuration
BASE_URL = "http://localhost:8000"
SESSION_ID = "145c3fc1-0e68-4570-92e3-236f3a40febf"  # Replace with real session ID
SEND_RATE = 30  # FPS (MediaPipe default)
SEND_INTERVAL = 1.0 / SEND_RATE


def generate_mock_face_data():
    """
    Generate realistic mock face detection data
    
    Simulates different states: alert, drowsy, fatigued
    """
    state = random.choice(["alert", "alert", "drowsy", "fatigued"])
    
    # Eye Aspect Ratio (EAR)
    # Alert: 0.25-0.35, Drowsy: 0.15-0.25, Fatigued: 0.05-0.15
    if state == "alert":
        ear = random.uniform(0.25, 0.35)
        eyes_closed = False
        blink_rate = random.uniform(10, 20)
        fatigue_score = random.uniform(0, 30)
    elif state == "drowsy":
        ear = random.uniform(0.15, 0.25)
        eyes_closed = random.choice([True, False])
        blink_rate = random.uniform(25, 40)
        fatigue_score = random.uniform(40, 70)
    else:  # fatigued
        ear = random.uniform(0.05, 0.15)
        eyes_closed = random.choice([True, True, False])
        blink_rate = random.uniform(5, 15)
        fatigue_score = random.uniform(70, 95)
    
    # Mouth Aspect Ratio (MAR)
    yawning = random.random() < 0.05  # 5% chance of yawning
    mar = random.uniform(0.5, 0.8) if yawning else random.uniform(0.1, 0.4)
    
    # Head pose
    head_yaw = random.uniform(-0.2, 0.2)
    head_pitch = random.uniform(-0.15, 0.1)
    head_roll = random.uniform(-0.1, 0.1)
    
    # Cumulative blink count (increases over time)
    blink_count = random.randint(0, 100)
    
    return {
        "session_id": SESSION_ID,
        "timestamp": datetime.now().isoformat() + "Z",
        "eye_aspect_ratio": round(ear, 3),
        "mouth_aspect_ratio": round(mar, 3),
        "eyes_closed": eyes_closed,
        "yawning": yawning,
        "blink_count": blink_count,
        "blink_rate": round(blink_rate, 1),
        "head_yaw": round(head_yaw, 3),
        "head_pitch": round(head_pitch, 3),
        "head_roll": round(head_roll, 3),
        "face_fatigue_score": round(fatigue_score, 1)
    }


def send_face_stream(duration_seconds=30):
    """
    Send continuous face detection stream for testing
    
    Args:
        duration_seconds: How long to stream data
    """
    endpoint = f"{BASE_URL}/api/v1/face/events"
    
    print(f"🧪 Starting Mock Face Detection Stream")
    print(f"📡 Endpoint: {endpoint}")
    print(f"🆔 Session ID: {SESSION_ID}")
    print(f"⏱️  Duration: {duration_seconds} seconds")
    print(f"📊 Send Rate: {SEND_RATE} FPS")
    print("-" * 60)
    
    samples_sent = 0
    errors = 0
    start_time = time.time()
    
    try:
        while (time.time() - start_time) < duration_seconds:
            # Generate mock data
            face_data = generate_mock_face_data()
            
            # Send to backend
            try:
                response = requests.post(endpoint, json=face_data, timeout=0.5)
                
                if response.status_code == 201:
                    samples_sent += 1
                    
                    # Print progress every 30 samples (1 second at 30 FPS)
                    if samples_sent % 30 == 0:
                        elapsed = time.time() - start_time
                        print(
                            f"✅ Sent {samples_sent} events | "
                            f"EAR: {face_data['eye_aspect_ratio']:.2f} | "
                            f"Fatigue: {face_data['face_fatigue_score']:.1f}% | "
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
        print(f"   Events sent: {samples_sent}")
        print(f"   Errors: {errors}")
        print(f"   Duration: {elapsed_time:.2f}s")
        print(f"   Actual rate: {actual_rate:.1f} FPS")
        print(f"   Success rate: {((samples_sent / (samples_sent + errors)) * 100) if (samples_sent + errors) > 0 else 0:.1f}%")


def check_face_stats():
    """Check face detection statistics"""
    endpoint = f"{BASE_URL}/api/v1/face/stats/{SESSION_ID}"
    
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            stats = response.json()
            print("📊 Face Detection Statistics:")
            print(f"   Total events: {stats['total_events']}")
            print(f"   Duration: {stats.get('duration_seconds', 0):.1f}s")
            print(f"   Avg blink rate: {stats.get('avg_blink_rate', 0):.1f} bpm")
            print(f"   Eyes closed: {stats['eyes_closed_percentage']:.1f}%")
            print(f"   Yawn count: {stats['yawn_count']}")
            print(f"   Avg fatigue: {stats.get('avg_fatigue_score', 0):.1f}%")
            return True
        else:
            print(f"❌ Stats check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Could not connect to backend: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("😊 Fumorive Mock Face Detection Sender")
    print("=" * 60)
    print()
    
    print("📝 Instructions:")
    print("   1. Create a session in the backend")
    print("   2. Update SESSION_ID variable with real session ID")
    print("   3. Run this script to send mock face detection data")
    print()
    print("🎯 Press Ctrl+C to stop streaming")
    print("=" * 60)
    print()
    
    # Start streaming
    send_face_stream(duration_seconds=30)  # Stream for 30 seconds
    
    print()
    check_face_stats()
