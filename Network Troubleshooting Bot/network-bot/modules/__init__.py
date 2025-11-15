"""
Network diagnostic modules
Core functionality for ping, traceroute, SNMP monitoring, SSH execution, and log analysis
"""

# Start with empty lists
__all__ = []

# Core modules - import with error handling
try:
    from .ping_test import PingTester, PingResult, ping_host, ping_multiple
    __all__.extend(['PingTester', 'PingResult', 'ping_host', 'ping_multiple'])
except ImportError as e:
    print(f"Warning: Ping module import failed: {e}")

try:
    from .traceroute import TracerouteTester, TracerouteResult, TracerouteHop, traceroute_host, traceroute_multiple  
    __all__.extend(['TracerouteTester', 'TracerouteResult', 'TracerouteHop', 'traceroute_host', 'traceroute_multiple'])
except ImportError as e:
    print(f"Warning: Traceroute module import failed: {e}")

try:
    from .log_parser import NetworkLogParser, LogEntry, LogAnalysis, LogSeverity, parse_log_content, analyze_log_content, get_critical_events
    __all__.extend(['NetworkLogParser', 'LogEntry', 'LogAnalysis', 'LogSeverity', 'parse_log_content', 'analyze_log_content', 'get_critical_events'])
except ImportError as e:
    print(f"Warning: Log parser module import failed: {e}")

# Optional modules with graceful degradation
try:
    from .snmp_monitor import SNMPMonitor, SNMPResult, DeviceInfo, InterfaceStats, get_device_snmp_info, monitor_devices
    __all__.extend(['SNMPMonitor', 'SNMPResult', 'DeviceInfo', 'InterfaceStats', 'get_device_snmp_info', 'monitor_devices'])
except ImportError:
    # SNMP functionality not available - requires pysnmp
    pass

try:
    from .ssh_exec import SSHExecutor, SSHResult, DeviceCredentials, NetworkDeviceAutomation, execute_ssh_command, restart_device_interface
    __all__.extend(['SSHExecutor', 'SSHResult', 'DeviceCredentials', 'NetworkDeviceAutomation', 'execute_ssh_command', 'restart_device_interface'])
except ImportError:
    # SSH functionality not available - requires paramiko/netmiko  
    pass