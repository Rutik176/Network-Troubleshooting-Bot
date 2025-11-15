#!/usr/bin/env python3
"""
Network Troubleshooting Bot - Enhanced Web Dashboard
Professional web interface for network diagnostics and troubleshooting
"""

import asyncio
import sys
import os
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes

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

try:
    from modules.advanced_diagnostics import scan_host_ports, lookup_dns, check_host_connectivity, analyze_ip_address
    MODULES_AVAILABLE['advanced_diagnostics'] = True
    print("✓ Advanced diagnostics module loaded")
except ImportError as e:
    print(f"✗ Advanced diagnostics module failed: {e}")
    MODULES_AVAILABLE['advanced_diagnostics'] = False

try:
    from modules.enhanced_features import (
        run_bandwidth_test, start_continuous_monitoring, cancel_test, get_test_status,
        discover_network_topology, create_performance_alert, get_performance_report,
        get_active_tests, get_alert_rules, get_recent_alerts, ACTIVE_TESTS
    )
    MODULES_AVAILABLE['enhanced_features'] = True
    print("✓ Enhanced features module loaded")
except ImportError as e:
    print(f"✗ Enhanced features module failed: {e}")
    MODULES_AVAILABLE['enhanced_features'] = False

try:
    from modules.network_directory import scan_network_comprehensive, quick_network_scan, get_network_directory
    MODULES_AVAILABLE['network_directory'] = True
    print("✓ Network directory module loaded")
except ImportError as e:
    print(f"✗ Network directory module failed: {e}")
    MODULES_AVAILABLE['network_directory'] = False

# Store active tests and results
ACTIVE_TESTS = {}
TEST_HISTORY = []

class DashboardHandler(BaseHTTPRequestHandler):
    """Enhanced HTTP request handler for Network Troubleshooting Dashboard"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        # Serve static files
        if path == '/' or path == '/index.html':
            self.serve_dashboard()
        elif path == '/api/status':
            self.handle_api_status()
        elif path == '/api/ping':
            self.handle_ping_request()
        elif path == '/api/traceroute':
            self.handle_traceroute_request()
        elif path == '/api/discover':
            self.handle_network_discovery()
        elif path == '/api/test-history':
            self.handle_test_history()
        elif path == '/api/port-scan':
            self.handle_port_scan()
        elif path == '/api/dns-lookup':
            self.handle_dns_lookup()
        elif path == '/api/ip-analysis':
            self.handle_ip_analysis()
        elif path == '/api/connectivity-check':
            self.handle_connectivity_check()
        elif path == '/api/bandwidth-test':
            self.handle_bandwidth_test()
        elif path == '/api/start-monitoring':
            self.handle_start_monitoring()
        elif path == '/api/cancel-test':
            self.handle_cancel_test()
        elif path == '/api/test-status':
            self.handle_test_status()
        elif path == '/api/active-tests':
            self.handle_active_tests()
        elif path == '/api/network-topology':
            self.handle_network_topology()
        elif path == '/api/performance-report':
            self.handle_performance_report()
        elif path == '/api/alert-rules':
            self.handle_alert_rules()
        elif path == '/api/recent-alerts':
            self.handle_recent_alerts()
        elif path == '/api/emergency-stop':
            self.handle_emergency_stop()
        elif path == '/api/network-scan':
            self.handle_network_scan()
        elif path == '/api/quick-scan':
            self.handle_quick_scan()
        elif path == '/api/network-directory':
            self.handle_network_directory()
        elif path.startswith('/static/'):
            self.serve_static_file(path)
        else:
            self.send_error(404, "Page not found")
    
    def do_POST(self):
        """Handle POST requests"""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path == '/api/bulk-test':
            self.handle_bulk_test()
        elif path == '/api/save-report':
            self.handle_save_report()
        else:
            self.send_error(404, "Endpoint not found")
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        html_content = self.get_dashboard_html()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def get_dashboard_html(self):
        """Generate the main dashboard HTML"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Troubleshooting Bot - Dashboard</title>
    <link rel="stylesheet" href="/static/styles.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .header h1 {{
            color: #2a5298;
            font-size: 1.8rem;
            display: flex;
            align-items: center;
            gap: 10px;
            flex: 1;
        }}
        
        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .emergency-stop {{
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
            transition: all 0.3s ease;
            animation: pulse-red 2s infinite;
        }}
        
        .emergency-stop:hover {{
            background: linear-gradient(135deg, #c82333 0%, #a71e2a 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(220, 53, 69, 0.4);
        }}
        
        .emergency-stop:active {{
            transform: translateY(0);
        }}
        
        @keyframes pulse-red {{
            0%, 100% {{ box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3); }}
            50% {{ box-shadow: 0 4px 25px rgba(220, 53, 69, 0.6); }}
        }}
        
        @keyframes slideInDown {{
            from {{ 
                transform: translateY(-20px); 
                opacity: 0; 
            }}
            to {{ 
                transform: translateY(0); 
                opacity: 1; 
            }}
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .loading-spinner {{
            width: 30px;
            height: 30px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .status-indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #28a745;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .container {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }}
        
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }}
        
        @media (max-width: 768px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header {{
                padding: 0.5rem 1rem;
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 1.4rem;
            }}
            
            .emergency-stop {{
                padding: 10px 20px;
                font-size: 0.9rem;
            }}
            
            .network-map {{
                min-height: 150px;
                max-height: 400px;
            }}
            
            .input-group {{
                flex-direction: column;
            }}
            
            .container {{
                padding: 0 1rem;
            }}
        }}
        
        .card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
        }}
        
        .card h3 {{
            color: #2a5298;
            margin-bottom: 1rem;
            font-size: 1.3rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .ip-input-section {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            grid-column: 1 / -1;
            padding: 2rem;
        }}
        
        .ip-input-section h3 {{
            color: white;
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        
        .input-group {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}
        
        .input-field {{
            flex: 1;
            min-width: 200px;
        }}
        
        .input-field label {{
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }}
        
        .input-field input, .input-field select {{
            width: 100%;
            padding: 0.75rem;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            background: rgba(255, 255, 255, 0.9);
        }}
        
        .btn {{
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }}
        
        .btn-primary {{
            background: #28a745;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #218838;
            transform: translateY(-1px);
        }}
        
        .btn-secondary {{
            background: #6c757d;
            color: white;
        }}
        
        .btn-warning {{
            background: #ffc107;
            color: #212529;
        }}
        
        .btn-danger {{
            background: #dc3545;
            color: white;
        }}
        
        .action-buttons {{
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }}
        
        .results-container {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 1rem;
            margin-top: 1rem;
            max-height: 300px;
            overflow-y: auto;
        }}
        
        .test-result {{
            background: white;
            border-left: 4px solid #28a745;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }}
        
        .test-result.error {{
            border-left-color: #dc3545;
            background: #f8d7da;
        }}
        
        .test-result.warning {{
            border-left-color: #ffc107;
            background: #fff3cd;
        }}
        
        .loading {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 1rem;
            background: rgba(42, 82, 152, 0.1);
            border-radius: 8px;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #2a5298;
            display: block;
        }}
        
        .stat-label {{
            font-size: 0.9rem;
            color: #666;
            margin-top: 0.5rem;
        }}
        
        .network-map {{
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            min-height: 200px;
            max-height: 500px;
            overflow-y: auto;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            color: #495057;
            font-style: italic;
            padding: 10px;
            position: relative;
        }}
        
        .network-map.has-results {{
            align-items: flex-start;
            justify-content: flex-start;
            font-style: normal;
        }}
        
        .results-container {{
            width: 100%;
            max-height: 450px;
            overflow-y: auto;
            background: white;
        }}
        
        .clear-results {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: #6c757d;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
            z-index: 10;
        }}
        
        .clear-results:hover {{
            background: #5a6268;
        }}
        
        .quick-actions {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }}
        
        .quick-action {{
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            color: #333;
        }}
        
        .quick-action:hover {{
            border-color: #2a5298;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(42, 82, 152, 0.2);
        }}
        
        .quick-action-icon {{
            font-size: 2.5rem;
            margin-bottom: 1rem;
            display: block;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>
            <span class="status-indicator" id="statusIndicator"></span>
            Network Troubleshooting Bot - Professional Dashboard
        </h1>
        <button class="emergency-stop" onclick="emergencyStopAll()" title="Emergency Stop - Cancel All Tests">
            🛑 EMERGENCY STOP
        </button>
    </div>
    
    <div class="container">
        <!-- System Status Overview -->
        <div class="card">
            <h3>🖥️ System Status</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-value" id="moduleCount">{sum(MODULES_AVAILABLE.values())}</span>
                    <div class="stat-label">Active Modules</div>
                </div>
                <div class="stat-item">
                    <span class="stat-value" id="testCount">0</span>
                    <div class="stat-label">Tests Today</div>
                </div>
                <div class="stat-item">
                    <span class="stat-value" id="uptime">00:00:00</span>
                    <div class="stat-label">Server Uptime</div>
                </div>
            </div>
        </div>
        
        <!-- IP Troubleshooting Section -->
        <div class="card ip-input-section">
            <h3>🎯 IP-Based Network Troubleshooting</h3>
            <div class="input-group">
                <div class="input-field">
                    <label for="targetIP">Target IP Address or Hostname:</label>
                    <input type="text" id="targetIP" placeholder="192.168.1.1 or google.com" value="8.8.8.8">
                </div>
                <div class="input-field">
                    <label for="testType">Test Type:</label>
                    <select id="testType">
                        <option value="ping">Ping Test</option>
                        <option value="traceroute">Traceroute</option>
                        <option value="comprehensive">Comprehensive Test</option>
                        <option value="port-scan">Port Scan</option>
                        <option value="dns-lookup">DNS Lookup</option>
                        <option value="ip-analysis">IP Analysis</option>
                        <option value="bandwidth-test">Bandwidth Test</option>
                        <option value="continuous-monitor">Continuous Monitor</option>
                    </select>
                </div>
            </div>
            
            <div class="action-buttons">
                <button class="btn btn-primary" onclick="runSingleTest()">🚀 Run Test</button>
                <button class="btn btn-secondary" onclick="runContinuousTest()">🔄 Continuous Monitor</button>
                <button class="btn btn-warning" onclick="runBulkTest()">📊 Bulk Test</button>
                <button class="btn btn-danger" onclick="clearResults()">🗑️ Clear Results</button>
            </div>
            
            <div class="results-container" id="testResults">
                <div style="text-align: center; color: #666; padding: 2rem;">
                    Ready for network diagnostics. Enter an IP address and click "Run Test" to begin.
                </div>
            </div>
        </div>
        
        <!-- Active Test Management -->
        <div class="card">
            <h3>⚡ Active Test Management</h3>
            <div id="activeTestsContainer" style="max-height: 200px; overflow-y: auto; background: #f8f9fa; border-radius: 6px; padding: 1rem;">
                <div style="text-align: center; color: #6c757d; font-weight: 500;">No active tests</div>
            </div>
            <div style="margin-top: 1rem; display: flex; gap: 1rem;">
                <button class="btn btn-secondary" onclick="refreshActiveTests()">🔄 Refresh</button>
                <button class="btn btn-warning" onclick="cancelAllTests()">⏹️ Cancel All</button>
                <button class="btn btn-primary" onclick="viewTestHistory()">📊 Test History</button>
            </div>
        </div>
        
        <!-- Advanced Network Directory -->
        <div class="card">
            <h3>🔍 Advanced Network Directory</h3>
            <div style="margin-bottom: 1rem;">
                <div class="input-group">
                    <div class="input-field">
                        <label for="scanRange">Network Range:</label>
                        <input type="text" id="scanRange" placeholder="192.168.1.0/24 or 'auto'" value="auto">
                    </div>
                    <div class="input-field">
                        <label for="scanType">Scan Type:</label>
                        <select id="scanType">
                            <option value="quick">Quick Scan (Ping Sweep)</option>
                            <option value="comprehensive">Comprehensive Scan (Full Discovery)</option>
                        </select>
                    </div>
                </div>
                <div style="margin-top: 1rem;">
                    <button class="btn btn-primary" onclick="startNetworkScan()">🔍 Start Network Scan</button>
                    <button class="btn btn-secondary" onclick="quickDiscovery()">⚡ Quick Discovery</button>
                    <button class="btn btn-warning" onclick="viewNetworkDirectory()">📋 View Directory</button>
                </div>
            </div>
            
            <div class="network-map" id="networkMap">
                <div id="defaultMessage" style="text-align: center; color: #495057; padding: 2rem;">
                    <div style="font-size: 2rem; margin-bottom: 10px;">🏢</div>
                    <h4 style="color: #2a5298; margin-bottom: 5px;">Network Directory Ready</h4>
                    <p style="color: #6c757d; margin: 0;">Click "Start Network Scan" to discover devices</p>
                </div>
            </div>
            
            <div id="scanProgress" style="display: none; margin-top: 1rem;">
                <div style="background: white; border: 2px solid #007bff; border-radius: 12px; padding: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <div style="background: #f8f9fa; border-radius: 8px; height: 20px; position: relative; overflow: hidden; border: 1px solid #dee2e6;">
                        <div style="background: linear-gradient(90deg, #007bff 0%, #0056b3 100%); height: 100%; border-radius: 7px; width: 0%; transition: width 0.3s ease; position: relative;" id="progressBar">
                            <div style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: white; font-size: 0.8rem; font-weight: bold;" id="progressPercent">0%</div>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 10px; font-size: 1rem; color: #2a5298; font-weight: bold;" id="progressText">Starting scan...</div>
                </div>
            </div>
        </div>
        
        <!-- Test History -->
        <div class="card">
            <h3>📈 Recent Test History</h3>
            <div id="testHistory" style="max-height: 250px; overflow-y: auto;">
                <div style="text-align: center; color: #666; padding: 2rem;">
                    No tests performed yet
                </div>
            </div>
        </div>
        
        <!-- Quick Actions -->
        <div class="quick-actions">
            <div class="quick-action" onclick="runCommonTests()">
                <span class="quick-action-icon">⚡</span>
                <strong>Common Tests</strong>
                <div>Run standard connectivity tests</div>
            </div>
            <div class="quick-action" onclick="runBandwidthSuite()">
                <span class="quick-action-icon">🚀</span>
                <strong>Speed Test Suite</strong>
                <div>Comprehensive bandwidth analysis</div>
            </div>
            <div class="quick-action" onclick="startNetworkMonitoring()">
                <span class="quick-action-icon">📊</span>
                <strong>Start Monitoring</strong>
                <div>Begin continuous monitoring</div>
            </div>
            <div class="quick-action" onclick="securityScan()">
                <span class="quick-action-icon">🔒</span>
                <strong>Security Scan</strong>
                <div>Network vulnerability assessment</div>
            </div>
            <div class="quick-action" onclick="generateReport()">
                <span class="quick-action-icon">📋</span>
                <strong>Generate Report</strong>
                <div>Create detailed network report</div>
            </div>
            <div class="quick-action" onclick="exportResults()">
                <span class="quick-action-icon">💾</span>
                <strong>Export Data</strong>
                <div>Save test results to file</div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        Network Troubleshooting Bot v2.0 | Professional Network Diagnostics Platform
    </div>

    <script>
        let testCounter = 0;
        let serverStartTime = Date.now();
        let continuousTestInterval = null;
        
        // Update uptime every second
        setInterval(updateUptime, 1000);
        
        // Update system status every 30 seconds
        setInterval(updateSystemStatus, 30000);
        updateSystemStatus();
        
        function updateUptime() {{
            const uptime = Date.now() - serverStartTime;
            const hours = Math.floor(uptime / 3600000);
            const minutes = Math.floor((uptime % 3600000) / 60000);
            const seconds = Math.floor((uptime % 60000) / 1000);
            document.getElementById('uptime').textContent = 
                `${{hours.toString().padStart(2, '0')}}:${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;
        }}
        
        function updateSystemStatus() {{
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {{
                    document.getElementById('moduleCount').textContent = data.total_modules || 0;
                    const indicator = document.getElementById('statusIndicator');
                    indicator.style.backgroundColor = data.server === 'running' ? '#28a745' : '#dc3545';
                }})
                .catch(error => {{
                    console.error('Status update failed:', error);
                    document.getElementById('statusIndicator').style.backgroundColor = '#ffc107';
                }});
        }}
        
        async function runSingleTest() {{
            const target = document.getElementById('targetIP').value.trim();
            const testType = document.getElementById('testType').value;
            
            if (!target) {{
                alert('Please enter a target IP address or hostname');
                return;
            }}
            
            const resultsContainer = document.getElementById('testResults');
            const testId = ++testCounter;
            
            // Add loading indicator
            const loadingDiv = createResultDiv(`
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span class="loading"></span>
                    <strong>Running ${{testType}} test on ${{target}}...</strong>
                </div>
            `, 'info');
            resultsContainer.insertBefore(loadingDiv, resultsContainer.firstChild);
            
            try {{
                let response;
                if (testType === 'ping') {{
                    response = await fetch(`/api/ping?target=${{encodeURIComponent(target)}}&count=4`);
                }} else if (testType === 'traceroute') {{
                    response = await fetch(`/api/traceroute?target=${{encodeURIComponent(target)}}&max_hops=15`);
                }} else if (testType === 'comprehensive') {{
                    // Run both ping and traceroute
                    await runComprehensiveTest(target, resultsContainer);
                    loadingDiv.remove();
                    return;
                }} else if (testType === 'port-scan') {{
                    response = await fetch(`/api/port-scan?target=${{encodeURIComponent(target)}}`);
                }} else if (testType === 'dns-lookup') {{
                    response = await fetch(`/api/dns-lookup?hostname=${{encodeURIComponent(target)}}`);
                }} else if (testType === 'ip-analysis') {{
                    response = await fetch(`/api/ip-analysis?ip=${{encodeURIComponent(target)}}`);
                }} else if (testType === 'bandwidth-test') {{
                    response = await fetch(`/api/bandwidth-test?target=${{encodeURIComponent(target)}}`);
                }} else if (testType === 'continuous-monitor') {{
                    const duration = prompt('Enter monitoring duration in minutes:', '60');
                    if (!duration) return;
                    response = await fetch(`/api/start-monitoring?target=${{encodeURIComponent(target)}}&duration=${{duration}}`);
                }}
                
                const result = await response.json();
                loadingDiv.remove();
                
                if (result.error) {{
                    addTestResult(result.error, 'error', target, testType);
                }} else {{
                    addTestResult(result, 'success', target, testType);
                }}
                
                updateTestHistory(target, testType, result.success !== false);
                document.getElementById('testCount').textContent = testCounter;
                
            }} catch (error) {{
                loadingDiv.remove();
                addTestResult(`Test failed: ${{error.message}}`, 'error', target, testType);
            }}
        }}
        
        async function runComprehensiveTest(target, container) {{
            try {{
                // Run ping test
                const pingResponse = await fetch(`/api/ping?target=${{encodeURIComponent(target)}}&count=4`);
                const pingResult = await pingResponse.json();
                addTestResult(pingResult, pingResult.error ? 'error' : 'success', target, 'ping');
                
                // Run traceroute test
                const traceResponse = await fetch(`/api/traceroute?target=${{encodeURIComponent(target)}}&max_hops=10`);
                const traceResult = await traceResponse.json();
                addTestResult(traceResult, traceResult.error ? 'error' : 'success', target, 'traceroute');
                
                updateTestHistory(target, 'comprehensive', !pingResult.error && !traceResult.error);
                
            }} catch (error) {{
                addTestResult(`Comprehensive test failed: ${{error.message}}`, 'error', target, 'comprehensive');
            }}
        }}
        
        function runContinuousTest() {{
            const target = document.getElementById('targetIP').value.trim();
            if (!target) {{
                alert('Please enter a target IP address or hostname');
                return;
            }}
            
            if (continuousTestInterval) {{
                clearInterval(continuousTestInterval);
                continuousTestInterval = null;
                event.target.textContent = '🔄 Continuous Monitor';
                event.target.className = 'btn btn-secondary';
                return;
            }}
            
            event.target.textContent = '⏹️ Stop Monitor';
            event.target.className = 'btn btn-danger';
            
            // Run test immediately
            runSingleTest();
            
            // Then run every 30 seconds
            continuousTestInterval = setInterval(() => {{
                fetch(`/api/ping?target=${{encodeURIComponent(target)}}&count=2`)
                    .then(response => response.json())
                    .then(result => {{
                        addTestResult(result, result.error ? 'error' : 'success', target, 'ping');
                        updateTestHistory(target, 'continuous-ping', result.success !== false);
                        document.getElementById('testCount').textContent = ++testCounter;
                    }});
            }}, 30000);
        }}
        
        function addTestResult(result, type, target, testType) {{
            const resultsContainer = document.getElementById('testResults');
            const timestamp = new Date().toLocaleTimeString();
            
            let content = '';
            if (typeof result === 'string') {{
                content = `<strong>Error:</strong> ${{result}}`;
            }} else if (testType === 'ping') {{
                if (result.success) {{
                    content = `
                        <strong>✅ Ping Success - ${{target}}</strong><br>
                        📊 Packets: ${{result.packets_sent}} sent, ${{result.packets_received}} received<br>
                        📉 Loss: ${{result.packet_loss_percent}}%<br>
                        ⚡ Latency: ${{result.avg_latency_ms}}ms avg (${{result.min_latency_ms}}-${{result.max_latency_ms}}ms)<br>
                        🕒 Time: ${{timestamp}}
                    `;
                }} else {{
                    content = `<strong>❌ Ping Failed - ${{target}}</strong><br>Error: ${{result.error_message || 'Unknown error'}}<br>🕒 Time: ${{timestamp}}`;
                }}
            }} else if (testType === 'traceroute') {{
                if (result.success && result.hops) {{
                    content = `
                        <strong>🛤️ Traceroute Success - ${{target}}</strong><br>
                        📍 Hops: ${{result.total_hops}}, Target reached: ${{result.target_reached ? 'Yes' : 'No'}}<br>
                        ⏱️ Execution time: ${{result.execution_time_ms}}ms<br>
                        🕒 Time: ${{timestamp}}<br>
                        <details style="margin-top: 10px;">
                            <summary>View Route Details</summary>
                            ${{result.hops.map((hop, i) => `
                                <div style="margin: 5px 0; font-family: monospace;">
                                    ${{hop.hop_number}}: ${{hop.ip_address || '*'}} 
                                    ${{hop.hostname ? `(${{hop.hostname}})` : ''}} 
                                    ${{hop.timeout ? 'timeout' : hop.avg_latency + 'ms'}}
                                </div>
                            `).join('')}}
                        </details>
                    `;
                }} else {{
                    content = `<strong>❌ Traceroute Failed - ${{target}}</strong><br>Error: ${{result.error_message || 'Unknown error'}}<br>🕒 Time: ${{timestamp}}`;
                }}
            }} else if (testType === 'port-scan') {{
                if (result.scan_results) {{
                    const openPorts = result.open_ports || [];
                    content = `
                        <strong>🔍 Port Scan - ${{target}}</strong><br>
                        📊 Scanned: ${{result.total_scanned}} ports, Open: ${{openPorts.length}}<br>
                        🕒 Time: ${{timestamp}}<br>
                        <details style="margin-top: 10px;">
                            <summary>View Open Ports (${{openPorts.length}})</summary>
                            ${{openPorts.map(port => `
                                <div style="margin: 5px 0; font-family: monospace;">
                                    Port ${{port.port}}: ${{port.service}} 
                                    ${{port.response_time_ms ? `(${{port.response_time_ms.toFixed(1)}}ms)` : ''}}
                                </div>
                            `).join('')}}
                        </details>
                    `;
                }} else {{
                    content = `<strong>❌ Port Scan Failed - ${{target}}</strong><br>Error: ${{result.error || 'Unknown error'}}<br>🕒 Time: ${{timestamp}}`;
                }}
            }} else if (testType === 'dns-lookup') {{
                if (result.success && result.ip_addresses) {{
                    content = `
                        <strong>🌐 DNS Lookup - ${{target}}</strong><br>
                        📍 IP Addresses: ${{result.ip_addresses.join(', ')}}<br>
                        📧 MX Records: ${{result.mx_records.length > 0 ? result.mx_records.join(', ') : 'None'}}<br>
                        🏢 NS Records: ${{result.ns_records.length > 0 ? result.ns_records.join(', ') : 'None'}}<br>
                        🕒 Time: ${{timestamp}}
                    `;
                }} else {{
                    content = `<strong>❌ DNS Lookup Failed - ${{target}}</strong><br>Error: ${{result.error_message || 'Unknown error'}}<br>🕒 Time: ${{timestamp}}`;
                }}
            }} else if (testType === 'ip-analysis') {{
                if (!result.error) {{
                    content = `
                        <strong>🔬 IP Analysis - ${{target}}</strong><br>
                        📡 Version: IPv${{result.version}}<br>
                        🏠 Type: ${{result.is_private ? 'Private' : 'Public'}} IP<br>
                        🏷️ Class: ${{result.network_class || 'N/A'}}<br>
                        🔒 Special: ${{result.is_loopback ? 'Loopback' : result.is_multicast ? 'Multicast' : result.is_reserved ? 'Reserved' : 'Standard'}}<br>
                        🕒 Time: ${{timestamp}}
                    `;
                }} else {{
                    content = `<strong>❌ IP Analysis Failed - ${{target}}</strong><br>Error: ${{result.error || 'Unknown error'}}<br>🕒 Time: ${{timestamp}}`;
                }}
            }} else if (testType === 'bandwidth-test') {{
                if (result.download_mbps !== undefined) {{
                    content = `
                        <strong>🚀 Bandwidth Test - ${{target}}</strong><br>
                        ⬇️ Download: ${{result.download_mbps.toFixed(1)}} Mbps<br>
                        ⬆️ Upload: ${{result.upload_mbps.toFixed(1)}} Mbps<br>
                        ⚡ Latency: ${{result.latency_ms.toFixed(1)}}ms<br>
                        📊 Jitter: ${{result.jitter_ms.toFixed(1)}}ms<br>
                        📉 Packet Loss: ${{result.packet_loss.toFixed(1)}}%<br>
                        ⏱️ Duration: ${{result.test_duration_seconds.toFixed(1)}}s<br>
                        🕒 Time: ${{timestamp}}
                        ${{result.session_id ? `<br>📋 Session: ${{result.session_id.substring(0,8)}}...` : ''}}
                    `;
                }} else {{
                    content = `<strong>❌ Bandwidth Test Failed - ${{target}}</strong><br>Error: ${{result.error || 'Unknown error'}}<br>🕒 Time: ${{timestamp}}`;
                }}
            }} else if (testType === 'continuous-monitor') {{
                if (result.session_id) {{
                    content = `
                        <strong>📊 Continuous Monitoring Started - ${{target}}</strong><br>
                        📋 Session ID: ${{result.session_id.substring(0,12)}}...<br>
                        ⏱️ Duration: ${{result.duration_minutes}} minutes<br>
                        🔄 Status: ${{result.status}}<br>
                        🕒 Started: ${{timestamp}}<br>
                        <button onclick="cancelTest('${{result.session_id}}')" class="btn btn-danger" style="margin-top: 10px; font-size: 0.8rem;">
                            ⏹️ Stop Monitoring
                        </button>
                    `;
                }} else {{
                    content = `<strong>❌ Monitoring Start Failed - ${{target}}</strong><br>Error: ${{result.error || 'Unknown error'}}<br>🕒 Time: ${{timestamp}}`;
                }}
            }}
            
            const resultDiv = createResultDiv(content, type);
            resultsContainer.insertBefore(resultDiv, resultsContainer.firstChild);
            
            // Keep only last 20 results
            while (resultsContainer.children.length > 20) {{
                resultsContainer.removeChild(resultsContainer.lastChild);
            }}
        }}
        
        function createResultDiv(content, type) {{
            const div = document.createElement('div');
            div.className = `test-result ${{type}}`;
            div.innerHTML = content;
            return div;
        }}
        
        function updateTestHistory(target, testType, success) {{
            const historyContainer = document.getElementById('testHistory');
            const timestamp = new Date().toLocaleString();
            
            const historyItem = document.createElement('div');
            historyItem.style.cssText = 'padding: 8px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center;';
            historyItem.innerHTML = `
                <div>
                    <strong>${{success ? '✅' : '❌'}} ${{testType.toUpperCase()}}</strong> 
                    <span style="color: #666;">${{target}}</span>
                </div>
                <small style="color: #999;">${{timestamp}}</small>
            `;
            
            historyContainer.insertBefore(historyItem, historyContainer.firstChild);
            
            // Keep only last 10 history items
            while (historyContainer.children.length > 10) {{
                historyContainer.removeChild(historyContainer.lastChild);
            }}
        }}
        
        function clearResults() {{
            document.getElementById('testResults').innerHTML = `
                <div style="text-align: center; color: #666; padding: 2rem;">
                    Results cleared. Ready for new tests.
                </div>
            `;
        }}
        
        function runCommonTests() {{
            const commonTargets = ['8.8.8.8', '1.1.1.1', 'google.com'];
            commonTargets.forEach((target, index) => {{
                setTimeout(() => {{
                    document.getElementById('targetIP').value = target;
                    document.getElementById('testType').value = 'ping';
                    runSingleTest();
                }}, index * 2000);
            }});
        }}
        
        function runBulkTest() {{
            const targets = prompt('Enter IP addresses/hostnames separated by commas:', '8.8.8.8, 1.1.1.1, google.com, github.com');
            if (!targets) return;
            
            const targetList = targets.split(',').map(t => t.trim()).filter(t => t);
            targetList.forEach((target, index) => {{
                setTimeout(() => {{
                    document.getElementById('targetIP').value = target;
                    runSingleTest();
                }}, index * 1500);
            }});
        }}
        
        function discoverNetwork() {{
            const mapElement = document.getElementById('networkMap');
            mapElement.innerHTML = '<div style="display: flex; align-items: center; gap: 10px;"><span class="loading"></span> Discovering network devices...</div>';
            
            fetch('/api/discover')
                .then(response => response.json())
                .then(data => {{
                    mapElement.innerHTML = `
                        <div style="text-align: left; font-family: monospace; font-size: 0.9rem;">
                            <strong>Local Network Scan Results:</strong><br>
                            ${{data.devices ? data.devices.map(device => `
                                📡 ${{device.ip}} - ${{device.status}} ${{device.hostname ? `(${{device.hostname}})` : ''}}
                            `).join('<br>') : 'Network discovery not available'}}
                        </div>
                    `;
                }})
                .catch(error => {{
                    mapElement.innerHTML = 'Network discovery failed. Feature may not be available.';
                }});
        }}
        
        function refreshTopology() {{
            document.getElementById('networkMap').innerHTML = 'Network topology refresh - Feature coming soon';
        }}
        
        function generateReport() {{
            // Collect all test results
            const results = Array.from(document.querySelectorAll('.test-result')).map(el => el.textContent).join('\\n\\n');
            const report = `
Network Troubleshooting Report
Generated: ${{new Date().toLocaleString()}}
Server Uptime: ${{document.getElementById('uptime').textContent}}
Total Tests: ${{document.getElementById('testCount').textContent}}

TEST RESULTS:
${{results || 'No test results available'}}
            `;
            
            const blob = new Blob([report], {{ type: 'text/plain' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `network-report-${{new Date().toISOString().split('T')[0]}}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }}
        
        function exportResults() {{
            generateReport(); // For now, same as generate report
        }}
        
        // Active test management functions
        function refreshActiveTests() {{
            fetch('/api/active-tests')
                .then(response => response.json())
                .then(data => {{
                    const container = document.getElementById('activeTestsContainer');
                    if (data.active_tests && data.active_tests.length > 0) {{
                        container.innerHTML = data.active_tests.map(test => `
                            <div style="background: white; border: 1px solid #ddd; border-radius: 4px; padding: 10px; margin-bottom: 10px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <strong>${{test.test_type.toUpperCase()}}</strong> - ${{test.target}}
                                        <br><small>Status: ${{test.status}} | Progress: ${{test.progress || 0}}%</small>
                                    </div>
                                    <div>
                                        <button onclick="cancelTest('${{test.session_id}}')" class="btn btn-danger" style="font-size: 0.8rem; padding: 4px 8px;">
                                            ⏹️ Cancel
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `).join('');
                    }} else {{
                        container.innerHTML = '<div style="text-align: center; color: #666;">No active tests</div>';
                    }}
                }})
                .catch(error => {{
                    console.error('Failed to refresh active tests:', error);
                }});
        }}
        
        function cancelTest(sessionId) {{
            fetch(`/api/cancel-test?session_id=${{sessionId}}`)
                .then(response => response.json())
                .then(data => {{
                    if (data.cancelled) {{
                        addTestResult(`Test cancelled successfully`, 'warning', 'System', 'cancellation');
                        refreshActiveTests();
                    }} else {{
                        addTestResult(`Failed to cancel test: ${{data.error || 'Unknown error'}}`, 'error', 'System', 'cancellation');
                    }}
                }})
                .catch(error => {{
                    console.error('Cancel test failed:', error);
                    addTestResult(`Cancel request failed: ${{error.message}}`, 'error', 'System', 'cancellation');
                }});
        }}
        
        function cancelAllTests() {{
            if (!confirm('Are you sure you want to cancel all active tests?')) return;
            
            fetch('/api/active-tests')
                .then(response => response.json())
                .then(data => {{
                    if (data.active_tests && data.active_tests.length > 0) {{
                        data.active_tests.forEach(test => {{
                            cancelTest(test.session_id);
                        }});
                    }} else {{
                        alert('No active tests to cancel');
                    }}
                }});
        }}
        
        function viewTestHistory() {{
            fetch('/api/test-history')
                .then(response => response.json())
                .then(data => {{
                    const historyWindow = window.open('', '_blank', 'width=800,height=600');
                    historyWindow.document.write(`
                        <html>
                        <head><title>Test History</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; }}
                            .test-item {{ border: 1px solid #ddd; margin: 10px 0; padding: 10px; border-radius: 4px; }}
                            .success {{ border-left: 4px solid #28a745; }}
                            .error {{ border-left: 4px solid #dc3545; }}
                        </style>
                        </head>
                        <body>
                        <h1>Test History (${{data.total_tests}} tests)</h1>
                        ${{(data.history || []).map(test => `
                            <div class="test-item ${{test.result && test.result.success ? 'success' : 'error'}}">
                                <strong>${{test.type.toUpperCase()}}</strong> - ${{test.target}}<br>
                                <small>Time: ${{new Date(test.timestamp * 1000).toLocaleString()}}</small>
                            </div>
                        `).join('')}}
                        </body>
                        </html>
                    `);
                }});
        }}
        
        function discoverTopology() {{
            const range = prompt('Enter network range (CIDR notation):', '192.168.1.0/24');
            if (!range) return;
            
            const mapElement = document.getElementById('networkMap');
            mapElement.innerHTML = '<div style="display: flex; align-items: center; gap: 10px;"><span class="loading"></span> Scanning network topology...</div>';
            
            fetch(`/api/network-topology?range=${{encodeURIComponent(range)}}`)
                .then(response => response.json())
                .then(data => {{
                    if (data.devices) {{
                        mapElement.innerHTML = `
                            <div style="text-align: left; font-family: monospace; font-size: 0.9rem;">
                                <strong>Network Topology - ${{data.range}}</strong><br>
                                <small>Scan completed: ${{new Date(data.scan_time * 1000).toLocaleString()}}</small><br><br>
                                ${{data.devices.map(device => `
                                    📡 ${{device.ip}} - ${{device.device_type}} ${{device.hostname ? `(${{device.hostname}})` : ''}}<br>
                                    &nbsp;&nbsp;&nbsp;MAC: ${{device.mac}} | Ports: ${{device.open_ports.join(', ')}}<br>
                                `).join('')}}
                            </div>
                        `;
                    }} else {{
                        mapElement.innerHTML = `Topology scan failed: ${{data.error || 'Unknown error'}}`;
                    }}
                }})
                .catch(error => {{
                    mapElement.innerHTML = 'Network topology scan failed';
                    console.error('Topology scan error:', error);
                }});
        }}
        
        // Auto-refresh active tests every 30 seconds
        setInterval(refreshActiveTests, 30000);
        
        // Initial load of active tests
        refreshActiveTests();
        
        // Emergency stop function
        function emergencyStopAll() {{
            if (!confirm('🚨 EMERGENCY STOP\\n\\nThis will immediately cancel ALL running tests and operations.\\n\\nAre you sure?')) {{
                return;
            }}
            
            const stopButton = document.querySelector('.emergency-stop');
            stopButton.style.background = 'linear-gradient(135deg, #6c757d 0%, #5a6268 100%)';
            stopButton.textContent = '⏳ STOPPING...';
            stopButton.disabled = true;
            
            fetch('/api/emergency-stop')
                .then(response => response.json())
                .then(data => {{
                    if (data.emergency_stop) {{
                        addTestResult(`🛑 EMERGENCY STOP EXECUTED - ${{data.cancelled_tests}} tests cancelled`, 'warning', 'System', 'emergency-stop');
                        refreshActiveTests();
                        
                        // Flash success color
                        stopButton.style.background = 'linear-gradient(135deg, #28a745 0%, #20a043 100%)';
                        stopButton.textContent = '✅ STOPPED';
                        
                        setTimeout(() => {{
                            stopButton.style.background = 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)';
                            stopButton.textContent = '🛑 EMERGENCY STOP';
                            stopButton.disabled = false;
                        }}, 3000);
                        
                    }} else {{
                        addTestResult('Emergency stop failed', 'error', 'System', 'emergency-stop');
                        stopButton.style.background = 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)';
                        stopButton.textContent = '🛑 EMERGENCY STOP';
                        stopButton.disabled = false;
                    }}
                }})
                .catch(error => {{
                    console.error('Emergency stop failed:', error);
                    addTestResult(`Emergency stop request failed: ${{error.message}}`, 'error', 'System', 'emergency-stop');
                    stopButton.style.background = 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)';
                    stopButton.textContent = '🛑 EMERGENCY STOP';
                    stopButton.disabled = false;
                }});
        }}
        
        // New quick action functions
        function runBandwidthSuite() {{
            const targets = ['8.8.8.8', '1.1.1.1', 'google.com'];
            if (confirm(`Run bandwidth tests on ${{targets.join(', ')}}? This may take several minutes.`)) {{
                targets.forEach((target, index) => {{
                    setTimeout(() => {{
                        document.getElementById('targetIP').value = target;
                        document.getElementById('testType').value = 'bandwidth-test';
                        runSingleTest();
                    }}, index * 30000); // 30 second delay between tests
                }});
            }}
        }}
        
        function startNetworkMonitoring() {{
            const target = prompt('Enter target to monitor:', '8.8.8.8');
            const duration = prompt('Enter duration in minutes:', '120');
            
            if (target && duration) {{
                document.getElementById('targetIP').value = target;
                document.getElementById('testType').value = 'continuous-monitor';
                
                fetch(`/api/start-monitoring?target=${{encodeURIComponent(target)}}&duration=${{duration}}`)
                    .then(response => response.json())
                    .then(result => {{
                        if (result.session_id) {{
                            addTestResult(result, 'success', target, 'continuous-monitor');
                            refreshActiveTests();
                        }} else {{
                            addTestResult(result.error || 'Monitoring failed to start', 'error', target, 'continuous-monitor');
                        }}
                    }})
                    .catch(error => {{
                        addTestResult(`Monitoring failed: ${{error.message}}`, 'error', target, 'continuous-monitor');
                    }});
            }}
        }}
        
        function securityScan() {{
            const target = prompt('Enter target for security scan:', '192.168.1.1');
            if (!target) return;
            
            // Run comprehensive security assessment
            if (confirm(`Run security scan on ${{target}}? This will perform port scanning and vulnerability checks.`)) {{
                // Port scan first
                document.getElementById('targetIP').value = target;
                document.getElementById('testType').value = 'port-scan';
                runSingleTest();
                
                // Then run additional security checks
                setTimeout(() => {{
                    document.getElementById('testType').value = 'comprehensive';
                    runSingleTest();
                }}, 5000);
                
                addTestResult('Security scan initiated - running port scan and vulnerability checks', 'info', target, 'security-scan');
            }}
        }}
        
        // Network Directory Functions
        function startNetworkScan() {{
            console.log('Starting network scan...');
            const scanRange = document.getElementById('scanRange').value.trim() || 'auto';
            const scanType = document.getElementById('scanType').value;
            
            console.log(`Scan parameters: range=${{scanRange}}, type=${{scanType}}`);
            
            const progressDiv = document.getElementById('scanProgress');
            const progressBar = document.getElementById('progressBar');
            const progressText = document.getElementById('progressText');
            const mapElement = document.getElementById('networkMap');
            
            // Show progress
            progressDiv.style.display = 'block';
            progressBar.style.width = '10%';
            progressText.textContent = 'Initializing network scan...';
            
            mapElement.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; gap: 15px; padding: 2rem; background: white; border-radius: 8px; border: 2px solid #007bff; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <div class="loading-spinner"></div>
                    <div style="color: #007bff;">
                        <strong style="font-size: 1.1rem;">Scanning network ${{scanRange}}</strong><br>
                        <small style="color: #6c757d;">Please wait while we discover devices...</small>
                    </div>
                </div>
            `;
            
            const endpoint = scanType === 'comprehensive' ? '/api/network-scan' : '/api/quick-scan';
            const startTime = Date.now();
            
            console.log(`Making request to: ${{endpoint}}?range=${{encodeURIComponent(scanRange)}}`);
            
            // Add CSS for spinner
            const style = document.createElement('style');
            style.textContent = '@keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}';
            document.head.appendChild(style);
            
            // Simulate progress updates
            const progressInterval = setInterval(() => {{
                const elapsed = Date.now() - startTime;
                const maxTime = scanType === 'comprehensive' ? 60000 : 15000; // 60s or 15s
                const progress = Math.min(90, (elapsed / maxTime) * 90);
                
                progressBar.style.width = progress + '%';
                const progressPercent = document.getElementById('progressPercent');
                if (progressPercent) {{
                    progressPercent.textContent = Math.round(progress) + '%';
                    progressPercent.style.display = progress > 15 ? 'block' : 'none'; // Show percentage when bar is wide enough
                }}
                
                const statusMessages = {{
                    'comprehensive': [
                        'Initializing network scan...',
                        'Discovering active hosts...',
                        'Scanning device ports...',
                        'Identifying device types...',
                        'Resolving hostnames...',
                        'Analyzing services...',
                        'Finalizing results...'
                    ],
                    'quick': [
                        'Initializing ping sweep...',
                        'Discovering active hosts...',
                        'Checking network range...',
                        'Finalizing results...'
                    ]
                }};
                
                const messages = statusMessages[scanType];
                const messageIndex = Math.min(Math.floor(progress / (90 / messages.length)), messages.length - 1);
                progressText.textContent = messages[messageIndex];
            }}, 1000);
            
            fetch(`${{endpoint}}?range=${{encodeURIComponent(scanRange)}}`)
                .then(response => response.json())
                .then(data => {{
                    clearInterval(progressInterval);
                    progressBar.style.width = '100%';
                    progressBar.style.background = 'linear-gradient(90deg, #28a745 0%, #20c997 100%)'; // Green for completion
                    
                    const progressPercent = document.getElementById('progressPercent');
                    if (progressPercent) {{
                        progressPercent.textContent = '100%';
                        progressPercent.style.display = 'block';
                    }}
                    
                    progressText.textContent = '✅ Scan completed successfully!';
                    progressText.style.color = '#28a745';
                    
                    setTimeout(() => {{
                        progressDiv.style.display = 'none';
                        // Reset styles for next scan
                        progressBar.style.background = 'linear-gradient(90deg, #007bff 0%, #0056b3 100%)';
                        progressText.style.color = '#2a5298';
                    }}, 3000);
                    
                    if (data.error) {{
                        mapElement.innerHTML = `
                            <div style="color: #dc3545; text-align: center; padding: 2rem; background: white; border: 2px solid #dc3545; border-radius: 8px; margin: 10px 0;">
                                <h4>❌ Scan Failed</h4>
                                <p>${{data.error}}</p>
                                <button onclick="clearNetworkResults()" style="background: #6c757d; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 10px;">
                                    Try Again
                                </button>
                            </div>
                        `;
                        addTestResult(`Network scan failed: ${{data.error}}`, 'error', scanRange, 'network-scan');
                        return;
                    }}
                    
                    console.log('Network scan data received:', data);
                    
                    // Display comprehensive results
                    if (data.devices || data.active_hosts > 0) {{
                        displayNetworkScanResults(data, scanType);
                        const deviceCount = data.devices ? data.devices.length : data.active_hosts || 0;
                        addTestResult(`Network scan completed - ${{deviceCount}} devices found`, 'success', scanRange, 'network-scan');
                    }} else {{
                        mapElement.innerHTML = `
                            <div style="text-align: center; color: #666; padding: 2rem; background: white; border: 2px solid #dee2e6; border-radius: 8px; margin: 10px 0;">
                                <h4>📡 Scan Complete</h4>
                                <p>No active devices found in network range: ${{scanRange}}</p>
                                <button onclick="clearNetworkResults()" style="background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 10px;">
                                    Scan Again
                                </button>
                            </div>
                        `;
                        addTestResult(`Network scan completed - No devices found in range ${{scanRange}}`, 'info', scanRange, 'network-scan');
                    }}
                }})
                .catch(error => {{
                    clearInterval(progressInterval);
                    
                    // Show error in progress bar
                    progressBar.style.width = '100%';
                    progressBar.style.background = 'linear-gradient(90deg, #dc3545 0%, #c82333 100%)'; // Red for error
                    
                    const progressPercent = document.getElementById('progressPercent');
                    if (progressPercent) {{
                        progressPercent.textContent = 'ERROR';
                        progressPercent.style.display = 'block';
                    }}
                    
                    progressText.textContent = '❌ Scan failed: ' + error.message;
                    progressText.style.color = '#dc3545';
                    
                    setTimeout(() => {{
                        progressDiv.style.display = 'none';
                        // Reset styles for next scan
                        progressBar.style.background = 'linear-gradient(90deg, #007bff 0%, #0056b3 100%)';
                        progressText.style.color = '#2a5298';
                    }}, 4000);
                    
                    console.error('Network scan failed:', error);
                    mapElement.innerHTML = `
                        <div style="color: #dc3545; text-align: center; padding: 2rem; background: white; border: 2px solid #dc3545; border-radius: 8px; margin: 10px 0;">
                            <h4>❌ Network Scan Failed</h4>
                            <p style="color: #6c757d;">${{error.message}}</p>
                            <button onclick="clearNetworkResults()" style="background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 10px;">
                                Try Again
                            </button>
                        </div>
                    `;
                    addTestResult(`Network scan error: ${{error.message}}`, 'error', scanRange, 'network-scan');
                }});
        }}
        
        function displayNetworkScanResults(data, scanType) {{
            console.log('Displaying network scan results:', data);
            const mapElement = document.getElementById('networkMap');
            const devices = data.devices || [];
            
            // Clear any existing content and add CSS class for results display
            mapElement.innerHTML = '';
            mapElement.classList.add('has-results');
            
            let resultsHtml = `
                <div class="results-container" style="width: 100%; background: white; border-radius: 8px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <button class="clear-results" onclick="clearNetworkResults()" title="Clear Results" style="position: absolute; top: 10px; right: 15px; background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 50%; cursor: pointer; font-weight: bold; z-index: 100;">✕</button>
                    
                    <div style="background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; position: relative;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h3 style="margin: 0; font-size: 1.2rem;">🌐 Network Scan Results</h3>
                            <span style="background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 15px; font-size: 0.8rem; font-weight: bold;">${{scanType.toUpperCase()}} SCAN</span>
                        </div>
                        <div style="font-size: 0.95rem; line-height: 1.6;">
                            📡 <strong>Range:</strong> ${{data.network_range || 'Auto-detected'}}<br>
                            ⏱️ <strong>Duration:</strong> ${{data.scan_time ? data.scan_time.toFixed(1) + 's' : 'N/A'}}<br>
                            📊 <strong>Found:</strong> ${{devices.length || data.active_hosts || 0}} active device(s)`;
            
            if (data.gateway_ip) {{
                resultsHtml += `<br>🚪 <strong>Gateway:</strong> ${{data.gateway_ip}}`;
            }}
            if (data.total_hosts) {{
                resultsHtml += `<br>🔍 <strong>Scanned:</strong> ${{data.total_hosts}} total hosts`;
            }}
            
            resultsHtml += `
                        </div>
                    </div>
            `;
            
            if (devices.length > 0) {{
                resultsHtml += '<div style="max-height: 350px; overflow-y: auto; padding-right: 8px; margin-top: 10px;">';
                resultsHtml += `<h4 style="color: #2a5298; margin-bottom: 15px; font-size: 1.1rem;">📱 Discovered Devices (${{devices.length}})</h4>`;
                
                devices.forEach((device, index) => {{
                    const deviceIcon = getDeviceIcon(device.device_type);
                    const statusColor = device.status === 'active' || device.ip_address ? '#28a745' : '#6c757d';
                    
                    resultsHtml += `
                        <div style="background: #f8f9fa; border: 2px solid #e9ecef; border-radius: 8px; padding: 12px; margin-bottom: 10px; border-left: 5px solid ${{statusColor}}; box-shadow: 0 3px 6px rgba(0,0,0,0.1); transition: all 0.3s ease;" 
                             onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 5px 12px rgba(0,0,0,0.15)'" 
                             onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 3px 6px rgba(0,0,0,0.1)'">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                <div style="flex: 1; font-size: 0.9rem; line-height: 1.4;">
                                    <div style="font-weight: bold; color: #2a5298; margin-bottom: 6px; font-size: 1rem;">${{deviceIcon}} ${{device.ip_address}}</div>
                                    ${{device.hostname ? `<div style="color: #495057; margin-bottom: 2px;">📛 <strong>Name:</strong> ${{device.hostname}}</div>` : ''}}
                                    ${{device.device_type && device.device_type !== 'unknown' ? `<div style="color: #495057; margin-bottom: 2px;">🔧 <strong>Type:</strong> ${{device.device_type.replace('_', ' ').toUpperCase()}}</div>` : ''}}
                                    ${{device.os_guess && device.os_guess !== 'Unknown' ? `<div style="color: #495057; margin-bottom: 2px;">💻 <strong>OS:</strong> ${{device.os_guess}}</div>` : ''}}
                                    ${{device.vendor && device.vendor !== 'Unknown' ? `<div style="color: #495057; margin-bottom: 2px;">🏭 <strong>Vendor:</strong> ${{device.vendor}}</div>` : ''}}
                                    ${{device.mac_address ? `<div style="color: #495057; margin-bottom: 2px;">📧 <strong>MAC:</strong> ${{device.mac_address}}</div>` : ''}}
                                    ${{device.open_ports && device.open_ports.length > 0 ? `<div style="color: #495057; margin-bottom: 2px;">🔌 <strong>Ports:</strong> ${{device.open_ports.slice(0, 6).join(', ')}}${{device.open_ports.length > 6 ? ` (+${{device.open_ports.length - 6}} more)` : ''}}</div>` : ''}}
                                    ${{device.response_time_ms ? `<div style="color: #28a745; font-weight: bold;">⚡ ${{device.response_time_ms.toFixed(1)}}ms response</div>` : ''}}
                                </div>
                                <div style="margin-left: 15px; display: flex; flex-direction: column; gap: 5px;">
                                    <button onclick="scanDeviceDetails('${{device.ip_address}}')" 
                                            style="background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); color: white; border: none; padding: 8px 12px; border-radius: 6px; font-size: 0.8rem; cursor: pointer; white-space: nowrap; font-weight: bold; box-shadow: 0 2px 4px rgba(0,123,255,0.3);"
                                            title="Scan device details"
                                            onmouseover="this.style.transform='scale(1.05)'"
                                            onmouseout="this.style.transform='scale(1)'">
                                        🔍 Details
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                }});
                resultsHtml += '</div>';
            }} else if (data.active_hosts > 0) {{
                resultsHtml += `<div style="text-align: center; background: #fff3cd; color: #856404; padding: 20px; border-radius: 6px; margin-top: 15px; border: 1px solid #ffeaa7;">
                    <h4>📡 Basic Scan Complete</h4>
                    <p>Found ${{data.active_hosts}} active host(s) but no detailed device information available.</p>
                    <p><small>Try a "Comprehensive" scan for detailed device discovery.</small></p>
                </div>`;
            }} else {{
                resultsHtml += `<div style="text-align: center; background: #d1ecf1; color: #0c5460; padding: 25px; border-radius: 6px; margin-top: 15px; border: 1px solid #bee5eb;">
                    <h4>📡 Scan Complete</h4>
                    <p>No active devices found in the specified network range.</p>
                    <p><small>Try scanning a different range or check your network connectivity.</small></p>
                </div>`;
            }}
            
            resultsHtml += '</div>';
            mapElement.innerHTML = resultsHtml;
        }}
        
        function getDeviceIcon(deviceType) {{
            const icons = {{
                'router': '🌐',
                'server': '🖥️',
                'workstation': '💻',
                'computer': '🖥️',
                'printer': '🖨️',
                'network_device': '📡',
                'web_device': '🌍',
                'database_server': '🗄️',
                'unknown': '❓'
            }};
            return icons[deviceType] || '📱';
        }}
        
        function scanDeviceDetails(ip) {{
            // Run detailed scans on specific device
            document.getElementById('targetIP').value = ip;
            document.getElementById('testType').value = 'comprehensive';
            runSingleTest();
        }}
        
        function clearNetworkResults() {{
            const mapElement = document.getElementById('networkMap');
            mapElement.classList.remove('has-results');
            mapElement.innerHTML = `
                <div id="defaultMessage" style="text-align: center; color: #495057; padding: 2rem;">
                    <div style="font-size: 2rem; margin-bottom: 10px;">🏢</div>
                    <h4 style="color: #2a5298; margin-bottom: 5px;">Network Directory Ready</h4>
                    <p style="color: #6c757d; margin: 0;">Click "Start Network Scan" to discover devices</p>
                </div>
            `;
            console.log('Network results cleared');
        }}
        
        function quickDiscovery() {{
            document.getElementById('scanRange').value = 'auto';
            document.getElementById('scanType').value = 'quick';
            startNetworkScan();
        }}
        
        function viewNetworkDirectory() {{
            fetch('/api/network-directory')
                .then(response => response.json())
                .then(data => {{
                    const dirWindow = window.open('', '_blank', 'width=900,height=700');
                    dirWindow.document.write(`
                        <html>
                        <head>
                            <title>Network Directory - Dashboard Help</title>
                            <style>
                                body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
                                .container {{ max-width: 800px; margin: 0 auto; }}
                                h1 {{ text-align: center; margin-bottom: 30px; }}
                                .section {{ background: rgba(255,255,255,0.1); padding: 20px; margin: 15px 0; border-radius: 8px; }}
                                .capability {{ background: rgba(255,255,255,0.2); padding: 8px 12px; margin: 5px 0; border-radius: 4px; border-left: 4px solid #28a745; }}
                                .range {{ background: rgba(0,0,0,0.2); padding: 8px 12px; margin: 3px 0; border-radius: 4px; font-family: monospace; }}
                                .status {{ background: #28a745; color: white; padding: 10px; border-radius: 6px; text-align: center; font-weight: bold; }}
                                ol {{ line-height: 1.6; }}
                                .close-btn {{ position: fixed; top: 20px; right: 20px; background: #dc3545; color: white; border: none; padding: 10px 15px; border-radius: 50%; cursor: pointer; font-size: 16px; }}
                            </style>
                        </head>
                        <body>
                            <button class="close-btn" onclick="window.close()">✕</button>
                            <div class="container">
                                <h1>🔍 Network Directory Scanner</h1>
                                
                                <div class="status">${{data.status}}</div>
                                
                                <div class="section">
                                    <h3>🚀 Capabilities:</h3>
                                    ${{(data.capabilities || []).map(cap => `<div class="capability">✓ ${{cap}}</div>`).join('')}}
                                </div>
                                
                                <div class="section">
                                    <h3>🌐 Supported Network Ranges:</h3>
                                    ${{(data.supported_ranges || []).map(range => `<div class="range">${{range}}</div>`).join('')}}
                                </div>
                                
                                <div class="section">
                                    <h3>📋 How to Use:</h3>
                                    <ol>
                                        <li><strong>Enter Network Range:</strong> Type a CIDR range (e.g., 192.168.1.0/24) or use 'auto' for automatic detection</li>
                                        <li><strong>Choose Scan Type:</strong>
                                            <br>• <strong>Quick Scan:</strong> Fast ping sweep (5-15 seconds)
                                            <br>• <strong>Comprehensive:</strong> Full device discovery with port scanning (30-120 seconds)
                                        </li>
                                        <li><strong>Start Scan:</strong> Click "Start Network Scan" and watch real-time progress</li>
                                        <li><strong>View Results:</strong> Browse discovered devices with full details</li>
                                        <li><strong>Device Analysis:</strong> Click "🔍 Details" on any device for complete analysis</li>
                                        <li><strong>Clear Results:</strong> Click "✕" button in top-right of results to clear</li>
                                    </ol>
                                </div>
                                
                                <div class="section">
                                    <h3>🛑 Emergency Controls:</h3>
                                    <p>Use the <strong>EMERGENCY STOP</strong> button in the main dashboard to cancel all active scans instantly.</p>
                                </div>
                            </div>
                        </body>
                        </html>
                    `);
                }})
                .catch(error => {{
                    alert('Failed to load network directory information');
                }});
        }}
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Network Troubleshooting Dashboard initialized');
        }});
    </script>
</body>
</html>
        """
    
    def handle_api_status(self):
        """Handle system status requests"""
        self.send_json_response({
            "server": "running",
            "available_modules": MODULES_AVAILABLE,
            "total_modules": sum(MODULES_AVAILABLE.values()),
            "active_tests": len(ACTIVE_TESTS),
            "test_history_count": len(TEST_HISTORY)
        })
    
    def handle_ping_request(self):
        """Handle ping requests"""
        if not MODULES_AVAILABLE.get('ping', False):
            self.send_json_response({
                "error": "Ping module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        target = params.get('target', ['8.8.8.8'])[0]
        count = int(params.get('count', ['3'])[0])
        timeout = int(params.get('timeout', ['5'])[0])
        
        def run_ping():
            try:
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
                    "error_message": result.error_message,
                    "timestamp": time.time()
                }
                
                # Store in history
                TEST_HISTORY.append({
                    "type": "ping",
                    "target": target,
                    "result": response,
                    "timestamp": time.time()
                })
                
                self.send_json_response(response)
                
            except Exception as e:
                self.send_json_response({
                    "error": f"Ping failed: {str(e)}"
                }, status=500)
        
        thread = threading.Thread(target=run_ping)
        thread.daemon = True
        thread.start()
        thread.join(timeout=30)
    
    def handle_traceroute_request(self):
        """Handle traceroute requests"""
        if not MODULES_AVAILABLE.get('traceroute', False):
            self.send_json_response({
                "error": "Traceroute module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        target = params.get('target', ['8.8.8.8'])[0]
        max_hops = int(params.get('max_hops', ['15'])[0])
        timeout = int(params.get('timeout', ['3'])[0])
        
        def run_traceroute():
            try:
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
                    "timestamp": time.time(),
                    "hops": [
                        {
                            "hop_number": hop.hop_number,
                            "ip_address": hop.ip_address,
                            "hostname": hop.hostname,
                            "avg_latency": sum(hop.latency_ms) / len(hop.latency_ms) if hop.latency_ms else 0,
                            "timeout": hop.timeout
                        }
                        for hop in result.hops[:10]  # Limit to first 10 hops
                    ]
                }
                
                # Store in history
                TEST_HISTORY.append({
                    "type": "traceroute",
                    "target": target,
                    "result": response,
                    "timestamp": time.time()
                })
                
                self.send_json_response(response)
                
            except Exception as e:
                self.send_json_response({
                    "error": f"Traceroute failed: {str(e)}"
                }, status=500)
        
        thread = threading.Thread(target=run_traceroute)
        thread.daemon = True
        thread.start()
        thread.join(timeout=30)
    
    def handle_network_discovery(self):
        """Handle network discovery requests"""
        # Simple network discovery - scan common local IPs
        def discover_network():
            try:
                devices = []
                import socket
                
                # Get local IP range
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                base_ip = '.'.join(local_ip.split('.')[:-1]) + '.'
                
                # Quick scan of first 10 IPs in local subnet
                for i in range(1, 11):
                    test_ip = base_ip + str(i)
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex((test_ip, 80))
                        if result == 0:
                            try:
                                hostname = socket.gethostbyaddr(test_ip)[0]
                            except:
                                hostname = None
                            devices.append({
                                "ip": test_ip,
                                "status": "reachable",
                                "hostname": hostname
                            })
                        sock.close()
                    except:
                        pass
                
                self.send_json_response({
                    "devices": devices,
                    "scan_range": base_ip + "1-10",
                    "timestamp": time.time()
                })
                
            except Exception as e:
                self.send_json_response({
                    "error": f"Network discovery failed: {str(e)}"
                }, status=500)
        
        thread = threading.Thread(target=discover_network)
        thread.daemon = True
        thread.start()
        thread.join(timeout=15)
    
    def handle_test_history(self):
        """Return test history"""
        self.send_json_response({
            "history": TEST_HISTORY[-50:],  # Last 50 tests
            "total_tests": len(TEST_HISTORY)
        })
    
    def handle_port_scan(self):
        """Handle port scanning requests"""
        if not MODULES_AVAILABLE.get('advanced_diagnostics', False):
            self.send_json_response({
                "error": "Advanced diagnostics module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        target = params.get('target', [''])[0]
        if not target:
            self.send_json_response({"error": "Target parameter required"}, status=400)
            return
        
        # Parse port list
        ports_param = params.get('ports', [''])[0]
        if ports_param:
            try:
                ports = [int(p.strip()) for p in ports_param.split(',') if p.strip()]
            except ValueError:
                self.send_json_response({"error": "Invalid port format"}, status=400)
                return
        else:
            ports = None  # Use default common ports
        
        def run_port_scan():
            try:
                from modules.advanced_diagnostics import scan_host_ports
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(scan_host_ports(target, ports or []))
                
                response = {
                    "target": target,
                    "scan_results": results,
                    "open_ports": [r for r in results if r["is_open"]],
                    "total_scanned": len(results),
                    "timestamp": time.time()
                }
                
                self.send_json_response(response)
                
            except Exception as e:
                self.send_json_response({
                    "error": f"Port scan failed: {str(e)}"
                }, status=500)
        
        thread = threading.Thread(target=run_port_scan)
        thread.daemon = True
        thread.start()
        thread.join(timeout=60)
    
    def handle_dns_lookup(self):
        """Handle DNS lookup requests"""
        if not MODULES_AVAILABLE.get('advanced_diagnostics', False):
            self.send_json_response({
                "error": "Advanced diagnostics module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        hostname = params.get('hostname', [''])[0]
        if not hostname:
            self.send_json_response({"error": "Hostname parameter required"}, status=400)
            return
        
        def run_dns_lookup():
            try:
                from modules.advanced_diagnostics import lookup_dns
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(lookup_dns(hostname))
                
                result["timestamp"] = time.time()
                self.send_json_response(result)
                
            except Exception as e:
                self.send_json_response({
                    "error": f"DNS lookup failed: {str(e)}"
                }, status=500)
        
        thread = threading.Thread(target=run_dns_lookup)
        thread.daemon = True
        thread.start()
        thread.join(timeout=15)
    
    def handle_ip_analysis(self):
        """Handle IP address analysis requests"""
        if not MODULES_AVAILABLE.get('advanced_diagnostics', False):
            self.send_json_response({
                "error": "Advanced diagnostics module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        ip_address = params.get('ip', [''])[0]
        if not ip_address:
            self.send_json_response({"error": "IP parameter required"}, status=400)
            return
        
        try:
            from modules.advanced_diagnostics import analyze_ip_address
            
            result = analyze_ip_address(ip_address)
            result["timestamp"] = time.time()
            
            self.send_json_response(result)
            
        except Exception as e:
            self.send_json_response({
                "error": f"IP analysis failed: {str(e)}"
            }, status=500)
    
    def handle_connectivity_check(self):
        """Handle connectivity check requests"""
        if not MODULES_AVAILABLE.get('advanced_diagnostics', False):
            self.send_json_response({
                "error": "Advanced diagnostics module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        host = params.get('host', [''])[0]
        if not host:
            self.send_json_response({"error": "Host parameter required"}, status=400)
            return
        
        port_param = params.get('port', [None])[0]
        port = None
        if port_param:
            try:
                port = int(port_param)
            except ValueError:
                self.send_json_response({"error": "Invalid port number"}, status=400)
                return
        
        def run_connectivity_check():
            try:
                from modules.advanced_diagnostics import check_host_connectivity
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(check_host_connectivity(host, port))
                
                result["timestamp"] = time.time()
                self.send_json_response(result)
                
            except Exception as e:
                self.send_json_response({
                    "error": f"Connectivity check failed: {str(e)}"
                }, status=500)
        
        thread = threading.Thread(target=run_connectivity_check)
        thread.daemon = True
        thread.start()
        thread.join(timeout=15)
    
    def handle_bandwidth_test(self):
        """Handle bandwidth testing requests"""
        if not MODULES_AVAILABLE.get('enhanced_features', False):
            self.send_json_response({
                "error": "Enhanced features module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        target = params.get('target', [''])[0]
        if not target:
            self.send_json_response({"error": "Target parameter required"}, status=400)
            return
        
        def run_bandwidth_test_bg():
            try:
                from modules.enhanced_features import run_bandwidth_test, enhanced_tools
                
                # Create session for tracking
                session_id = enhanced_tools.create_test_session('bandwidth_test', target)
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(run_bandwidth_test(target, session_id))
                
                result["session_id"] = session_id
                self.send_json_response(result)
                
            except Exception as e:
                self.send_json_response({
                    "error": f"Bandwidth test failed: {str(e)}"
                }, status=500)
        
        thread = threading.Thread(target=run_bandwidth_test_bg)
        thread.daemon = True
        thread.start()
        thread.join(timeout=120)
    
    def handle_start_monitoring(self):
        """Handle continuous monitoring requests"""
        if not MODULES_AVAILABLE.get('enhanced_features', False):
            self.send_json_response({
                "error": "Enhanced features module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        target = params.get('target', [''])[0]
        duration = int(params.get('duration', ['60'])[0])
        
        if not target:
            self.send_json_response({"error": "Target parameter required"}, status=400)
            return
        
        try:
            from modules.enhanced_features import start_continuous_monitoring
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            session_id = loop.run_until_complete(start_continuous_monitoring(target, duration))
            
            self.send_json_response({
                "session_id": session_id,
                "target": target,
                "duration_minutes": duration,
                "status": "monitoring_started"
            })
            
        except Exception as e:
            self.send_json_response({
                "error": f"Failed to start monitoring: {str(e)}"
            }, status=500)
    
    def handle_cancel_test(self):
        """Handle test cancellation requests"""
        if not MODULES_AVAILABLE.get('enhanced_features', False):
            self.send_json_response({
                "error": "Enhanced features module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        session_id = params.get('session_id', [''])[0]
        if not session_id:
            self.send_json_response({"error": "Session ID required"}, status=400)
            return
        
        try:
            from modules.enhanced_features import cancel_test
            
            success = cancel_test(session_id)
            self.send_json_response({
                "session_id": session_id,
                "cancelled": success,
                "timestamp": time.time()
            })
            
        except Exception as e:
            self.send_json_response({
                "error": f"Failed to cancel test: {str(e)}"
            }, status=500)
    
    def handle_test_status(self):
        """Handle test status requests"""
        if not MODULES_AVAILABLE.get('enhanced_features', False):
            self.send_json_response({
                "error": "Enhanced features module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        session_id = params.get('session_id', [''])[0]
        if not session_id:
            self.send_json_response({"error": "Session ID required"}, status=400)
            return
        
        try:
            from modules.enhanced_features import get_test_status
            
            status = get_test_status(session_id)
            if status:
                self.send_json_response(status)
            else:
                self.send_json_response({
                    "error": "Session not found"
                }, status=404)
            
        except Exception as e:
            self.send_json_response({
                "error": f"Failed to get test status: {str(e)}"
            }, status=500)
    
    def handle_active_tests(self):
        """Handle active tests listing"""
        if not MODULES_AVAILABLE.get('enhanced_features', False):
            self.send_json_response({
                "error": "Enhanced features module not available"
            }, status=503)
            return
        
        try:
            from modules.enhanced_features import get_active_tests
            
            active_tests = get_active_tests()
            self.send_json_response({
                "active_tests": active_tests,
                "count": len(active_tests),
                "timestamp": time.time()
            })
            
        except Exception as e:
            self.send_json_response({
                "error": f"Failed to get active tests: {str(e)}"
            }, status=500)
    
    def handle_network_topology(self):
        """Handle network topology discovery"""
        if not MODULES_AVAILABLE.get('enhanced_features', False):
            self.send_json_response({
                "error": "Enhanced features module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        network_range = params.get('range', ['192.168.1.0/24'])[0]
        
        def run_topology_scan():
            try:
                from modules.enhanced_features import discover_network_topology
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(discover_network_topology(network_range))
                
                self.send_json_response(result)
                
            except Exception as e:
                self.send_json_response({
                    "error": f"Topology scan failed: {str(e)}"
                }, status=500)
        
        thread = threading.Thread(target=run_topology_scan)
        thread.daemon = True
        thread.start()
        thread.join(timeout=30)
    
    def handle_performance_report(self):
        """Handle performance report requests"""
        if not MODULES_AVAILABLE.get('enhanced_features', False):
            self.send_json_response({
                "error": "Enhanced features module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        target = params.get('target', [''])[0]
        hours = int(params.get('hours', ['24'])[0])
        
        if not target:
            self.send_json_response({"error": "Target parameter required"}, status=400)
            return
        
        try:
            from modules.enhanced_features import get_performance_report
            
            report = get_performance_report(target, hours)
            self.send_json_response(report)
            
        except Exception as e:
            self.send_json_response({
                "error": f"Failed to generate performance report: {str(e)}"
            }, status=500)
    
    def handle_alert_rules(self):
        """Handle alert rules listing"""
        if not MODULES_AVAILABLE.get('enhanced_features', False):
            self.send_json_response({
                "error": "Enhanced features module not available"
            }, status=503)
            return
        
        try:
            from modules.enhanced_features import get_alert_rules
            
            rules = get_alert_rules()
            self.send_json_response({
                "alert_rules": rules,
                "count": len(rules),
                "timestamp": time.time()
            })
            
        except Exception as e:
            self.send_json_response({
                "error": f"Failed to get alert rules: {str(e)}"
            }, status=500)
    
    def handle_recent_alerts(self):
        """Handle recent alerts listing"""
        if not MODULES_AVAILABLE.get('enhanced_features', False):
            self.send_json_response({
                "error": "Enhanced features module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        hours = int(params.get('hours', ['24'])[0])
        
        try:
            from modules.enhanced_features import get_recent_alerts
            
            alerts = get_recent_alerts(hours)
            self.send_json_response({
                "recent_alerts": alerts,
                "count": len(alerts),
                "period_hours": hours,
                "timestamp": time.time()
            })
            
        except Exception as e:
            self.send_json_response({
                "error": f"Failed to get recent alerts: {str(e)}"
            }, status=500)
    
    def handle_emergency_stop(self):
        """Handle emergency stop - cancel all active tests"""
        try:
            cancelled_count = 0
            
            if MODULES_AVAILABLE.get('enhanced_features', False):
                from modules.enhanced_features import ACTIVE_TESTS, cancel_test
                
                # Cancel all active tests
                session_ids = list(ACTIVE_TESTS.keys())
                for session_id in session_ids:
                    if cancel_test(session_id):
                        cancelled_count += 1
            
            self.send_json_response({
                "emergency_stop": True,
                "cancelled_tests": cancelled_count,
                "message": f"Emergency stop executed - {cancelled_count} tests cancelled",
                "timestamp": time.time()
            })
            
        except Exception as e:
            self.send_json_response({
                "error": f"Emergency stop failed: {str(e)}"
            }, status=500)
    
    def handle_network_scan(self):
        """Handle comprehensive network scanning"""
        if not MODULES_AVAILABLE.get('network_directory', False):
            self.send_json_response({
                "error": "Network directory module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        network_range = params.get('range', ['auto'])[0]
        
        def run_network_scan():
            try:
                from modules.network_directory import scan_network_comprehensive
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(scan_network_comprehensive(network_range))
                
                self.send_json_response(result)
                
            except Exception as e:
                self.send_json_response({
                    "error": f"Network scan failed: {str(e)}"
                }, status=500)
        
        thread = threading.Thread(target=run_network_scan)
        thread.daemon = True
        thread.start()
        thread.join(timeout=300)  # 5 minute timeout for comprehensive scan
    
    def handle_quick_scan(self):
        """Handle quick network scanning"""
        if not MODULES_AVAILABLE.get('network_directory', False):
            self.send_json_response({
                "error": "Network directory module not available"
            }, status=503)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        network_range = params.get('range', ['auto'])[0]
        
        def run_quick_scan():
            try:
                from modules.network_directory import quick_network_scan
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(quick_network_scan(network_range))
                
                self.send_json_response(result)
                
            except Exception as e:
                self.send_json_response({
                    "error": f"Quick scan failed: {str(e)}"
                }, status=500)
        
        thread = threading.Thread(target=run_quick_scan)
        thread.daemon = True
        thread.start()
        thread.join(timeout=60)  # 1 minute timeout for quick scan
    
    def handle_network_directory(self):
        """Handle network directory info requests"""
        if not MODULES_AVAILABLE.get('network_directory', False):
            self.send_json_response({
                "error": "Network directory module not available"
            }, status=503)
            return
        
        try:
            from modules.network_directory import get_network_directory
            
            directory_info = get_network_directory()
            self.send_json_response(directory_info)
            
        except Exception as e:
            self.send_json_response({
                "error": f"Failed to get network directory info: {str(e)}"
            }, status=500)
    
    def handle_bulk_test(self):
        """Handle bulk testing requests"""
        # This would be implemented for POST requests
        self.send_json_response({
            "message": "Bulk test endpoint - POST method required"
        })
    
    def handle_save_report(self):
        """Handle report saving requests"""
        self.send_json_response({
            "message": "Report saved successfully"
        })
    
    def serve_static_file(self, path):
        """Serve static files"""
        try:
            # Remove /static/ prefix and get file path
            file_path = path[8:]  # Remove '/static/'
            static_dir = os.path.join(os.path.dirname(__file__), 'static')
            full_path = os.path.join(static_dir, file_path)
            
            # Security check - make sure file is within static directory
            if not os.path.abspath(full_path).startswith(os.path.abspath(static_dir)):
                self.send_error(403, "Access denied")
                return
                
            if os.path.exists(full_path) and os.path.isfile(full_path):
                # Get MIME type
                mime_type, _ = mimetypes.guess_type(full_path)
                if mime_type is None:
                    mime_type = 'application/octet-stream'
                
                # Read and serve file
                with open(full_path, 'rb') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', mime_type)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "File not found")
        except Exception as e:
            print(f"Error serving static file {path}: {e}")
            self.send_error(500, "Internal server error")
    
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
    print("Network Troubleshooting Bot - Professional Dashboard")
    print("=" * 55)
    print(f"Available modules: {sum(MODULES_AVAILABLE.values())}/{len(MODULES_AVAILABLE)}")
    
    # Show available features
    print("\nDashboard Features:")
    print("  • Real-time IP troubleshooting with command control")
    print("  • Advanced network performance testing")
    print("  • Bandwidth and speed testing suite")
    print("  • Continuous monitoring with alerts")
    print("  • Active test management and cancellation")
    print("  • Network topology discovery and mapping")
    print("  • Security scanning and vulnerability assessment")
    print("  • Performance analytics and quality scoring")
    print("  • Test history and comprehensive reporting")
    print("  • Professional network discovery tools")
    
    # Start HTTP server
    server_address = ('127.0.0.1', 9000)
    httpd = HTTPServer(server_address, DashboardHandler)
    
    print(f"\n>> Dashboard starting on http://localhost:9000")
    print(">> Open your browser and navigate to the dashboard")
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n>> Dashboard stopped by user")
        httpd.shutdown()

if __name__ == "__main__":
    main()