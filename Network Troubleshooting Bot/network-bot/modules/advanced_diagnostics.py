#!/usr/bin/env python3
"""
Advanced Network Diagnostic Tools
Additional modules for comprehensive IP troubleshooting
"""

import asyncio
import socket
import subprocess
import json
import time
import platform
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import concurrent.futures
import ipaddress

@dataclass
class PortScanResult:
    """Result of a port scan"""
    host: str
    port: int
    is_open: bool
    service: Optional[str] = None
    response_time_ms: Optional[float] = None

@dataclass
class DNSLookupResult:
    """Result of DNS lookup"""
    hostname: str
    ip_addresses: List[str]
    mx_records: List[str]
    ns_records: List[str]
    success: bool
    error_message: Optional[str] = None

class AdvancedNetworkTools:
    """Advanced network diagnostic tools"""
    
    def __init__(self):
        self.common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 993, 995, 1433, 1521, 3389, 5432, 8080]
        self.service_map = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
            80: "HTTP", 110: "POP3", 135: "RPC", 139: "NetBIOS", 143: "IMAP",
            443: "HTTPS", 993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 
            1521: "Oracle", 3389: "RDP", 5432: "PostgreSQL", 8080: "HTTP-Alt"
        }
    
    async def scan_single_port(self, host: str, port: int, timeout: float = 3.0) -> PortScanResult:
        """Scan a single port on a host"""
        start_time = time.time()
        
        try:
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            result = sock.connect_ex((host, port))
            response_time = (time.time() - start_time) * 1000
            
            is_open = (result == 0)
            service = self.service_map.get(port, f"Port {port}")
            
            sock.close()
            
            return PortScanResult(
                host=host,
                port=port,
                is_open=is_open,
                service=service,
                response_time_ms=response_time if is_open else None
            )
            
        except Exception as e:
            return PortScanResult(
                host=host,
                port=port,
                is_open=False,
                service=self.service_map.get(port, f"Port {port}"),
                response_time_ms=None
            )
    
    async def scan_ports(self, host: str, ports: List[int] = None, timeout: float = 3.0) -> List[PortScanResult]:
        """Scan multiple ports on a host"""
        if ports is None:
            ports = self.common_ports
        
        tasks = []
        for port in ports:
            task = self.scan_single_port(host, port, timeout)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = []
        for result in results:
            if isinstance(result, PortScanResult):
                valid_results.append(result)
        
        return valid_results
    
    async def dns_lookup(self, hostname: str) -> DNSLookupResult:
        """Perform comprehensive DNS lookup"""
        try:
            # Basic A record lookup
            ip_addresses = []
            try:
                addr_info = socket.getaddrinfo(hostname, None)
                ip_addresses = list(set([addr[4][0] for addr in addr_info]))
            except socket.gaierror:
                pass
            
            # Try to get MX and NS records using nslookup if available
            mx_records = []
            ns_records = []
            
            try:
                # Try nslookup for MX records
                if platform.system().lower() == 'windows':
                    mx_result = subprocess.run(['nslookup', '-type=MX', hostname], 
                                             capture_output=True, text=True, timeout=10)
                    if mx_result.returncode == 0:
                        mx_lines = [line.strip() for line in mx_result.stdout.split('\n') 
                                  if 'mail exchanger' in line.lower()]
                        mx_records = [line.split('=')[-1].strip() for line in mx_lines]
                
                # Try nslookup for NS records
                    ns_result = subprocess.run(['nslookup', '-type=NS', hostname], 
                                             capture_output=True, text=True, timeout=10)
                    if ns_result.returncode == 0:
                        ns_lines = [line.strip() for line in ns_result.stdout.split('\n') 
                                  if 'nameserver' in line.lower()]
                        ns_records = [line.split('=')[-1].strip() for line in ns_lines]
                        
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass  # nslookup not available or timeout
            
            return DNSLookupResult(
                hostname=hostname,
                ip_addresses=ip_addresses,
                mx_records=mx_records,
                ns_records=ns_records,
                success=len(ip_addresses) > 0,
                error_message=None if len(ip_addresses) > 0 else "No IP addresses found"
            )
            
        except Exception as e:
            return DNSLookupResult(
                hostname=hostname,
                ip_addresses=[],
                mx_records=[],
                ns_records=[],
                success=False,
                error_message=str(e)
            )
    
    async def check_connectivity(self, host: str, port: Optional[int] = None) -> Dict:
        """Check basic connectivity to a host"""
        result = {
            "host": host,
            "reachable": False,
            "response_time_ms": None,
            "error_message": None
        }
        
        try:
            start_time = time.time()
            
            if port:
                # Check specific port
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                connection_result = sock.connect_ex((host, port))
                sock.close()
                
                result["reachable"] = (connection_result == 0)
                result["port"] = port
            else:
                # Basic hostname resolution
                socket.gethostbyname(host)
                result["reachable"] = True
            
            result["response_time_ms"] = (time.time() - start_time) * 1000
            
        except Exception as e:
            result["error_message"] = str(e)
        
        return result
    
    def validate_ip_address(self, ip_str: str) -> bool:
        """Validate if string is a valid IP address"""
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False
    
    def get_ip_info(self, ip_str: str) -> Dict:
        """Get information about an IP address"""
        try:
            ip = ipaddress.ip_address(ip_str)
            return {
                "ip": str(ip),
                "version": ip.version,
                "is_private": ip.is_private,
                "is_multicast": ip.is_multicast,
                "is_reserved": ip.is_reserved,
                "is_loopback": ip.is_loopback,
                "network_class": self._get_network_class(str(ip)) if ip.version == 4 else "IPv6"
            }
        except ValueError:
            return {"error": "Invalid IP address format"}
    
    def _get_network_class(self, ip_str: str) -> str:
        """Determine IPv4 network class"""
        first_octet = int(ip_str.split('.')[0])
        if 1 <= first_octet <= 126:
            return "Class A"
        elif 128 <= first_octet <= 191:
            return "Class B"
        elif 192 <= first_octet <= 223:
            return "Class C"
        elif 224 <= first_octet <= 239:
            return "Class D (Multicast)"
        elif 240 <= first_octet <= 255:
            return "Class E (Reserved)"
        else:
            return "Unknown"

# Global instance
advanced_tools = AdvancedNetworkTools()

# Convenience functions for API use
async def scan_host_ports(host: str, ports: List[int] = None) -> List[Dict]:
    """Scan ports on a host and return results as dictionaries"""
    results = await advanced_tools.scan_ports(host, ports)
    return [
        {
            "host": r.host,
            "port": r.port,
            "is_open": r.is_open,
            "service": r.service,
            "response_time_ms": r.response_time_ms
        }
        for r in results
    ]

async def lookup_dns(hostname: str) -> Dict:
    """Perform DNS lookup and return result as dictionary"""
    result = await advanced_tools.dns_lookup(hostname)
    return {
        "hostname": result.hostname,
        "ip_addresses": result.ip_addresses,
        "mx_records": result.mx_records,
        "ns_records": result.ns_records,
        "success": result.success,
        "error_message": result.error_message
    }

async def check_host_connectivity(host: str, port: Optional[int] = None) -> Dict:
    """Check connectivity to a host"""
    return await advanced_tools.check_connectivity(host, port)

def analyze_ip_address(ip_str: str) -> Dict:
    """Analyze an IP address"""
    return advanced_tools.get_ip_info(ip_str)

def validate_ip(ip_str: str) -> bool:
    """Validate IP address format"""
    return advanced_tools.validate_ip_address(ip_str)