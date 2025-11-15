"""
Ping Test Module for Network Troubleshooting Bot
Performs ping tests to check connectivity and measure latency
"""
import asyncio
import platform
import subprocess
import socket
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class PingResult:
    target: str
    success: bool
    packets_sent: int
    packets_received: int
    packet_loss_percent: float
    min_latency_ms: Optional[float]
    max_latency_ms: Optional[float]
    avg_latency_ms: Optional[float]
    error_message: Optional[str]
    timestamp: float

class PingTester:
    def __init__(self, timeout: int = 5, count: int = 4):
        self.timeout = timeout
        self.count = count
        self.system = platform.system().lower()
        
    async def ping_host(self, target: str) -> PingResult:
        """
        Perform ping test to target host
        """
        try:
            # Validate target
            if not self._is_valid_target(target):
                return PingResult(
                    target=target,
                    success=False,
                    packets_sent=0,
                    packets_received=0,
                    packet_loss_percent=100.0,
                    min_latency_ms=None,
                    max_latency_ms=None,
                    avg_latency_ms=None,
                    error_message="Invalid target format",
                    timestamp=time.time()
                )
            
            # Build ping command based on OS
            command = self._build_ping_command(target)
            
            # Execute ping command
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.timeout + 10
                )
            except asyncio.TimeoutError:
                process.kill()
                return PingResult(
                    target=target,
                    success=False,
                    packets_sent=self.count,
                    packets_received=0,
                    packet_loss_percent=100.0,
                    min_latency_ms=None,
                    max_latency_ms=None,
                    avg_latency_ms=None,
                    error_message="Ping timeout",
                    timestamp=time.time()
                )
            
            # Parse results
            return self._parse_ping_output(target, stdout.decode(), stderr.decode())
            
        except Exception as e:
            logger.error(f"Error pinging {target}: {str(e)}")
            return PingResult(
                target=target,
                success=False,
                packets_sent=0,
                packets_received=0,
                packet_loss_percent=100.0,
                min_latency_ms=None,
                max_latency_ms=None,
                avg_latency_ms=None,
                error_message=str(e),
                timestamp=time.time()
            )
    
    def _build_ping_command(self, target: str) -> List[str]:
        """Build ping command based on operating system"""
        if self.system == "windows":
            return ["ping", "-n", str(self.count), "-w", str(self.timeout * 1000), target]
        else:  # Linux/Mac
            return ["ping", "-c", str(self.count), "-W", str(self.timeout), target]
    
    def _is_valid_target(self, target: str) -> bool:
        """Validate if target is a valid IP address or hostname"""
        try:
            # Try to resolve hostname to IP
            socket.gethostbyname(target)
            return True
        except socket.gaierror:
            return False
    
    def _parse_ping_output(self, target: str, stdout: str, stderr: str) -> PingResult:
        """Parse ping command output"""
        timestamp = time.time()
        
        if stderr and not stdout:
            return PingResult(
                target=target,
                success=False,
                packets_sent=self.count,
                packets_received=0,
                packet_loss_percent=100.0,
                min_latency_ms=None,
                max_latency_ms=None,
                avg_latency_ms=None,
                error_message=stderr.strip(),
                timestamp=timestamp
            )
        
        try:
            if self.system == "windows":
                return self._parse_windows_ping(target, stdout, timestamp)
            else:
                return self._parse_unix_ping(target, stdout, timestamp)
        except Exception as e:
            logger.error(f"Error parsing ping output: {str(e)}")
            return PingResult(
                target=target,
                success=False,
                packets_sent=self.count,
                packets_received=0,
                packet_loss_percent=100.0,
                min_latency_ms=None,
                max_latency_ms=None,
                avg_latency_ms=None,
                error_message=f"Failed to parse output: {str(e)}",
                timestamp=timestamp
            )
    
    def _parse_windows_ping(self, target: str, output: str, timestamp: float) -> PingResult:
        """Parse Windows ping output"""
        lines = output.split('\n')
        packets_sent = self.count
        packets_received = 0
        latencies = []
        
        for line in lines:
            if "Reply from" in line and "time=" in line:
                packets_received += 1
                # Extract latency
                try:
                    time_part = line.split("time=")[1].split("ms")[0]
                    if time_part.strip() == "<1":
                        latency = 1.0
                    else:
                        latency = float(time_part)
                    latencies.append(latency)
                except (IndexError, ValueError):
                    pass
            elif "Request timed out" in line or "Destination host unreachable" in line:
                # Count as sent but not received
                pass
        
        packet_loss = ((packets_sent - packets_received) / packets_sent) * 100
        success = packets_received > 0
        
        min_lat = min(latencies) if latencies else None
        max_lat = max(latencies) if latencies else None
        avg_lat = sum(latencies) / len(latencies) if latencies else None
        
        return PingResult(
            target=target,
            success=success,
            packets_sent=packets_sent,
            packets_received=packets_received,
            packet_loss_percent=packet_loss,
            min_latency_ms=min_lat,
            max_latency_ms=max_lat,
            avg_latency_ms=avg_lat,
            error_message=None if success else "No replies received",
            timestamp=timestamp
        )
    
    def _parse_unix_ping(self, target: str, output: str, timestamp: float) -> PingResult:
        """Parse Unix/Linux ping output"""
        lines = output.split('\n')
        packets_sent = self.count
        packets_received = 0
        latencies = []
        
        for line in lines:
            if " bytes from " in line and "time=" in line:
                packets_received += 1
                # Extract latency
                try:
                    time_part = line.split("time=")[1].split(" ")[0]
                    latency = float(time_part)
                    latencies.append(latency)
                except (IndexError, ValueError):
                    pass
            elif "packet loss" in line:
                # Extract packet loss percentage
                try:
                    loss_part = line.split("packet loss")[0].split()[-1].replace('%', '')
                    packet_loss_from_output = float(loss_part)
                except (IndexError, ValueError):
                    packet_loss_from_output = ((packets_sent - packets_received) / packets_sent) * 100
        
        packet_loss = ((packets_sent - packets_received) / packets_sent) * 100
        success = packets_received > 0
        
        min_lat = min(latencies) if latencies else None
        max_lat = max(latencies) if latencies else None
        avg_lat = sum(latencies) / len(latencies) if latencies else None
        
        return PingResult(
            target=target,
            success=success,
            packets_sent=packets_sent,
            packets_received=packets_received,
            packet_loss_percent=packet_loss,
            min_latency_ms=min_lat,
            max_latency_ms=max_lat,
            avg_latency_ms=avg_lat,
            error_message=None if success else "No replies received",
            timestamp=timestamp
        )
    
    async def ping_multiple_hosts(self, targets: List[str]) -> Dict[str, PingResult]:
        """
        Ping multiple hosts concurrently
        """
        tasks = [self.ping_host(target) for target in targets]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                output[targets[i]] = PingResult(
                    target=targets[i],
                    success=False,
                    packets_sent=0,
                    packets_received=0,
                    packet_loss_percent=100.0,
                    min_latency_ms=None,
                    max_latency_ms=None,
                    avg_latency_ms=None,
                    error_message=str(result),
                    timestamp=time.time()
                )
            else:
                output[targets[i]] = result
        
        return output
    
    async def continuous_ping(self, target: str, duration_seconds: int = 60, interval: int = 1):
        """
        Perform continuous ping for monitoring
        """
        results = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            result = await self.ping_host(target)
            results.append(result)
            
            if time.time() - start_time < duration_seconds:
                await asyncio.sleep(interval)
        
        return results

# Convenience functions
async def ping_host(target: str, timeout: int = 5, count: int = 4) -> PingResult:
    """Simple ping function"""
    tester = PingTester(timeout=timeout, count=count)
    return await tester.ping_host(target)

async def ping_multiple(targets: List[str], timeout: int = 5, count: int = 4) -> Dict[str, PingResult]:
    """Ping multiple hosts"""
    tester = PingTester(timeout=timeout, count=count)
    return await tester.ping_multiple_hosts(targets)