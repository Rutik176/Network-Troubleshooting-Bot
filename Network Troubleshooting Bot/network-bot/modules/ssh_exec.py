"""
SSH Execution Module for Network Troubleshooting Bot
Executes commands on network devices via SSH for automation and troubleshooting
"""
import asyncio
import paramiko
import socket
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
import io
import select

logger = logging.getLogger(__name__)

@dataclass
class SSHResult:
    host: str
    command: str
    success: bool
    output: str
    error: str
    exit_code: Optional[int]
    execution_time_ms: float
    timestamp: float

@dataclass
class DeviceCredentials:
    username: str
    password: str
    enable_password: Optional[str] = None
    port: int = 22
    timeout: int = 30

class SSHExecutor:
    def __init__(self, connect_timeout: int = 30, command_timeout: int = 60):
        self.connect_timeout = connect_timeout
        self.command_timeout = command_timeout
        self._connections = {}  # Cache connections for reuse
    
    async def execute_command(self, host: str, credentials: DeviceCredentials, 
                            command: str, enable_mode: bool = False) -> SSHResult:
        """
        Execute a single command on a remote device via SSH
        """
        start_time = time.time()
        timestamp = start_time
        
        try:
            # Get or create SSH connection
            ssh_client = await self._get_ssh_connection(host, credentials)
            
            if enable_mode and credentials.enable_password:
                # Enter enable mode for Cisco devices
                await self._enter_enable_mode(ssh_client, credentials.enable_password)
            
            # Execute command
            stdin, stdout, stderr = ssh_client.exec_command(
                command, timeout=self.command_timeout
            )
            
            # Wait for command completion
            exit_code = stdout.channel.recv_exit_status()
            
            # Read output
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            execution_time = (time.time() - start_time) * 1000
            
            return SSHResult(
                host=host,
                command=command,
                success=exit_code == 0,
                output=output,
                error=error,
                exit_code=exit_code,
                execution_time_ms=execution_time,
                timestamp=timestamp
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"SSH execution error on {host}: {str(e)}")
            return SSHResult(
                host=host,
                command=command,
                success=False,
                output="",
                error=str(e),
                exit_code=None,
                execution_time_ms=execution_time,
                timestamp=timestamp
            )
    
    async def execute_multiple_commands(self, host: str, credentials: DeviceCredentials, 
                                     commands: List[str], enable_mode: bool = False) -> List[SSHResult]:
        """
        Execute multiple commands on the same device
        """
        results = []
        
        try:
            # Get SSH connection
            ssh_client = await self._get_ssh_connection(host, credentials)
            
            if enable_mode and credentials.enable_password:
                await self._enter_enable_mode(ssh_client, credentials.enable_password)
            
            # Execute each command
            for command in commands:
                result = await self._execute_single_command(ssh_client, host, command)
                results.append(result)
                
                # If a command fails, decide whether to continue
                if not result.success:
                    logger.warning(f"Command failed on {host}: {command}")
                    
        except Exception as e:
            logger.error(f"Error executing multiple commands on {host}: {str(e)}")
            # Add error results for remaining commands
            for command in commands[len(results):]:
                results.append(SSHResult(
                    host=host,
                    command=command,
                    success=False,
                    output="",
                    error=str(e),
                    exit_code=None,
                    execution_time_ms=0,
                    timestamp=time.time()
                ))
        
        return results
    
    async def _execute_single_command(self, ssh_client, host: str, command: str) -> SSHResult:
        """Execute a single command using existing SSH connection"""
        start_time = time.time()
        
        try:
            stdin, stdout, stderr = ssh_client.exec_command(
                command, timeout=self.command_timeout
            )
            
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            execution_time = (time.time() - start_time) * 1000
            
            return SSHResult(
                host=host,
                command=command,
                success=exit_code == 0,
                output=output,
                error=error,
                exit_code=exit_code,
                execution_time_ms=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SSHResult(
                host=host,
                command=command,
                success=False,
                output="",
                error=str(e),
                exit_code=None,
                execution_time_ms=execution_time,
                timestamp=start_time
            )
    
    async def _get_ssh_connection(self, host: str, credentials: DeviceCredentials):
        """Get or create SSH connection"""
        connection_key = f"{host}:{credentials.port}:{credentials.username}"
        
        # Check if we have a cached connection
        if connection_key in self._connections:
            ssh_client = self._connections[connection_key]
            try:
                # Test if connection is still alive
                transport = ssh_client.get_transport()
                if transport and transport.is_alive():
                    return ssh_client
                else:
                    # Connection is dead, remove from cache
                    del self._connections[connection_key]
            except:
                # Connection is not usable, remove from cache
                if connection_key in self._connections:
                    del self._connections[connection_key]
        
        # Create new SSH connection
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                ssh_client.connect,
                host,
                credentials.port,
                credentials.username,
                credentials.password,
                self.connect_timeout
            )
            
            # Cache the connection for reuse
            self._connections[connection_key] = ssh_client
            return ssh_client
            
        except Exception as e:
            logger.error(f"Failed to connect to {host}: {str(e)}")
            raise
    
    async def _enter_enable_mode(self, ssh_client, enable_password: str):
        """Enter enable mode on Cisco devices"""
        try:
            # Create interactive shell
            shell = ssh_client.invoke_shell()
            
            # Send enable command
            shell.send("enable\n")
            time.sleep(1)
            
            # Send enable password
            shell.send(f"{enable_password}\n")
            time.sleep(1)
            
            # Read response to clear buffer
            if shell.recv_ready():
                shell.recv(1024)
                
        except Exception as e:
            logger.error(f"Failed to enter enable mode: {str(e)}")
            raise
    
    async def interactive_session(self, host: str, credentials: DeviceCredentials, 
                                commands: List[str]) -> List[str]:
        """
        Run commands in an interactive SSH session (for devices that need it)
        """
        try:
            ssh_client = await self._get_ssh_connection(host, credentials)
            
            # Create interactive shell
            shell = ssh_client.invoke_shell()
            time.sleep(2)  # Wait for shell to be ready
            
            outputs = []
            
            for command in commands:
                # Clear any existing output
                if shell.recv_ready():
                    shell.recv(4096)
                
                # Send command
                shell.send(f"{command}\n")
                time.sleep(2)  # Wait for command execution
                
                # Collect output
                output = ""
                while shell.recv_ready():
                    data = shell.recv(4096).decode('utf-8', errors='ignore')
                    output += data
                    time.sleep(0.1)
                
                outputs.append(output)
            
            shell.close()
            return outputs
            
        except Exception as e:
            logger.error(f"Interactive session error on {host}: {str(e)}")
            return [f"Error: {str(e)}"] * len(commands)
    
    def close_connection(self, host: str, port: int = 22, username: str = ""):
        """Close and remove cached SSH connection"""
        connection_key = f"{host}:{port}:{username}"
        if connection_key in self._connections:
            try:
                self._connections[connection_key].close()
            except:
                pass
            del self._connections[connection_key]
    
    def close_all_connections(self):
        """Close all cached SSH connections"""
        for ssh_client in self._connections.values():
            try:
                ssh_client.close()
            except:
                pass
        self._connections.clear()

class NetworkDeviceAutomation:
    """High-level automation for common network device operations"""
    
    def __init__(self, ssh_executor: SSHExecutor = None):
        self.ssh = ssh_executor or SSHExecutor()
    
    async def restart_interface(self, host: str, credentials: DeviceCredentials, 
                              interface: str, vendor: str = "cisco") -> Dict[str, Any]:
        """
        Restart a network interface
        """
        commands = self._get_interface_restart_commands(interface, vendor)
        
        results = await self.ssh.execute_multiple_commands(
            host, credentials, commands, enable_mode=True
        )
        
        # Analyze results
        success = all(result.success for result in results)
        
        return {
            "success": success,
            "interface": interface,
            "vendor": vendor,
            "commands_executed": [r.command for r in results],
            "outputs": [r.output for r in results],
            "errors": [r.error for r in results if r.error]
        }
    
    async def check_interface_status(self, host: str, credentials: DeviceCredentials, 
                                   interface: str = None, vendor: str = "cisco") -> Dict[str, Any]:
        """
        Check status of interfaces
        """
        if vendor.lower() == "cisco":
            if interface:
                command = f"show interface {interface}"
            else:
                command = "show ip interface brief"
        elif vendor.lower() == "juniper":
            if interface:
                command = f"show interfaces {interface}"
            else:
                command = "show interfaces terse"
        else:
            command = "show interfaces"
        
        result = await self.ssh.execute_command(host, credentials, command, enable_mode=True)
        
        return {
            "success": result.success,
            "command": command,
            "output": result.output,
            "error": result.error,
            "parsed_interfaces": self._parse_interface_output(result.output, vendor)
        }
    
    async def check_routing_table(self, host: str, credentials: DeviceCredentials, 
                                destination: str = None, vendor: str = "cisco") -> Dict[str, Any]:
        """
        Check routing table
        """
        if vendor.lower() == "cisco":
            if destination:
                command = f"show ip route {destination}"
            else:
                command = "show ip route"
        elif vendor.lower() == "juniper":
            if destination:
                command = f"show route {destination}"
            else:
                command = "show route"
        else:
            command = "show route"
        
        result = await self.ssh.execute_command(host, credentials, command, enable_mode=True)
        
        return {
            "success": result.success,
            "command": command,
            "output": result.output,
            "error": result.error
        }
    
    async def reload_routing_daemon(self, host: str, credentials: DeviceCredentials, 
                                  protocol: str = "ospf", vendor: str = "cisco") -> Dict[str, Any]:
        """
        Reload routing protocol
        """
        commands = self._get_routing_reload_commands(protocol, vendor)
        
        results = await self.ssh.execute_multiple_commands(
            host, credentials, commands, enable_mode=True
        )
        
        success = all(result.success for result in results)
        
        return {
            "success": success,
            "protocol": protocol,
            "vendor": vendor,
            "commands_executed": [r.command for r in results],
            "outputs": [r.output for r in results]
        }
    
    def _get_interface_restart_commands(self, interface: str, vendor: str) -> List[str]:
        """Get commands to restart an interface"""
        if vendor.lower() == "cisco":
            return [
                "configure terminal",
                f"interface {interface}",
                "shutdown",
                "no shutdown",
                "exit",
                "exit"
            ]
        elif vendor.lower() == "juniper":
            return [
                "configure",
                f"deactivate interfaces {interface}",
                "commit",
                f"activate interfaces {interface}",
                "commit",
                "exit"
            ]
        else:
            return [f"# Restart interface {interface} - vendor {vendor} not supported"]
    
    def _get_routing_reload_commands(self, protocol: str, vendor: str) -> List[str]:
        """Get commands to reload routing protocol"""
        if vendor.lower() == "cisco":
            if protocol.lower() == "ospf":
                return ["clear ip ospf process"]
            elif protocol.lower() == "bgp":
                return ["clear ip bgp *"]
            else:
                return [f"# Reload {protocol} - not implemented"]
        elif vendor.lower() == "juniper":
            return ["restart routing"]
        else:
            return [f"# Reload {protocol} for {vendor} - not supported"]
    
    def _parse_interface_output(self, output: str, vendor: str) -> List[Dict[str, Any]]:
        """Parse interface status output"""
        interfaces = []
        
        try:
            if vendor.lower() == "cisco" and "show ip interface brief" in output:
                lines = output.split('\n')
                for line in lines:
                    # Parse Cisco interface brief format
                    if 'YES' in line or 'NO' in line:
                        parts = line.split()
                        if len(parts) >= 6:
                            interfaces.append({
                                'interface': parts[0],
                                'ip_address': parts[1],
                                'ok': parts[2],
                                'method': parts[3],
                                'status': parts[4],
                                'protocol': parts[5]
                            })
        except Exception as e:
            logger.error(f"Error parsing interface output: {str(e)}")
        
        return interfaces

# Convenience functions
async def execute_ssh_command(host: str, username: str, password: str, 
                            command: str, port: int = 22, enable_password: str = None) -> SSHResult:
    """Simple SSH command execution"""
    executor = SSHExecutor()
    credentials = DeviceCredentials(
        username=username,
        password=password,
        enable_password=enable_password,
        port=port
    )
    
    return await executor.execute_command(host, credentials, command, enable_mode=bool(enable_password))

async def restart_device_interface(host: str, username: str, password: str, 
                                 interface: str, vendor: str = "cisco", 
                                 enable_password: str = None) -> Dict[str, Any]:
    """Simple interface restart"""
    automation = NetworkDeviceAutomation()
    credentials = DeviceCredentials(
        username=username,
        password=password,
        enable_password=enable_password
    )
    
    return await automation.restart_interface(host, credentials, interface, vendor)