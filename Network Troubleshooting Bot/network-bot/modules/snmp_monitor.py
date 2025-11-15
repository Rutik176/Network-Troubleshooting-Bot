"""
SNMP Monitor Module for Network Troubleshooting Bot
Fetches interface statistics and device information via SNMP
"""
import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

try:
    from pysnmp.hlapi import *
    from pysnmp.error import PySnmpError
except ImportError:
    logging.warning("pysnmp not installed. SNMP functionality will be limited.")
    PySnmpError = Exception

logger = logging.getLogger(__name__)

@dataclass
class InterfaceStats:
    interface_name: str
    interface_index: int
    admin_status: str  # up, down, testing
    oper_status: str   # up, down, testing, unknown, dormant, notPresent, lowerLayerDown
    bytes_in: int
    bytes_out: int
    packets_in: int
    packets_out: int
    errors_in: int
    errors_out: int
    discards_in: int
    discards_out: int
    speed_bps: int
    mtu: int
    last_change: int
    utilization_in_percent: float
    utilization_out_percent: float

@dataclass
class DeviceInfo:
    system_description: str
    system_uptime: int
    system_contact: str
    system_name: str
    system_location: str
    system_services: int
    cpu_usage_percent: Optional[float]
    memory_usage_percent: Optional[float]
    temperature_celsius: Optional[float]

@dataclass
class SNMPResult:
    target: str
    success: bool
    device_info: Optional[DeviceInfo]
    interfaces: List[InterfaceStats]
    error_message: Optional[str]
    timestamp: float
    response_time_ms: float

class SNMPMonitor:
    def __init__(self, community: str = "public", timeout: int = 5, retries: int = 3):
        self.community = community
        self.timeout = timeout
        self.retries = retries
        
        # Standard SNMP OIDs
        self.oids = {
            # System Information
            'sysDescr': '1.3.6.1.2.1.1.1.0',
            'sysUpTime': '1.3.6.1.2.1.1.3.0',
            'sysContact': '1.3.6.1.2.1.1.4.0',
            'sysName': '1.3.6.1.2.1.1.5.0',
            'sysLocation': '1.3.6.1.2.1.1.6.0',
            'sysServices': '1.3.6.1.2.1.1.7.0',
            
            # Interface Information
            'ifIndex': '1.3.6.1.2.1.2.2.1.1',
            'ifDescr': '1.3.6.1.2.1.2.2.1.2',
            'ifType': '1.3.6.1.2.1.2.2.1.3',
            'ifMtu': '1.3.6.1.2.1.2.2.1.4',
            'ifSpeed': '1.3.6.1.2.1.2.2.1.5',
            'ifPhysAddress': '1.3.6.1.2.1.2.2.1.6',
            'ifAdminStatus': '1.3.6.1.2.1.2.2.1.7',
            'ifOperStatus': '1.3.6.1.2.1.2.2.1.8',
            'ifLastChange': '1.3.6.1.2.1.2.2.1.9',
            'ifInOctets': '1.3.6.1.2.1.2.2.1.10',
            'ifInUcastPkts': '1.3.6.1.2.1.2.2.1.11',
            'ifInDiscards': '1.3.6.1.2.1.2.2.1.13',
            'ifInErrors': '1.3.6.1.2.1.2.2.1.14',
            'ifOutOctets': '1.3.6.1.2.1.2.2.1.16',
            'ifOutUcastPkts': '1.3.6.1.2.1.2.2.1.17',
            'ifOutDiscards': '1.3.6.1.2.1.2.2.1.19',
            'ifOutErrors': '1.3.6.1.2.1.2.2.1.20',
            
            # High-speed interface counters (64-bit)
            'ifHCInOctets': '1.3.6.1.2.1.31.1.1.1.6',
            'ifHCOutOctets': '1.3.6.1.2.1.31.1.1.1.10',
            'ifHighSpeed': '1.3.6.1.2.1.31.1.1.1.15',
            
            # Cisco-specific OIDs
            'cpmCPUTotalIndex': '1.3.6.1.4.1.9.9.109.1.1.1.1.2',
            'cpmCPUTotal5minRev': '1.3.6.1.4.1.9.9.109.1.1.1.1.8',
            'ciscoMemoryPoolUsed': '1.3.6.1.4.1.9.9.48.1.1.1.5',
            'ciscoMemoryPoolFree': '1.3.6.1.4.1.9.9.48.1.1.1.6',
        }
        
        # Status mappings
        self.admin_status_map = {1: 'up', 2: 'down', 3: 'testing'}
        self.oper_status_map = {
            1: 'up', 2: 'down', 3: 'testing', 4: 'unknown',
            5: 'dormant', 6: 'notPresent', 7: 'lowerLayerDown'
        }
    
    async def get_device_info(self, target: str, community: str = None) -> SNMPResult:
        """
        Get comprehensive device information via SNMP
        """
        start_time = time.time()
        timestamp = start_time
        community = community or self.community
        
        try:
            # Get basic system information
            device_info = await self._get_system_info(target, community)
            
            # Get interface information
            interfaces = await self._get_interface_stats(target, community)
            
            response_time = (time.time() - start_time) * 1000
            
            return SNMPResult(
                target=target,
                success=True,
                device_info=device_info,
                interfaces=interfaces,
                error_message=None,
                timestamp=timestamp,
                response_time_ms=response_time
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"SNMP error for {target}: {str(e)}")
            return SNMPResult(
                target=target,
                success=False,
                device_info=None,
                interfaces=[],
                error_message=str(e),
                timestamp=timestamp,
                response_time_ms=response_time
            )
    
    async def _get_system_info(self, target: str, community: str) -> DeviceInfo:
        """Get system information via SNMP"""
        system_oids = [
            self.oids['sysDescr'],
            self.oids['sysUpTime'],
            self.oids['sysContact'],
            self.oids['sysName'],
            self.oids['sysLocation'],
            self.oids['sysServices']
        ]
        
        results = await self._snmp_get(target, community, system_oids)
        
        # Try to get CPU and memory usage (Cisco-specific)
        cpu_usage = await self._get_cpu_usage(target, community)
        memory_usage = await self._get_memory_usage(target, community)
        
        return DeviceInfo(
            system_description=results.get(self.oids['sysDescr'], 'Unknown'),
            system_uptime=int(results.get(self.oids['sysUpTime'], 0)),
            system_contact=results.get(self.oids['sysContact'], ''),
            system_name=results.get(self.oids['sysName'], ''),
            system_location=results.get(self.oids['sysLocation'], ''),
            system_services=int(results.get(self.oids['sysServices'], 0)),
            cpu_usage_percent=cpu_usage,
            memory_usage_percent=memory_usage,
            temperature_celsius=None  # Could be added with vendor-specific OIDs
        )
    
    async def _get_interface_stats(self, target: str, community: str) -> List[InterfaceStats]:
        """Get interface statistics via SNMP"""
        interfaces = []
        
        try:
            # Get interface indices first
            interface_indices = await self._snmp_walk(target, community, self.oids['ifIndex'])
            
            for index_oid, index_value in interface_indices.items():
                interface_index = int(index_value)
                
                # Get interface data
                interface_data = await self._get_single_interface_stats(
                    target, community, interface_index
                )
                
                if interface_data:
                    interfaces.append(interface_data)
                    
        except Exception as e:
            logger.error(f"Error getting interface stats: {str(e)}")
        
        return interfaces
    
    async def _get_single_interface_stats(self, target: str, community: str, 
                                        interface_index: int) -> Optional[InterfaceStats]:
        """Get statistics for a single interface"""
        try:
            # Build OIDs for this specific interface
            oids = [
                f"{self.oids['ifDescr']}.{interface_index}",
                f"{self.oids['ifAdminStatus']}.{interface_index}",
                f"{self.oids['ifOperStatus']}.{interface_index}",
                f"{self.oids['ifSpeed']}.{interface_index}",
                f"{self.oids['ifMtu']}.{interface_index}",
                f"{self.oids['ifLastChange']}.{interface_index}",
                f"{self.oids['ifInOctets']}.{interface_index}",
                f"{self.oids['ifOutOctets']}.{interface_index}",
                f"{self.oids['ifInUcastPkts']}.{interface_index}",
                f"{self.oids['ifOutUcastPkts']}.{interface_index}",
                f"{self.oids['ifInErrors']}.{interface_index}",
                f"{self.oids['ifOutErrors']}.{interface_index}",
                f"{self.oids['ifInDiscards']}.{interface_index}",
                f"{self.oids['ifOutDiscards']}.{interface_index}",
            ]
            
            results = await self._snmp_get(target, community, oids)
            
            # Try to get high-speed counters if available
            hc_in_oid = f"{self.oids['ifHCInOctets']}.{interface_index}"
            hc_out_oid = f"{self.oids['ifHCOutOctets']}.{interface_index}"
            hc_speed_oid = f"{self.oids['ifHighSpeed']}.{interface_index}"
            
            hc_results = await self._snmp_get(target, community, [hc_in_oid, hc_out_oid, hc_speed_oid])
            
            # Extract values
            interface_name = results.get(f"{self.oids['ifDescr']}.{interface_index}", f"Interface{interface_index}")
            admin_status = int(results.get(f"{self.oids['ifAdminStatus']}.{interface_index}", 2))
            oper_status = int(results.get(f"{self.oids['ifOperStatus']}.{interface_index}", 2))
            speed_bps = int(results.get(f"{self.oids['ifSpeed']}.{interface_index}", 0))
            mtu = int(results.get(f"{self.oids['ifMtu']}.{interface_index}", 0))
            last_change = int(results.get(f"{self.oids['ifLastChange']}.{interface_index}", 0))
            
            # Use high-speed counters if available, otherwise use regular counters
            bytes_in = int(hc_results.get(hc_in_oid, results.get(f"{self.oids['ifInOctets']}.{interface_index}", 0)))
            bytes_out = int(hc_results.get(hc_out_oid, results.get(f"{self.oids['ifOutOctets']}.{interface_index}", 0)))
            
            packets_in = int(results.get(f"{self.oids['ifInUcastPkts']}.{interface_index}", 0))
            packets_out = int(results.get(f"{self.oids['ifOutUcastPkts']}.{interface_index}", 0))
            errors_in = int(results.get(f"{self.oids['ifInErrors']}.{interface_index}", 0))
            errors_out = int(results.get(f"{self.oids['ifOutErrors']}.{interface_index}", 0))
            discards_in = int(results.get(f"{self.oids['ifInDiscards']}.{interface_index}", 0))
            discards_out = int(results.get(f"{self.oids['ifOutDiscards']}.{interface_index}", 0))
            
            # Use high-speed value if available
            high_speed = hc_results.get(hc_speed_oid)
            if high_speed:
                speed_bps = int(high_speed) * 1000000  # Convert from Mbps to bps
            
            # Calculate utilization (this would need to be calculated over time intervals)
            utilization_in = 0.0
            utilization_out = 0.0
            
            return InterfaceStats(
                interface_name=interface_name,
                interface_index=interface_index,
                admin_status=self.admin_status_map.get(admin_status, 'unknown'),
                oper_status=self.oper_status_map.get(oper_status, 'unknown'),
                bytes_in=bytes_in,
                bytes_out=bytes_out,
                packets_in=packets_in,
                packets_out=packets_out,
                errors_in=errors_in,
                errors_out=errors_out,
                discards_in=discards_in,
                discards_out=discards_out,
                speed_bps=speed_bps,
                mtu=mtu,
                last_change=last_change,
                utilization_in_percent=utilization_in,
                utilization_out_percent=utilization_out
            )
            
        except Exception as e:
            logger.error(f"Error getting stats for interface {interface_index}: {str(e)}")
            return None
    
    async def _get_cpu_usage(self, target: str, community: str) -> Optional[float]:
        """Get CPU usage (Cisco-specific)"""
        try:
            cpu_oid = f"{self.oids['cpmCPUTotal5minRev']}.1"
            results = await self._snmp_get(target, community, [cpu_oid])
            cpu_value = results.get(cpu_oid)
            return float(cpu_value) if cpu_value else None
        except:
            return None
    
    async def _get_memory_usage(self, target: str, community: str) -> Optional[float]:
        """Get memory usage (Cisco-specific)"""
        try:
            used_oid = f"{self.oids['ciscoMemoryPoolUsed']}.1"
            free_oid = f"{self.oids['ciscoMemoryPoolFree']}.1"
            
            results = await self._snmp_get(target, community, [used_oid, free_oid])
            
            used = results.get(used_oid)
            free = results.get(free_oid)
            
            if used and free:
                used = int(used)
                free = int(free)
                total = used + free
                return (used / total) * 100 if total > 0 else None
                
        except:
            return None
    
    async def _snmp_get(self, target: str, community: str, oids: List[str]) -> Dict[str, str]:
        """Perform SNMP GET operation"""
        results = {}
        
        try:
            for errorIndication, errorStatus, errorIndex, varBinds in getCmd(
                SnmpEngine(),
                CommunityData(community),
                UdpTransportTarget((target, 161), timeout=self.timeout, retries=self.retries),
                ContextData(),
                *[ObjectType(ObjectIdentity(oid)) for oid in oids]
            ):
                if errorIndication:
                    raise Exception(f"SNMP error: {errorIndication}")
                
                if errorStatus:
                    raise Exception(f"SNMP error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}")
                
                for varBind in varBinds:
                    oid_str = str(varBind[0])
                    value_str = str(varBind[1])
                    results[oid_str] = value_str
                    
        except Exception as e:
            logger.error(f"SNMP GET error: {str(e)}")
            raise
        
        return results
    
    async def _snmp_walk(self, target: str, community: str, base_oid: str) -> Dict[str, str]:
        """Perform SNMP WALK operation"""
        results = {}
        
        try:
            for errorIndication, errorStatus, errorIndex, varBinds in nextCmd(
                SnmpEngine(),
                CommunityData(community),
                UdpTransportTarget((target, 161), timeout=self.timeout, retries=self.retries),
                ContextData(),
                ObjectType(ObjectIdentity(base_oid)),
                lexicographicMode=False
            ):
                if errorIndication:
                    break
                
                if errorStatus:
                    raise Exception(f"SNMP error: {errorStatus.prettyPrint()}")
                
                for varBind in varBinds:
                    oid_str = str(varBind[0])
                    value_str = str(varBind[1])
                    results[oid_str] = value_str
                    
        except Exception as e:
            logger.error(f"SNMP WALK error: {str(e)}")
            raise
        
        return results
    
    async def monitor_multiple_devices(self, targets: List[str], community: str = None) -> Dict[str, SNMPResult]:
        """Monitor multiple devices concurrently"""
        tasks = [self.get_device_info(target, community) for target in targets]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                output[targets[i]] = SNMPResult(
                    target=targets[i],
                    success=False,
                    device_info=None,
                    interfaces=[],
                    error_message=str(result),
                    timestamp=time.time(),
                    response_time_ms=0
                )
            else:
                output[targets[i]] = result
        
        return output
    
    def calculate_utilization(self, current_stats: InterfaceStats, 
                            previous_stats: InterfaceStats, interval_seconds: int) -> InterfaceStats:
        """Calculate interface utilization based on two measurements"""
        if not current_stats.speed_bps or interval_seconds <= 0:
            return current_stats
        
        # Calculate bytes per second
        bytes_in_per_sec = (current_stats.bytes_in - previous_stats.bytes_in) / interval_seconds
        bytes_out_per_sec = (current_stats.bytes_out - previous_stats.bytes_out) / interval_seconds
        
        # Convert to bits per second
        bits_in_per_sec = bytes_in_per_sec * 8
        bits_out_per_sec = bytes_out_per_sec * 8
        
        # Calculate utilization percentage
        utilization_in = (bits_in_per_sec / current_stats.speed_bps) * 100
        utilization_out = (bits_out_per_sec / current_stats.speed_bps) * 100
        
        # Create updated stats
        updated_stats = current_stats
        updated_stats.utilization_in_percent = max(0, min(100, utilization_in))
        updated_stats.utilization_out_percent = max(0, min(100, utilization_out))
        
        return updated_stats

# Convenience functions
async def get_device_snmp_info(target: str, community: str = "public") -> SNMPResult:
    """Simple SNMP info function"""
    monitor = SNMPMonitor(community=community)
    return await monitor.get_device_info(target)

async def monitor_devices(targets: List[str], community: str = "public") -> Dict[str, SNMPResult]:
    """Monitor multiple devices"""
    monitor = SNMPMonitor(community=community)
    return await monitor.monitor_multiple_devices(targets, community)