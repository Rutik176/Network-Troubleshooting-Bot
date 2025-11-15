#!/usr/bin/env python3
"""
Network Troubleshooting Bot - Working Demo Script
Tests core functionality without external dependencies
"""

import asyncio
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

print("Network Troubleshooting Bot - Demo")
print("=" * 40)

async def test_ping():
    """Test ping functionality"""
    print("\n1. PING TEST")
    print("-" * 15)
    
    try:
        from modules.ping_test import ping_host
        
        targets = ["8.8.8.8", "1.1.1.1"]
        for target in targets:
            try:
                print(f"Testing ping to {target}...")
                result = await ping_host(target, timeout=3, count=2)
                if result.success:
                    print(f"  SUCCESS: {result.avg_latency_ms:.1f}ms avg, {result.packet_loss_percent:.0f}% loss")
                else:
                    print(f"  FAILED: {result.error_message}")
            except Exception as e:
                print(f"  ERROR: {e}")
                
    except ImportError as e:
        print(f"  Import error: {e}")

async def test_traceroute():
    """Test traceroute functionality"""
    print("\n2. TRACEROUTE TEST")
    print("-" * 20)
    
    try:
        from modules.traceroute import traceroute_host
        
        target = "1.1.1.1"
        print(f"Testing traceroute to {target}...")
        result = await traceroute_host(target, max_hops=10, timeout=3)
        if result.success:
            print(f"  SUCCESS: {result.total_hops} hops, {result.execution_time_ms:.0f}ms")
        else:
            print(f"  FAILED: {result.error_message}")
            
    except ImportError as e:
        print(f"  Import error: {e}")
    except Exception as e:
        print(f"  ERROR: {e}")

def test_log_parser():
    """Test log parsing"""
    print("\n3. LOG PARSER TEST")
    print("-" * 20)
    
    try:
        from modules.log_parser import parse_log_content
        
        sample = "Dec 12 10:30:15 Router1 %LINK-3-UPDOWN: Interface FastEthernet0/1, changed state to down"
        print("Testing log parser...")
        entries = parse_log_content(sample)
        if entries:
            print(f"  SUCCESS: Parsed {len(entries)} entries")
        else:
            print("  No entries parsed")
            
    except ImportError as e:
        print(f"  Import error: {e}")
    except Exception as e:
        print(f"  ERROR: {e}")

def test_api_server():
    """Test if API server can start"""
    print("\n4. API SERVER TEST")
    print("-" * 20)
    
    try:
        import fastapi
        import uvicorn
        print("  SUCCESS: FastAPI and Uvicorn available")
        print("  You can run: python simple_main.py")
        
    except ImportError as e:
        print(f"  Import error: {e}")
        print("  Install with: pip install fastapi uvicorn")

async def main():
    """Run all tests"""
    await test_ping()
    await test_traceroute()
    test_log_parser()
    test_api_server()
    
    print("\n" + "=" * 40)
    print("DEMO COMPLETE")
    print("\nTo start the API server:")
    print("  python simple_main.py")
    print("\nThen visit:")
    print("  http://localhost:8000/docs")
    print("  http://localhost:8000/health")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDemo interrupted")
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()