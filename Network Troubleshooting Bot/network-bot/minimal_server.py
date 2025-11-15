#!/usr/bin/env python3
"""
Network Troubleshooting Bot - Minimal Working Version
Simple HTTP server with core network diagnostics
"""

import asyncio
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import threading

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test what modules are available
MODULES_AVAILABLE = {}

try:
    from modules.ping_test import ping_host
    MODULES_AVAILABLE['ping'] = True
    print("✓ Ping module loaded")
except ImportError as e:
    print(f"✗ Ping module failed: {e}")
    MODULES_AVAILABLE['ping'] = False

try:
    from modules.traceroute import traceroute_host
    MODULES_AVAILABLE['traceroute'] = True
    print("✓ Traceroute module loaded")
except ImportError as e:
    print(f"✗ Traceroute module failed: {e}")
    MODULES_AVAILABLE['traceroute'] = False

try:
    from modules.log_parser import parse_log_content
    MODULES_AVAILABLE['log_parser'] = True
    print("✓ Log parser module loaded")
except ImportError as e:
    print(f"✗ Log parser module failed: {e}")
    MODULES_AVAILABLE['log_parser'] = False

class NetworkBotHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Network Bot API"""
    
    def do_GET(self):
        """Handle GET requests"""
        # Parse the URL to get just the path without query parameters
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path == '/':
            self.send_json_response({
                "message": "Network Troubleshooting Bot API",
                "version": "1.0.0",
                "endpoints": {
                    "/health": "Health check",
                    "/status": "System status", 
                    "/ping?target=X": "Ping test",
                    "/traceroute?target=X": "Traceroute test"
                }
            })
        
        elif path == '/health':
            self.send_json_response({
                "status": "healthy",
                "modules": MODULES_AVAILABLE
            })
        
        elif path == '/status':
            self.send_json_response({
                "server": "running",
                "available_modules": MODULES_AVAILABLE,
                "total_modules": sum(MODULES_AVAILABLE.values())
            })
        
        elif path == '/ping':
            self.handle_ping_request()
        
        elif path == '/traceroute':
            self.handle_traceroute_request()
        
        else:
            self.send_error(404, "Endpoint not found")
    
    def handle_ping_request(self):
        """Handle ping requests"""
        if not MODULES_AVAILABLE.get('ping', False):
            self.send_json_response({
                "error": "Ping module not available"
            }, status=503)
            return
        
        # Parse query parameters
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        target = params.get('target', ['8.8.8.8'])[0]
        count = int(params.get('count', ['3'])[0])
        timeout = int(params.get('timeout', ['5'])[0])
        
        # Run ping in background thread
        def run_ping():
            try:
                # Import here to avoid unbound variable issues
                from modules.ping_test import ping_host
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(ping_host(target, timeout, count))
                
                response = {
                    "target": target,
                    "success": result.success,
                    "packets_sent": result.packets_sent,
                    "packets_received": result.packets_received,
                    "packet_loss_percent": result.packet_loss_percent,
                    "avg_latency_ms": result.avg_latency_ms,
                    "min_latency_ms": result.min_latency_ms,
                    "max_latency_ms": result.max_latency_ms,
                    "error_message": result.error_message
                }
                
                self.send_json_response(response)
                
            except Exception as e:
                self.send_json_response({
                    "error": f"Ping failed: {str(e)}"
                }, status=500)
        
        # Start ping in background
        thread = threading.Thread(target=run_ping)
        thread.daemon = True
        thread.start()
        thread.join(timeout=30)  # Wait max 30 seconds
    
    def handle_traceroute_request(self):
        """Handle traceroute requests"""
        if not MODULES_AVAILABLE.get('traceroute', False):
            self.send_json_response({
                "error": "Traceroute module not available"
            }, status=503)
            return
        
        # Parse query parameters
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        target = params.get('target', ['8.8.8.8'])[0]
        max_hops = int(params.get('max_hops', ['15'])[0])
        timeout = int(params.get('timeout', ['3'])[0])
        
        # Run traceroute in background thread
        def run_traceroute():
            try:
                # Import here to avoid unbound variable issues
                from modules.traceroute import traceroute_host
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(traceroute_host(target, max_hops, timeout))
                
                response = {
                    "target": target,
                    "success": result.success,
                    "total_hops": result.total_hops,
                    "target_reached": result.target_reached,
                    "execution_time_ms": result.execution_time_ms,
                    "error_message": result.error_message,
                    "hops": [
                        {
                            "hop_number": hop.hop_number,
                            "ip_address": hop.ip_address,
                            "hostname": hop.hostname,
                            "avg_latency": sum(hop.latency_ms) / len(hop.latency_ms) if hop.latency_ms else 0,
                            "timeout": hop.timeout
                        }
                        for hop in result.hops[:5]  # Limit to first 5 hops for demo
                    ]
                }
                
                self.send_json_response(response)
                
            except Exception as e:
                self.send_json_response({
                    "error": f"Traceroute failed: {str(e)}"
                }, status=500)
        
        # Start traceroute in background
        thread = threading.Thread(target=run_traceroute)
        thread.daemon = True
        thread.start()
        thread.join(timeout=30)  # Wait max 30 seconds
    
    def send_json_response(self, data, status=200):
        """Send JSON response"""
        response = json.dumps(data, indent=2)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"[{self.address_string()}] {format % args}")

def main():
    """Main application entry point"""
    print("Network Troubleshooting Bot - Minimal HTTP Server")
    print("=" * 50)
    print(f"Available modules: {sum(MODULES_AVAILABLE.values())}/{len(MODULES_AVAILABLE)}")
    
    # Show available endpoints
    print("\nAvailable endpoints:")
    print("  http://localhost:8888/         - API info")
    print("  http://localhost:8888/health   - Health check")
    print("  http://localhost:8888/status   - System status")
    
    if MODULES_AVAILABLE.get('ping', False):
        print("  http://localhost:8888/ping?target=google.com - Ping test")
    
    if MODULES_AVAILABLE.get('traceroute', False):
        print("  http://localhost:8888/traceroute?target=1.1.1.1 - Traceroute test")
    
    # Start HTTP server
    server_address = ('127.0.0.1', 8888)
    httpd = HTTPServer(server_address, NetworkBotHandler)
    
    print(f"\n>> Server starting on http://localhost:8888")
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n>> Server stopped by user")
        httpd.shutdown()

if __name__ == "__main__":
    main()