"""Check for available LSL streams"""
from pylsl import resolve_streams

print("Searching for LSL streams (5 seconds)...")
streams = resolve_streams(wait_time=5.0)

if streams:
    print(f"\n✅ Found {len(streams)} stream(s):")
    for s in streams:
        print(f"   - Name: {s.name()}")
        print(f"     Type: {s.type()}")
        print(f"     Channels: {s.channel_count()}")
        print(f"     Rate: {s.nominal_srate()} Hz")
        print()
else:
    print("\n❌ No LSL streams found!")
    print("\nPossible issues:")
    print("1. muselsl stream not running")
    print("2. Muse device not connected via Bluetooth")
    print("3. Firewall blocking LSL communication")
