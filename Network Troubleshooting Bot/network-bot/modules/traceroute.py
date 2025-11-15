"""
Traceroute Module for Network Troubleshooting Bot
Performs traceroute to trace network path and identify routing issues
"""
import asyncio
import platform
import subprocess
import socket
import time
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TracerouteHop:
    hop_number: int
    ip_address: Optional[str]
    hostname: Optional[str]
    latency_ms: List[float]
    timeout: bool
    error_message: Optional[str]

@dataclass
class TracerouteResult:
    target: str
    success: bool
    hops: List[TracerouteHop]
    total_hops: int
    target_reached: bool
    error_message: Optional[str]
    timestamp: float
    execution_time_ms: float

class TracerouteTester:
    def __init__(self, max_hops: int = 30, timeout: int = 5):
        self.max_hops = max_hops
        self.timeout = timeout
        self.system = platform.system().lower()
    
    async def traceroute(self, target: str) -> TracerouteResult:
        """
        Perform traceroute to target host
        """
        start_time = time.time()
        timestamp = start_time
        
        try:
            # Validate target
            if not self._is_valid_target(target):
                return TracerouteResult(
                    target=target,
                    success=False,
                    hops=[],
                    total_hops=0,
                    target_reached=False,
                    error_message="Invalid target format",
                    timestamp=timestamp,
                    execution_time_ms=0
                )
            
            # Build traceroute command
            command = self._build_traceroute_command(target)
            
            # Execute traceroute command
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout * self.max_hops  # Allow enough time
                )
            except asyncio.TimeoutError:
                process.kill()
                execution_time = (time.time() - start_time) * 1000
                return TracerouteResult(
                    target=target,
                    success=False,
                    hops=[],
                    total_hops=0,
                    target_reached=False,
                    error_message="Traceroute timeout",
                    timestamp=timestamp,
                    execution_time_ms=execution_time
                )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Parse results
            return self._parse_traceroute_output(
                target, stdout.decode(), stderr.decode(), timestamp, execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Error running traceroute to {target}: {str(e)}")
            return TracerouteResult(
                target=target,
                success=False,
                hops=[],
                total_hops=0,
                target_reached=False,
                error_message=str(e),
                timestamp=timestamp,
                execution_time_ms=execution_time
            )
    
    def _build_traceroute_command(self, target: str) -> List[str]:
        """Build traceroute command based on operating system"""
        if self.system == "windows":
            return ["tracert", "-h", str(self.max_hops), "-w", str(self.timeout * 1000), target]
        else:  # Linux/Mac
            return ["traceroute", "-m", str(self.max_hops), "-w", str(self.timeout), target]
    
    def _is_valid_target(self, target: str) -> bool:
        """Validate if target is a valid IP address or hostname"""
        try:
            socket.gethostbyname(target)
            return True
        except socket.gaierror:
            return False
    
    def _parse_traceroute_output(self, target: str, stdout: str, stderr: str, 
                                timestamp: float, execution_time: float) -> TracerouteResult:
        """Parse traceroute command output"""
        if stderr and not stdout:
            return TracerouteResult(
                target=target,
                success=False,
                hops=[],
                total_hops=0,
                target_reached=False,
                error_message=stderr.strip(),
                timestamp=timestamp,
                execution_time_ms=execution_time
            )
        
        try:
            if self.system == "windows":
                return self._parse_windows_tracert(target, stdout, timestamp, execution_time)
            else:
                return self._parse_unix_traceroute(target, stdout, timestamp, execution_time)
        except Exception as e:
            logger.error(f"Error parsing traceroute output: {str(e)}")
            return TracerouteResult(
                target=target,
                success=False,
                hops=[],
                total_hops=0,
                target_reached=False,
                error_message=f"Failed to parse output: {str(e)}",
                timestamp=timestamp,
                execution_time_ms=execution_time
            )
    
    def _parse_windows_tracert(self, target: str, output: str, 
                              timestamp: float, execution_time: float) -> TracerouteResult:
        """Parse Windows tracert output"""
        lines = output.split('\n')
        hops = []
        target_reached = False
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("Tracing route"):
                continue
            
            # Look for hop lines (start with hop number)
            hop_match = re.match(r'^\s*(\d+)', line)
            if hop_match:
                hop_number = int(hop_match.group(1))
                
                # Check for timeouts
                if "Request timed out" in line or "*" in line:
                    hops.append(TracerouteHop(
                        hop_number=hop_number,
                        ip_address=None,
                        hostname=None,
                        latency_ms=[],
                        timeout=True,
                        error_message="Request timed out"
                    ))
                else:
                    # Parse IP address and latencies
                    ip_pattern = r'(\d+\.\d+\.\d+\.\d+)'
                    latency_pattern = r'(\d+)\s*ms'
                    
                    ip_matches = re.findall(ip_pattern, line)
                    latency_matches = re.findall(latency_pattern, line)
                    
                    ip_address = ip_matches[0] if ip_matches else None
                    latencies = [float(lat) for lat in latency_matches]
                    
                    # Try to resolve hostname
                    hostname = None
                    if ip_address:
                        try:
                            hostname = socket.gethostbyaddr(ip_address)[0]
                        except socket.herror:
                            pass
                    
                    hops.append(TracerouteHop(
                        hop_number=hop_number,
                        ip_address=ip_address,
                        hostname=hostname,
                        latency_ms=latencies,
                        timeout=False,
                        error_message=None
                    ))
                    
                    # Check if target is reached
                    if ip_address:
                        try:
                            target_ip = socket.gethostbyname(target)
                            if ip_address == target_ip:
                                target_reached = True
                        except socket.gaierror:
                            pass
        
        success = len(hops) > 0
        
        return TracerouteResult(
            target=target,
            success=success,
            hops=hops,
            total_hops=len(hops),
            target_reached=target_reached,
            error_message=None if success else "No hops found",
            timestamp=timestamp,
            execution_time_ms=execution_time
        )
    
    def _parse_unix_traceroute(self, target: str, output: str, 
                              timestamp: float, execution_time: float) -> TracerouteResult:
        """Parse Unix/Linux traceroute output"""
        lines = output.split('\n')
        hops = []
        target_reached = False
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("traceroute to"):
                continue
            
            # Look for hop lines
            hop_match = re.match(r'^\s*(\d+)', line)
            if hop_match:
                hop_number = int(hop_match.group(1))
                
                # Check for timeouts
                if "*" in line:
                    hops.append(TracerouteHop(
                        hop_number=hop_number,
                        ip_address=None,
                        hostname=None,
                        latency_ms=[],
                        timeout=True,
                        error_message="Request timed out"
                    ))
                else:
                    # Parse hostname/IP and latencies
                    # Pattern to match hostname (hostname) or IP
                    host_pattern = r'([a-zA-Z0-9.-]+)\s*\(([0-9.]+)\)|([0-9.]+)'
                    latency_pattern = r'(\d+\.?\d*)\s*ms'
                    
                    host_matches = re.findall(host_pattern, line)
                    latency_matches = re.findall(latency_pattern, line)
                    
                    hostname = None
                    ip_address = None
                    
                    if host_matches:
                        match = host_matches[0]
                        if match[0] and match[1]:  # hostname (ip) format
                            hostname = match[0]
                            ip_address = match[1]
                        elif match[2]:  # ip only format
                            ip_address = match[2]
                    
                    latencies = [float(lat) for lat in latency_matches]
                    
                    hops.append(TracerouteHop(
                        hop_number=hop_number,
                        ip_address=ip_address,
                        hostname=hostname,
                        latency_ms=latencies,
                        timeout=False,
                        error_message=None
                    ))
                    
                    # Check if target is reached
                    if ip_address:
                        try:
                            target_ip = socket.gethostbyname(target)
                            if ip_address == target_ip:
                                target_reached = True
                        except socket.gaierror:
                            pass
        
        success = len(hops) > 0
        
        return TracerouteResult(
            target=target,
            success=success,
            hops=hops,
            total_hops=len(hops),
            target_reached=target_reached,
            error_message=None if success else "No hops found",
            timestamp=timestamp,
            execution_time_ms=execution_time
        )
    
    async def traceroute_multiple(self, targets: List[str]) -> Dict[str, TracerouteResult]:
        """
        Run traceroute to multiple targets concurrently
        """
        tasks = [self.traceroute(target) for target in targets]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                output[targets[i]] = TracerouteResult(
                    target=targets[i],
                    success=False,
                    hops=[],
                    total_hops=0,
                    target_reached=False,
                    error_message=str(result),
                    timestamp=time.time(),
                    execution_time_ms=0
                )
            else:
                output[targets[i]] = result
        
        return output
    
    def analyze_path(self, result: TracerouteResult) -> Dict[str, any]:
        """
        Analyze traceroute results for issues
        """
        analysis = {
            "path_complete": result.target_reached,
            "total_hops": result.total_hops,
            "timeouts": [],
            "high_latency_hops": [],
            "latency_spikes": [],
            "avg_latency_per_hop": []
        }
        
        prev_latency = 0
        for hop in result.hops:
            if hop.timeout:
                analysis["timeouts"].append(hop.hop_number)
            elif hop.latency_ms:
                avg_latency = sum(hop.latency_ms) / len(hop.latency_ms)
                analysis["avg_latency_per_hop"].append({
                    "hop": hop.hop_number,
                    "latency": avg_latency,
                    "ip": hop.ip_address
                })
                
                # High latency detection (>100ms)
                if avg_latency > 100:
                    analysis["high_latency_hops"].append({
                        "hop": hop.hop_number,
                        "latency": avg_latency,
                        "ip": hop.ip_address
                    })
                
                # Latency spike detection (>50ms increase from previous hop)
                if prev_latency > 0 and avg_latency - prev_latency > 50:
                    analysis["latency_spikes"].append({
                        "hop": hop.hop_number,
                        "current_latency": avg_latency,
                        "previous_latency": prev_latency,
                        "spike": avg_latency - prev_latency,
                        "ip": hop.ip_address
                    })
                
                prev_latency = avg_latency
        
        return analysis

# Convenience functions
async def traceroute_host(target: str, max_hops: int = 30, timeout: int = 5) -> TracerouteResult:
    """Simple traceroute function"""
    tester = TracerouteTester(max_hops=max_hops, timeout=timeout)
    return await tester.traceroute(target)

async def traceroute_multiple(targets: List[str], max_hops: int = 30, timeout: int = 5) -> Dict[str, TracerouteResult]:
    """Traceroute multiple hosts"""
    tester = TracerouteTester(max_hops=max_hops, timeout=timeout)
    return await tester.traceroute_multiple(targets)