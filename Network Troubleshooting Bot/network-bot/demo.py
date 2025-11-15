#!/usr/bin/env python3
"""
Network Troubleshooting Bot - Demo Script
Demonstrates key functionality and features
"""

import asyncio
import sys
import os

# Add project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🌐 AI-Powered Network Troubleshooting Bot - Demo")
print("=" * 60)

async def demo_ping_functionality():
    """Demonstrate ping testing capabilities"""
    print("\n🏓 PING FUNCTIONALITY DEMO")
    print("-" * 30)
    
    try:
        from modules.ping_test import ping_host
        
        # Test multiple targets
        targets = ["1.1.1.1", "8.8.8.8", "google.com"]
        
        for target in targets:
            try:
                print(f"Testing ping to {target}...")
                result = await ping_host(target, timeout=3, count=3)
                
                if result.success:
                    print(f"  ✅ Success: {result.avg_latency_ms:.1f}ms avg, {result.packet_loss_percent:.0f}% loss")
                else:
                    print(f"  ❌ Failed: {result.error_message}")
                    
            except Exception as e:
                print(f"  ⚠️ Error: {e}")
                
    except ImportError as e:
        print(f"  ⚠️ Import error: {e}")

async def demo_traceroute_functionality():
    """Demonstrate traceroute capabilities"""
    print("\n🛤️ TRACEROUTE FUNCTIONALITY DEMO")
    print("-" * 35)
    
    try:
        from modules.traceroute import traceroute_host
        
        targets = ["1.1.1.1", "google.com"]
        
        for target in targets:
            try:
                print(f"Tracing route to {target}...")
                result = await traceroute_host(target, max_hops=15, timeout=3)
                
                if result.success:
                    print(f"  ✅ Success: {result.total_hops} hops, target {'reached' if result.target_reached else 'not reached'}")
                    if result.hops and len(result.hops) > 0:
                        print(f"      First hop: {result.hops[0].ip_address or 'unknown'}")
                        if len(result.hops) > 1:
                            print(f"      Last hop: {result.hops[-1].ip_address or 'unknown'}")
                else:
                    print(f"  ❌ Failed: {result.error_message}")
                    
            except Exception as e:
                print(f"  ⚠️ Error: {e}")
                
    except ImportError as e:
        print(f"  ⚠️ Import error: {e}")

def demo_log_parser_functionality():
    """Demonstrate log parsing capabilities"""
    print("\n📝 LOG PARSER FUNCTIONALITY DEMO") 
    print("-" * 35)
    
    try:
        from modules.log_parser import NetworkLogParser, parse_log_content
        
        # Sample network logs
        sample_logs = [
            "Dec 12 10:30:15 Router1 %LINK-3-UPDOWN: Interface FastEthernet0/1, changed state to down",
            "Dec 12 10:30:16 Router1 %OSPF-5-ADJCHG: Process 1, Nbr 192.168.1.2 on FastEthernet0/1 from FULL to DOWN",
            "Dec 12 10:30:17 Switch1 %SYS-5-CONFIG_I: Configured from console by admin on vty0",
            "Dec 12 10:30:18 Firewall1 authentication failure from 192.168.1.100"
        ]
        
        print("Processing sample network logs...")
        
        parser = NetworkLogParser()
        total_parsed = 0
        
        for i, log_line in enumerate(sample_logs, 1):
            try:
                entries = parse_log_content(log_line)
                if entries:
                    entry = entries[0]
                    print(f"  ✅ Log {i}: {entry.severity.upper()} - {entry.message[:50]}...")
                    total_parsed += 1
                else:
                    print(f"  ⚠️ Log {i}: Could not parse")
            except Exception as e:
                print(f"  ❌ Log {i}: Error - {e}")
        
        print(f"\nSuccessfully parsed {total_parsed}/{len(sample_logs)} log entries")
        
        # Try full log analysis
        try:
            all_logs = "\n".join(sample_logs)
            entries = parser.parse_log_file(all_logs)
            if entries:
                analysis = parser.analyze_logs(entries)
                print(f"Analysis found:")
                print(f"  - Interface issues: {len(analysis.interface_issues)}")
                print(f"  - Security events: {len(analysis.security_events)}")
                print(f"  - Routing issues: {len(analysis.routing_issues)}")
        except Exception as e:
            print(f"  ⚠️ Analysis error: {e}")
            
    except ImportError as e:
        print(f"  ⚠️ Import error: {e}")

def demo_ai_functionality():
    """Demonstrate AI intent processing"""
    print("\n🤖 AI FUNCTIONALITY DEMO")
    print("-" * 25)
    
    try:
        from ai.intent_handler import process_user_query
        
        # Sample user queries
        queries = [
            "ping google.com",
            "check connectivity to 8.8.8.8", 
            "trace route to cloudflare.com",
            "help me troubleshoot network issues"
        ]
        
        print("Processing natural language queries...")
        
        for query in queries:
            try:
                print(f"\nQuery: '{query}'")
                result = process_user_query(query)
                print(f"  Intent: {result.intent.value}")
                print(f"  Suggested Action: {result.suggested_action}")
                print(f"  Confidence: {result.confidence:.1%}")
                if result.entities:
                    print(f"  Entities: {result.entities}")
                    
            except Exception as e:
                print(f"  ⚠️ Error processing query: {e}")
                
    except ImportError as e:
        print(f"  ⚠️ Import error (AI features require additional setup): {e}")

def demo_database_functionality():
    """Demonstrate database operations"""
    print("\n🗄️ DATABASE FUNCTIONALITY DEMO")
    print("-" * 33)
    
    try:
        from db.models import DatabaseManager, Device, TestResult
        
        print("Initializing database...")
        db_manager = DatabaseManager()
        db_manager.create_tables()
        print("  ✅ Database tables created successfully")
        
        # Add a test device
        session = db_manager.get_session()
        try:
            # Check if device already exists
            existing_device = session.query(Device).filter_by(name="demo-device").first()
            if not existing_device:
                device = Device(
                    name="demo-device",
                    ip_address="192.168.1.100",
                    device_type="demo",
                    location="Demo Lab"
                )
                session.add(device)
                session.commit()
                print("  ✅ Added demo device to database")
            else:
                print("  ℹ️ Demo device already exists")
                
            # Count devices
            device_count = session.query(Device).count()
            print(f"  📊 Total devices in database: {device_count}")
            
            # Count test results
            result_count = session.query(TestResult).count()
            print(f"  📊 Total test results in database: {result_count}")
            
        finally:
            session.close()
            
    except ImportError as e:
        print(f"  ⚠️ Import error: {e}")

async def main():
    """Main demo function"""
    print("Running comprehensive functionality demonstrations...\n")
    
    # Run all demos
    await demo_ping_functionality()
    await demo_traceroute_functionality()
    demo_log_parser_functionality()
    demo_ai_functionality()
    demo_database_functionality()
    
    print("\n" + "=" * 60)
    print("🎉 DEMO COMPLETE!")
    print("\nYour Network Troubleshooting Bot is ready with:")
    print("✅ Network connectivity testing (ping/traceroute)")
    print("✅ Intelligent log analysis and parsing")
    print("✅ Natural language query processing")
    print("✅ Database-backed device and result management")
    print("✅ Cross-platform compatibility")
    
    print(f"\n🚀 Next Steps:")
    print("1. Run the API server: python main.py")
    print("2. Launch the dashboard: streamlit run dashboard/app.py")
    print("3. Or deploy with Docker: ./deploy.sh (Linux/Mac) or deploy.bat (Windows)")
    print("4. Visit http://localhost:8501 for the interactive dashboard")
    
    print(f"\n📚 For more information, see README.md")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()