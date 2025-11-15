#!/usr/bin/env python3
"""
Enhanced Network Troubleshooting Features
Additional advanced capabilities for professional network diagnostics
"""

import asyncio
import time
import threading
import json
import statistics
import subprocess
import platform
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid

# Global test management
ACTIVE_TESTS = {}
TEST_QUEUE = []
MONITORING_SESSIONS = {}
ALERT_RULES = []
PERFORMANCE_HISTORY = []

@dataclass
class TestSession:
    """Represents an active test session"""
    session_id: str
    test_type: str
    target: str
    status: str  # 'running', 'completed', 'cancelled', 'failed'
    start_time: float
    end_time: Optional[float] = None
    progress: int = 0  # 0-100
    results: Optional[Dict] = None
    cancellation_token: Optional[threading.Event] = None

@dataclass
class BandwidthResult:
    """Bandwidth test result"""
    target: str
    download_mbps: float
    upload_mbps: float
    latency_ms: float
    jitter_ms: float
    packet_loss: float
    test_duration_seconds: float
    timestamp: float

@dataclass
class PerformanceMetrics:
    """Network performance metrics"""
    target: str
    avg_latency: float
    min_latency: float
    max_latency: float
    jitter: float
    packet_loss_rate: float
    availability: float
    quality_score: float  # 0-100
    timestamp: float

@dataclass
class AlertRule:
    """Alert configuration"""
    rule_id: str
    name: str
    target: str
    metric: str  # 'latency', 'packet_loss', 'availability'
    threshold: float
    operator: str  # '>', '<', '>=', '<=', '=='
    enabled: bool = True
    last_triggered: Optional[float] = None

class EnhancedNetworkTools:
    """Enhanced network diagnostic capabilities"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.active_sessions = {}
    
    def create_test_session(self, test_type: str, target: str) -> str:
        """Create a new test session with cancellation support"""
        session_id = str(uuid.uuid4())
        cancellation_token = threading.Event()
        
        session = TestSession(
            session_id=session_id,
            test_type=test_type,
            target=target,
            status='running',
            start_time=time.time(),
            cancellation_token=cancellation_token
        )
        
        ACTIVE_TESTS[session_id] = session
        return session_id
    
    def cancel_test_session(self, session_id: str) -> bool:
        """Cancel an active test session"""
        if session_id in ACTIVE_TESTS:
            session = ACTIVE_TESTS[session_id]
            if session.cancellation_token:
                session.cancellation_token.set()
            session.status = 'cancelled'
            session.end_time = time.time()
            return True
        return False
    
    def get_test_status(self, session_id: str) -> Optional[Dict]:
        """Get status of a test session"""
        if session_id in ACTIVE_TESTS:
            session = ACTIVE_TESTS[session_id]
            return {
                'session_id': session.session_id,
                'test_type': session.test_type,
                'target': session.target,
                'status': session.status,
                'progress': session.progress,
                'start_time': session.start_time,
                'end_time': session.end_time,
                'duration': (session.end_time or time.time()) - session.start_time
            }
        return None
    
    async def bandwidth_test(self, target: str, session_id: str = None) -> BandwidthResult:
        """Perform bandwidth testing"""
        start_time = time.time()
        session = ACTIVE_TESTS.get(session_id) if session_id else None
        
        try:
            # Update progress
            if session:
                session.progress = 25
            
            # Simulate download test with multiple connections
            download_speeds = []
            for i in range(3):
                if session and session.cancellation_token.is_set():
                    raise asyncio.CancelledError("Test cancelled by user")
                
                # Simulate download measurement
                await asyncio.sleep(0.5)  # Simulate test time
                download_speeds.append(50.0 + (i * 10))  # Mock data
                
                if session:
                    session.progress = 25 + (i * 15)
            
            # Update progress
            if session:
                session.progress = 70
            
            # Simulate upload test
            upload_speeds = []
            for i in range(2):
                if session and session.cancellation_token.is_set():
                    raise asyncio.CancelledError("Test cancelled by user")
                
                await asyncio.sleep(0.3)
                upload_speeds.append(25.0 + (i * 5))
                
                if session:
                    session.progress = 70 + (i * 10)
            
            # Calculate metrics
            avg_download = statistics.mean(download_speeds)
            avg_upload = statistics.mean(upload_speeds)
            latency = 15.5  # Mock latency
            jitter = 2.3   # Mock jitter
            packet_loss = 0.1  # Mock packet loss
            
            if session:
                session.progress = 100
                session.status = 'completed'
                session.end_time = time.time()
            
            result = BandwidthResult(
                target=target,
                download_mbps=avg_download,
                upload_mbps=avg_upload,
                latency_ms=latency,
                jitter_ms=jitter,
                packet_loss=packet_loss,
                test_duration_seconds=time.time() - start_time,
                timestamp=time.time()
            )
            
            # Store in history
            PERFORMANCE_HISTORY.append(result)
            
            return result
            
        except asyncio.CancelledError:
            if session:
                session.status = 'cancelled'
                session.end_time = time.time()
            raise
        except Exception as e:
            if session:
                session.status = 'failed'
                session.end_time = time.time()
            raise
    
    async def continuous_latency_monitor(self, target: str, duration_minutes: int = 60) -> List[PerformanceMetrics]:
        """Continuous latency monitoring with quality assessment"""
        results = []
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            try:
                # Perform ping test
                latencies = []
                for i in range(10):  # 10 pings per sample
                    # Mock ping implementation
                    await asyncio.sleep(0.1)
                    latency = 20.0 + (i * 0.5)  # Mock latency data
                    latencies.append(latency)
                
                # Calculate metrics
                avg_latency = statistics.mean(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)
                jitter = statistics.stdev(latencies) if len(latencies) > 1 else 0
                packet_loss = 0.0  # Mock packet loss
                availability = 100.0  # Mock availability
                
                # Calculate quality score (0-100)
                quality_score = self._calculate_quality_score(
                    avg_latency, jitter, packet_loss, availability
                )
                
                metrics = PerformanceMetrics(
                    target=target,
                    avg_latency=avg_latency,
                    min_latency=min_latency,
                    max_latency=max_latency,
                    jitter=jitter,
                    packet_loss_rate=packet_loss,
                    availability=availability,
                    quality_score=quality_score,
                    timestamp=time.time()
                )
                
                results.append(metrics)
                
                # Check alert rules
                self._check_alert_rules(target, metrics)
                
                # Wait for next sample (30 seconds)
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                break
        
        return results
    
    def _calculate_quality_score(self, latency: float, jitter: float, 
                                packet_loss: float, availability: float) -> float:
        """Calculate network quality score (0-100)"""
        # Scoring algorithm based on network performance metrics
        latency_score = max(0, 100 - (latency * 2))  # Lower latency = higher score
        jitter_score = max(0, 100 - (jitter * 10))   # Lower jitter = higher score
        loss_score = max(0, 100 - (packet_loss * 20)) # Lower loss = higher score
        availability_score = availability
        
        # Weighted average
        quality_score = (
            latency_score * 0.3 +
            jitter_score * 0.2 +
            loss_score * 0.3 +
            availability_score * 0.2
        )
        
        return min(100, max(0, quality_score))
    
    def _check_alert_rules(self, target: str, metrics: PerformanceMetrics):
        """Check if any alert rules are triggered"""
        current_time = time.time()
        
        for rule in ALERT_RULES:
            if not rule.enabled or rule.target != target:
                continue
            
            # Avoid spamming alerts (minimum 5 minutes between same rule triggers)
            if rule.last_triggered and (current_time - rule.last_triggered) < 300:
                continue
            
            metric_value = getattr(metrics, rule.metric, None)
            if metric_value is None:
                continue
            
            triggered = False
            if rule.operator == '>':
                triggered = metric_value > rule.threshold
            elif rule.operator == '<':
                triggered = metric_value < rule.threshold
            elif rule.operator == '>=':
                triggered = metric_value >= rule.threshold
            elif rule.operator == '<=':
                triggered = metric_value <= rule.threshold
            elif rule.operator == '==':
                triggered = abs(metric_value - rule.threshold) < 0.001
            
            if triggered:
                rule.last_triggered = current_time
                self._send_alert(rule, target, metric_value)
    
    def _send_alert(self, rule: AlertRule, target: str, value: float):
        """Send alert notification"""
        alert = {
            'rule_name': rule.name,
            'target': target,
            'metric': rule.metric,
            'value': value,
            'threshold': rule.threshold,
            'timestamp': time.time(),
            'severity': 'critical' if value > rule.threshold * 2 else 'warning'
        }
        
        # In a real implementation, this would send email/SMS/webhook
        print(f"ALERT: {rule.name} - {target} {rule.metric}={value} (threshold: {rule.threshold})")
    
    async def network_topology_scan(self, network_range: str = "192.168.1.0/24") -> Dict:
        """Advanced network topology discovery"""
        devices = []
        network_info = {
            'range': network_range,
            'scan_time': time.time(),
            'devices': [],
            'topology': {}
        }
        
        # Simulate network scanning
        base_ip = "192.168.1."
        for i in range(1, 255, 10):  # Sample every 10th IP for demo
            ip = base_ip + str(i)
            
            # Mock device discovery
            device_info = {
                'ip': ip,
                'mac': f"00:1A:2B:3C:4D:{i:02X}",
                'hostname': f"device-{i}",
                'os': 'Unknown',
                'open_ports': [22, 80, 443] if i % 3 == 0 else [80],
                'device_type': 'router' if i == 1 else 'computer',
                'vendor': 'Unknown',
                'last_seen': time.time()
            }
            
            devices.append(device_info)
            
            # Simulate scan delay
            await asyncio.sleep(0.1)
        
        network_info['devices'] = devices
        return network_info
    
    def create_alert_rule(self, name: str, target: str, metric: str, 
                         threshold: float, operator: str = '>') -> str:
        """Create a new alert rule"""
        rule_id = str(uuid.uuid4())
        rule = AlertRule(
            rule_id=rule_id,
            name=name,
            target=target,
            metric=metric,
            threshold=threshold,
            operator=operator
        )
        ALERT_RULES.append(rule)
        return rule_id
    
    def get_performance_summary(self, target: str, hours: int = 24) -> Dict:
        """Get performance summary for a target"""
        cutoff_time = time.time() - (hours * 3600)
        
        # Filter recent performance data
        recent_data = [
            metric for metric in PERFORMANCE_HISTORY 
            if hasattr(metric, 'target') and metric.target == target and 
               hasattr(metric, 'timestamp') and metric.timestamp > cutoff_time
        ]
        
        if not recent_data:
            return {'error': 'No recent performance data available'}
        
        # Calculate summary statistics
        latencies = [m.avg_latency for m in recent_data if hasattr(m, 'avg_latency')]
        quality_scores = [m.quality_score for m in recent_data if hasattr(m, 'quality_score')]
        
        summary = {
            'target': target,
            'period_hours': hours,
            'sample_count': len(recent_data),
            'avg_latency': statistics.mean(latencies) if latencies else 0,
            'min_latency': min(latencies) if latencies else 0,
            'max_latency': max(latencies) if latencies else 0,
            'avg_quality_score': statistics.mean(quality_scores) if quality_scores else 0,
            'uptime_percentage': 99.5,  # Mock uptime
            'incidents_count': 2,       # Mock incidents
            'last_updated': time.time()
        }
        
        return summary

# Global instance
enhanced_tools = EnhancedNetworkTools()

# Convenience functions for API use
async def run_bandwidth_test(target: str, session_id: str = None) -> Dict:
    """Run bandwidth test with session management"""
    result = await enhanced_tools.bandwidth_test(target, session_id)
    return asdict(result)

async def start_continuous_monitoring(target: str, duration_minutes: int = 60) -> str:
    """Start continuous monitoring session"""
    session_id = enhanced_tools.create_test_session('continuous_monitor', target)
    
    # Run monitoring in background
    async def monitor():
        try:
            await enhanced_tools.continuous_latency_monitor(target, duration_minutes)
        except Exception as e:
            print(f"Monitoring failed: {e}")
    
    # Start monitoring task
    asyncio.create_task(monitor())
    return session_id

def cancel_test(session_id: str) -> bool:
    """Cancel a running test"""
    return enhanced_tools.cancel_test_session(session_id)

def get_test_status(session_id: str) -> Optional[Dict]:
    """Get test status"""
    return enhanced_tools.get_test_status(session_id)

async def discover_network_topology(network_range: str = "192.168.1.0/24") -> Dict:
    """Discover network topology"""
    return await enhanced_tools.network_topology_scan(network_range)

def create_performance_alert(name: str, target: str, metric: str, 
                           threshold: float, operator: str = '>') -> str:
    """Create performance alert rule"""
    return enhanced_tools.create_alert_rule(name, target, metric, threshold, operator)

def get_performance_report(target: str, hours: int = 24) -> Dict:
    """Get performance summary report"""
    return enhanced_tools.get_performance_summary(target, hours)

def get_active_tests() -> List[Dict]:
    """Get all active test sessions"""
    return [
        enhanced_tools.get_test_status(session_id) 
        for session_id in ACTIVE_TESTS.keys()
    ]

def get_alert_rules() -> List[Dict]:
    """Get all alert rules"""
    return [asdict(rule) for rule in ALERT_RULES]

def get_recent_alerts(hours: int = 24) -> List[Dict]:
    """Get recent alerts"""
    cutoff_time = time.time() - (hours * 3600)
    # Mock alerts for demonstration
    return [
        {
            'alert_id': '1',
            'rule_name': 'High Latency Alert',
            'target': '8.8.8.8',
            'metric': 'avg_latency',
            'value': 150.5,
            'threshold': 100.0,
            'severity': 'warning',
            'timestamp': time.time() - 3600
        }
    ]