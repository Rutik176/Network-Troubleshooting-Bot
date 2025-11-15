"""
Log Parser Module for Network Troubleshooting Bot
Analyzes network device logs to identify issues and patterns
"""
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class LogSeverity(Enum):
    EMERGENCY = 0    # System is unusable
    ALERT = 1        # Action must be taken immediately
    CRITICAL = 2     # Critical conditions
    ERROR = 3        # Error conditions
    WARNING = 4      # Warning conditions
    NOTICE = 5       # Normal but significant condition
    INFO = 6         # Informational messages
    DEBUG = 7        # Debug-level messages

@dataclass
class LogEntry:
    timestamp: datetime
    severity: LogSeverity
    facility: str
    hostname: str
    process: str
    message: str
    raw_line: str
    parsed_data: Dict[str, Any]

@dataclass
class LogAnalysis:
    total_entries: int
    time_range: Tuple[datetime, datetime]
    severity_counts: Dict[LogSeverity, int]
    top_error_patterns: List[Dict[str, Any]]
    interface_issues: List[Dict[str, Any]]
    routing_issues: List[Dict[str, Any]]
    security_events: List[Dict[str, Any]]
    performance_issues: List[Dict[str, Any]]
    recommendations: List[str]

class NetworkLogParser:
    def __init__(self):
        self.syslog_pattern = re.compile(
            r'(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+)\s+'
            r'(?P<hostname>\S+)\s+'
            r'(?P<process>\S+?):\s*'
            r'(?:%(?P<facility>\w+)-(?P<severity>\d+)-(?P<mnemonic>\w+):\s*)?'
            r'(?P<message>.*)'
        )
        
        # Common network error patterns
        self.error_patterns = {
            'interface_down': [
                r'Interface\s+(\S+)\s+.*down',
                r'%LINK-\d+-UPDOWN:.*Interface\s+(\S+).*down',
                r'(\S+)\s+changed state to down'
            ],
            'interface_up': [
                r'Interface\s+(\S+)\s+.*up',
                r'%LINK-\d+-UPDOWN:.*Interface\s+(\S+).*up',
                r'(\S+)\s+changed state to up'
            ],
            'high_cpu': [
                r'CPU utilization.*(\d+)%',
                r'High CPU detected.*(\d+)%'
            ],
            'memory_issues': [
                r'Memory.*low',
                r'Out of memory',
                r'Memory allocation failed'
            ],
            'routing_issues': [
                r'BGP.*neighbor.*down',
                r'OSPF.*neighbor.*down',
                r'Routing table.*full',
                r'No route to host'
            ],
            'authentication_failure': [
                r'Authentication failed',
                r'Login failed',
                r'Invalid.*credentials',
                r'Access denied'
            ],
            'port_security': [
                r'Port security violation',
                r'Security violation.*port',
                r'MAC address violation'
            ],
            'spanning_tree': [
                r'STP.*topology change',
                r'Spanning tree.*blocked',
                r'Root bridge.*changed'
            ],
            'dhcp_issues': [
                r'DHCP.*pool.*exhausted',
                r'DHCP.*lease.*expired',
                r'DHCP server.*unreachable'
            ],
            'dns_issues': [
                r'DNS.*resolution failed',
                r'DNS server.*timeout',
                r'Name resolution.*failed'
            ]
        }
        
        # Performance indicators
        self.performance_patterns = {
            'high_latency': [
                r'Latency.*(\d+)ms',
                r'RTT.*(\d+)ms'
            ],
            'packet_loss': [
                r'Packet loss.*(\d+)%',
                r'(\d+)%.*packet.*loss'
            ],
            'bandwidth_utilization': [
                r'Bandwidth.*(\d+)%',
                r'Utilization.*(\d+)%'
            ]
        }
    
    def parse_log_file(self, log_content: str, log_format: str = 'syslog') -> List[LogEntry]:
        """
        Parse log file content and return structured log entries
        """
        entries = []
        lines = log_content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
            
            try:
                if log_format == 'syslog':
                    entry = self._parse_syslog_line(line)
                elif log_format == 'cisco':
                    entry = self._parse_cisco_log_line(line)
                elif log_format == 'juniper':
                    entry = self._parse_juniper_log_line(line)
                else:
                    entry = self._parse_generic_log_line(line)
                
                if entry:
                    entries.append(entry)
                    
            except Exception as e:
                logger.warning(f"Failed to parse line {line_num}: {str(e)}")
        
        return entries
    
    def _parse_syslog_line(self, line: str) -> Optional[LogEntry]:
        """Parse standard syslog format"""
        match = self.syslog_pattern.match(line)
        if not match:
            return None
        
        groups = match.groupdict()
        
        # Parse timestamp
        timestamp_str = groups['timestamp']
        try:
            # Assume current year if not specified
            current_year = datetime.now().year
            timestamp = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
        except ValueError:
            timestamp = datetime.now()
        
        # Parse severity
        severity_num = groups.get('severity')
        if severity_num:
            try:
                severity = LogSeverity(int(severity_num))
            except ValueError:
                severity = LogSeverity.INFO
        else:
            severity = LogSeverity.INFO
        
        # Extract additional data
        parsed_data = {}
        if groups.get('mnemonic'):
            parsed_data['mnemonic'] = groups['mnemonic']
        if groups.get('facility'):
            parsed_data['facility'] = groups['facility']
        
        return LogEntry(
            timestamp=timestamp,
            severity=severity,
            facility=groups.get('facility', 'unknown'),
            hostname=groups['hostname'],
            process=groups['process'],
            message=groups['message'],
            raw_line=line,
            parsed_data=parsed_data
        )
    
    def _parse_cisco_log_line(self, line: str) -> Optional[LogEntry]:
        """Parse Cisco-specific log format"""
        # Cisco format: timestamp: %FACILITY-SEVERITY-MNEMONIC: message
        cisco_pattern = re.compile(
            r'(?P<timestamp>\*?\w+\s+\d+\s+\d+:\d+:\d+(?:\.\d+)?)\s*:\s*'
            r'%(?P<facility>\w+)-(?P<severity>\d+)-(?P<mnemonic>\w+):\s*'
            r'(?P<message>.*)'
        )
        
        match = cisco_pattern.match(line)
        if not match:
            return self._parse_generic_log_line(line)
        
        groups = match.groupdict()
        
        # Parse timestamp
        timestamp_str = groups['timestamp'].lstrip('*')
        try:
            current_year = datetime.now().year
            timestamp = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
        except ValueError:
            try:
                timestamp = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S.%f")
            except ValueError:
                timestamp = datetime.now()
        
        # Parse severity
        try:
            severity = LogSeverity(int(groups['severity']))
        except ValueError:
            severity = LogSeverity.INFO
        
        return LogEntry(
            timestamp=timestamp,
            severity=severity,
            facility=groups['facility'],
            hostname='cisco_device',  # Often not included in Cisco logs
            process=groups['mnemonic'],
            message=groups['message'],
            raw_line=line,
            parsed_data={
                'mnemonic': groups['mnemonic'],
                'facility': groups['facility']
            }
        )
    
    def _parse_juniper_log_line(self, line: str) -> Optional[LogEntry]:
        """Parse Juniper-specific log format"""
        # Juniper format: timestamp hostname process[pid]: message
        juniper_pattern = re.compile(
            r'(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+)\s+'
            r'(?P<hostname>\S+)\s+'
            r'(?P<process>\w+)(?:\[(?P<pid>\d+)\])?\s*:\s*'
            r'(?P<message>.*)'
        )
        
        match = juniper_pattern.match(line)
        if not match:
            return self._parse_generic_log_line(line)
        
        groups = match.groupdict()
        
        # Parse timestamp
        timestamp_str = groups['timestamp']
        try:
            current_year = datetime.now().year
            timestamp = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
        except ValueError:
            timestamp = datetime.now()
        
        # Determine severity from message content
        message = groups['message'].lower()
        if any(keyword in message for keyword in ['error', 'fail', 'critical']):
            severity = LogSeverity.ERROR
        elif any(keyword in message for keyword in ['warn', 'warning']):
            severity = LogSeverity.WARNING
        else:
            severity = LogSeverity.INFO
        
        return LogEntry(
            timestamp=timestamp,
            severity=severity,
            facility='juniper',
            hostname=groups['hostname'],
            process=groups['process'],
            message=groups['message'],
            raw_line=line,
            parsed_data={'pid': groups.get('pid')}
        )
    
    def _parse_generic_log_line(self, line: str) -> Optional[LogEntry]:
        """Parse generic log format as fallback"""
        return LogEntry(
            timestamp=datetime.now(),
            severity=LogSeverity.INFO,
            facility='unknown',
            hostname='unknown',
            process='unknown',
            message=line,
            raw_line=line,
            parsed_data={}
        )
    
    def analyze_logs(self, log_entries: List[LogEntry], 
                    time_window_hours: int = 24) -> LogAnalysis:
        """
        Analyze parsed log entries for issues and patterns
        """
        if not log_entries:
            return self._empty_analysis()
        
        # Filter by time window
        end_time = max(entry.timestamp for entry in log_entries)
        start_time = end_time - timedelta(hours=time_window_hours)
        filtered_entries = [
            entry for entry in log_entries 
            if start_time <= entry.timestamp <= end_time
        ]
        
        if not filtered_entries:
            return self._empty_analysis()
        
        # Count severities
        severity_counts = {}
        for severity in LogSeverity:
            severity_counts[severity] = sum(
                1 for entry in filtered_entries if entry.severity == severity
            )
        
        # Find error patterns
        error_patterns = self._find_error_patterns(filtered_entries)
        
        # Analyze specific issue types
        interface_issues = self._analyze_interface_issues(filtered_entries)
        routing_issues = self._analyze_routing_issues(filtered_entries)
        security_events = self._analyze_security_events(filtered_entries)
        performance_issues = self._analyze_performance_issues(filtered_entries)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            severity_counts, error_patterns, interface_issues, 
            routing_issues, security_events, performance_issues
        )
        
        return LogAnalysis(
            total_entries=len(filtered_entries),
            time_range=(start_time, end_time),
            severity_counts=severity_counts,
            top_error_patterns=error_patterns,
            interface_issues=interface_issues,
            routing_issues=routing_issues,
            security_events=security_events,
            performance_issues=performance_issues,
            recommendations=recommendations
        )
    
    def _find_error_patterns(self, log_entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Find common error patterns in logs"""
        pattern_counts = {}
        
        for entry in log_entries:
            if entry.severity in [LogSeverity.ERROR, LogSeverity.CRITICAL, LogSeverity.ALERT]:
                # Check against known patterns
                for category, patterns in self.error_patterns.items():
                    for pattern in patterns:
                        matches = re.findall(pattern, entry.message, re.IGNORECASE)
                        if matches:
                            key = f"{category}:{pattern}"
                            if key not in pattern_counts:
                                pattern_counts[key] = {
                                    'category': category,
                                    'pattern': pattern,
                                    'count': 0,
                                    'examples': [],
                                    'affected_devices': set()
                                }
                            pattern_counts[key]['count'] += 1
                            pattern_counts[key]['examples'].append(entry.message)
                            pattern_counts[key]['affected_devices'].add(entry.hostname)
        
        # Convert to list and sort by count
        error_patterns = []
        for pattern_data in pattern_counts.values():
            pattern_data['affected_devices'] = list(pattern_data['affected_devices'])
            pattern_data['examples'] = pattern_data['examples'][:5]  # Limit examples
            error_patterns.append(pattern_data)
        
        return sorted(error_patterns, key=lambda x: x['count'], reverse=True)[:10]
    
    def _analyze_interface_issues(self, log_entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Analyze interface-related issues"""
        interface_events = {}
        
        for entry in log_entries:
            # Check for interface up/down events
            for pattern in self.error_patterns['interface_down'] + self.error_patterns['interface_up']:
                matches = re.findall(pattern, entry.message, re.IGNORECASE)
                for match in matches:
                    interface = match if isinstance(match, str) else match[0]
                    if interface not in interface_events:
                        interface_events[interface] = {
                            'interface': interface,
                            'down_events': 0,
                            'up_events': 0,
                            'last_event': None,
                            'flapping': False
                        }
                    
                    if 'down' in entry.message.lower():
                        interface_events[interface]['down_events'] += 1
                    elif 'up' in entry.message.lower():
                        interface_events[interface]['up_events'] += 1
                    
                    interface_events[interface]['last_event'] = entry.timestamp
        
        # Detect interface flapping
        for interface_data in interface_events.values():
            total_events = interface_data['down_events'] + interface_data['up_events']
            if total_events > 10:  # Threshold for flapping detection
                interface_data['flapping'] = True
        
        return list(interface_events.values())
    
    def _analyze_routing_issues(self, log_entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Analyze routing-related issues"""
        routing_issues = []
        
        for entry in log_entries:
            for pattern in self.error_patterns['routing_issues']:
                if re.search(pattern, entry.message, re.IGNORECASE):
                    routing_issues.append({
                        'timestamp': entry.timestamp,
                        'hostname': entry.hostname,
                        'message': entry.message,
                        'severity': entry.severity.name
                    })
        
        return routing_issues
    
    def _analyze_security_events(self, log_entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Analyze security-related events"""
        security_events = []
        
        security_patterns = (
            self.error_patterns['authentication_failure'] + 
            self.error_patterns['port_security']
        )
        
        for entry in log_entries:
            for pattern in security_patterns:
                if re.search(pattern, entry.message, re.IGNORECASE):
                    security_events.append({
                        'timestamp': entry.timestamp,
                        'hostname': entry.hostname,
                        'message': entry.message,
                        'severity': entry.severity.name,
                        'type': 'authentication' if 'auth' in pattern.lower() else 'port_security'
                    })
        
        return security_events
    
    def _analyze_performance_issues(self, log_entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Analyze performance-related issues"""
        performance_issues = []
        
        for entry in log_entries:
            for issue_type, patterns in self.performance_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, entry.message, re.IGNORECASE)
                    for match in matches:
                        value = match if isinstance(match, str) else match[0]
                        try:
                            numeric_value = float(value)
                            performance_issues.append({
                                'timestamp': entry.timestamp,
                                'hostname': entry.hostname,
                                'type': issue_type,
                                'value': numeric_value,
                                'message': entry.message
                            })
                        except ValueError:
                            continue
        
        return performance_issues
    
    def _generate_recommendations(self, severity_counts, error_patterns, 
                                interface_issues, routing_issues, security_events, 
                                performance_issues) -> List[str]:
        """Generate troubleshooting recommendations based on analysis"""
        recommendations = []
        
        # High severity issues
        critical_count = severity_counts.get(LogSeverity.CRITICAL, 0)
        error_count = severity_counts.get(LogSeverity.ERROR, 0)
        
        if critical_count > 0:
            recommendations.append(f"CRITICAL: {critical_count} critical events detected. Immediate attention required.")
        
        if error_count > 10:
            recommendations.append(f"HIGH: {error_count} error events in the analyzed period. Review error patterns.")
        
        # Interface issues
        flapping_interfaces = [iface for iface in interface_issues if iface.get('flapping')]
        if flapping_interfaces:
            recommendations.append(f"Interface flapping detected on {len(flapping_interfaces)} interfaces. Check physical connections.")
        
        # Routing issues
        if routing_issues:
            recommendations.append(f"{len(routing_issues)} routing issues detected. Verify neighbor relationships and routing configuration.")
        
        # Security events
        if security_events:
            auth_failures = [event for event in security_events if event.get('type') == 'authentication']
            if len(auth_failures) > 5:
                recommendations.append(f"Multiple authentication failures detected. Possible security threat.")
        
        # Performance issues
        high_cpu_issues = [issue for issue in performance_issues if issue.get('type') == 'high_cpu' and issue.get('value', 0) > 90]
        if high_cpu_issues:
            recommendations.append("High CPU utilization detected. Review running processes and optimize configuration.")
        
        # Top error patterns
        if error_patterns and len(error_patterns[0].get('examples', [])) > 5:
            top_pattern = error_patterns[0]
            recommendations.append(f"Most frequent error: {top_pattern['category']} ({top_pattern['count']} occurrences)")
        
        if not recommendations:
            recommendations.append("No critical issues detected in the analyzed logs.")
        
        return recommendations
    
    def _empty_analysis(self) -> LogAnalysis:
        """Return empty analysis result"""
        return LogAnalysis(
            total_entries=0,
            time_range=(datetime.now(), datetime.now()),
            severity_counts={severity: 0 for severity in LogSeverity},
            top_error_patterns=[],
            interface_issues=[],
            routing_issues=[],
            security_events=[],
            performance_issues=[],
            recommendations=["No log entries found to analyze."]
        )

# Convenience functions
def parse_log_content(log_content: str, log_format: str = 'syslog') -> List[LogEntry]:
    """Parse log content and return entries"""
    parser = NetworkLogParser()
    return parser.parse_log_file(log_content, log_format)

def analyze_log_content(log_content: str, log_format: str = 'syslog', 
                       time_window_hours: int = 24) -> LogAnalysis:
    """Parse and analyze log content in one step"""
    parser = NetworkLogParser()
    entries = parser.parse_log_file(log_content, log_format)
    return parser.analyze_logs(entries, time_window_hours)

def get_critical_events(log_entries: List[LogEntry]) -> List[LogEntry]:
    """Get only critical and error events"""
    return [
        entry for entry in log_entries 
        if entry.severity in [LogSeverity.CRITICAL, LogSeverity.ERROR, LogSeverity.ALERT]
    ]