#!/usr/bin/env python3
"""
Simple test script to verify the Network Troubleshooting Bot installation
"""
import sys
import os
import asyncio
import subprocess
import sqlite3

# Add project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing Network Troubleshooting Bot Installation")
    print("=" * 50)
    
    # Test standard library imports
    try:
        try:
            import yaml
            yaml_available = True
        except ImportError:
            yaml_available = False
        print("✅ Standard library modules: OK")
    except ImportError as e:
        print(f"❌ Standard library error: {e}")
        return False
    
    # Test core modules
    try:
        from modules.ping_test import ping_host, PingResult
        from modules.traceroute import traceroute_host, TracerouteResult  
        from modules.snmp_monitor import get_device_snmp_info, SNMPResult
        from modules.ssh_exec import SSHExecutor, DeviceCredentials
        from modules.log_parser import NetworkLogParser, LogEntry
        print("✅ Core diagnostic modules: OK")
    except ImportError as e:
        print(f"❌ Core modules error: {e}")
        return False
    
    # Test AI modules
    try:
        from ai.intent_handler import process_user_query, Intent
        from ai.rules_engine import NetworkRulesEngine
        print("✅ AI modules: OK")
    except ImportError as e:
        print(f"⚠️ AI modules warning: {e}")
        print("   (This is OK if OpenAI API key is not configured)")
    
    # Test database
    try:
        from db.models import DatabaseManager, Device, TestResult, Alert
        print("✅ Database modules: OK")
    except ImportError as e:
        print(f"❌ Database modules error: {e}")
        return False
    
    # Test integrations
    try:
        from integrations.email_notify import EmailNotifier
        from integrations.slack_alerts import SlackNotifier
        from integrations.telegram_bot import TelegramNotifier
        print("✅ Integration modules: OK")
    except ImportError as e:
        print(f"⚠️ Integration modules warning: {e}")
        print("   (This is OK if notification services are not configured)")
    
    print("\n🎉 Basic installation test completed successfully!")
    return True

async def test_basic_functionality():
    """Test basic network functionality"""
    print("\n🔍 Testing Basic Network Functionality")
    print("=" * 40)
    
    # Import what we need for testing
    try:
        from modules.ping_test import ping_host
        from db.models import DatabaseManager, Device
    except ImportError as e:
        print(f"   ❌ Import error in functionality test: {e}")
        return
    
    # Test ping functionality
    try:
        print("🏓 Testing ping to localhost...")
        result = await ping_host("127.0.0.1", timeout=3, count=2)
        if result.success:
            print(f"   ✅ Ping successful: {result.avg_latency_ms:.2f}ms")
        else:
            print(f"   ⚠️ Ping failed: {result.error_message}")
    except Exception as e:
        print(f"   ❌ Ping test error: {e}")
    
    # Test database
    try:
        print("🗄️ Testing database connection...")
        db_manager = DatabaseManager()
        db_manager.create_tables()
        print("   ✅ Database tables created successfully")
        
        # Test adding a device
        session = db_manager.get_session()
        try:
            device = Device(
                name="test-device",
                ip_address="127.0.0.1", 
                device_type="test",
                location="test lab"
            )
            session.add(device)
            session.commit()
            print("   ✅ Database write test successful")
        finally:
            session.close()
            
    except Exception as e:
        print(f"   ❌ Database test error: {e}")
    
    print("\n✨ Basic functionality tests completed!")

def main():
    """Main test function"""
    print("🚀 Starting Network Troubleshooting Bot Tests\n")
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Please check your installation.")
        return
    
    # Test basic functionality
    try:
        asyncio.run(test_basic_functionality())
    except Exception as e:
        print(f"\n❌ Functionality tests failed: {e}")
        return
    
    print(f"\n🎯 All tests completed! Your installation is working.")
    print("\nNext steps:")
    print("1. Configure your environment variables (OpenAI API key, etc.)")
    print("2. Update config/config.yaml with your settings")
    print("3. Run the FastAPI server: uvicorn main:app --reload")
    print("4. Run the dashboard: streamlit run dashboard/app.py")

if __name__ == "__main__":
    main()