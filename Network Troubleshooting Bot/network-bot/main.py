"""
Main FastAPI Application for Network Troubleshooting Bot
Provides REST API endpoints for network diagnostics, troubleshooting, and chat interface
"""
import asyncio
import os
import yaml
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import our modules
from modules import (
    PingTester, TracerouteTester, SNMPMonitor, SSHExecutor, NetworkLogParser,
    DeviceCredentials, ping_host, traceroute_host, get_device_snmp_info
)
from ai import NetworkIntentHandler, NetworkRulesEngine, process_user_query, troubleshoot_issue
from db.models import DatabaseManager, Device, TestResult, Alert, UserQuery, NetworkMetric
from integrations.email_notify import EmailNotifier
from integrations.slack_alerts import SlackNotifier
from integrations.telegram_bot import TelegramNotifier

# Load configuration
def load_config():
    config_path = os.path.join("config", "config.yaml")
    devices_path = os.path.join("config", "devices.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    with open(devices_path, 'r') as f:
        devices_config = yaml.safe_load(f)
    
    return config, devices_config

# Global variables
config, devices_config = load_config()
db_manager = DatabaseManager()
intent_handler = NetworkIntentHandler(openai_api_key=os.getenv("OPENAI_API_KEY"))
rules_engine = NetworkRulesEngine()

# Initialize database
db_manager.create_tables()

# Pydantic models for API
class PingRequest(BaseModel):
    target: str = Field(..., description="IP address or hostname to ping")
    timeout: int = Field(5, description="Timeout in seconds")
    count: int = Field(4, description="Number of ping packets")

class TracerouteRequest(BaseModel):
    target: str = Field(..., description="IP address or hostname for traceroute")
    max_hops: int = Field(30, description="Maximum number of hops")
    timeout: int = Field(5, description="Timeout in seconds")

class SNMPRequest(BaseModel):
    target: str = Field(..., description="IP address or hostname for SNMP")
    community: str = Field("public", description="SNMP community string")

class SSHRequest(BaseModel):
    host: str = Field(..., description="Device IP address or hostname")
    username: str = Field(..., description="SSH username")
    password: str = Field(..., description="SSH password")
    command: str = Field(..., description="Command to execute")
    enable_password: Optional[str] = Field(None, description="Enable password for privilege escalation")

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    user_id: str = Field("web_user", description="User identifier")
    channel: str = Field("web", description="Communication channel")

class DeviceStatusRequest(BaseModel):
    device_id: Optional[int] = Field(None, description="Database device ID")
    ip_address: Optional[str] = Field(None, description="Device IP address")

class InterfaceActionRequest(BaseModel):
    device_ip: str = Field(..., description="Device IP address")
    interface: str = Field(..., description="Interface name")
    action: str = Field(..., description="Action to perform (restart, check)")
    credentials: Dict[str, str] = Field(..., description="Device credentials")

# FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Network Troubleshooting Bot starting up...")
    yield
    # Shutdown
    print("👋 Network Troubleshooting Bot shutting down...")

app = FastAPI(
    title="Network Troubleshooting Bot API",
    description="AI-powered network diagnostic and troubleshooting API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Network Troubleshooting Bot API",
        "docs_url": "/docs",
        "health_url": "/health"
    }

# Ping endpoints
@app.post("/api/ping")
async def ping_endpoint(request: PingRequest):
    """Perform ping test to target host"""
    try:
        result = await ping_host(request.target, request.timeout, request.count)
        
        # Store result in database
        session = db_manager.get_session()
        try:
            test_result = TestResult(
                test_type="ping",
                target=request.target,
                status="success" if result.success else "failed",
                latency_ms=result.avg_latency_ms,
                packet_loss=result.packet_loss_percent,
                details={
                    "packets_sent": result.packets_sent,
                    "packets_received": result.packets_received,
                    "min_latency_ms": result.min_latency_ms,
                    "max_latency_ms": result.max_latency_ms
                },
                error_message=result.error_message
            )
            session.add(test_result)
            session.commit()
        finally:
            session.close()
        
        return {
            "success": result.success,
            "target": result.target,
            "packets_sent": result.packets_sent,
            "packets_received": result.packets_received,
            "packet_loss_percent": result.packet_loss_percent,
            "latency": {
                "min_ms": result.min_latency_ms,
                "max_ms": result.max_latency_ms,
                "avg_ms": result.avg_latency_ms
            },
            "error_message": result.error_message,
            "timestamp": result.timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Traceroute endpoints
@app.post("/api/traceroute")
async def traceroute_endpoint(request: TracerouteRequest):
    """Perform traceroute to target host"""
    try:
        result = await traceroute_host(request.target, request.max_hops, request.timeout)
        
        # Store result in database
        session = db_manager.get_session()
        try:
            test_result = TestResult(
                test_type="traceroute",
                target=request.target,
                status="success" if result.success else "failed",
                details={
                    "total_hops": result.total_hops,
                    "target_reached": result.target_reached,
                    "hops": [
                        {
                            "hop_number": hop.hop_number,
                            "ip_address": hop.ip_address,
                            "hostname": hop.hostname,
                            "latency_ms": hop.latency_ms,
                            "timeout": hop.timeout
                        }
                        for hop in result.hops
                    ]
                },
                error_message=result.error_message
            )
            session.add(test_result)
            session.commit()
        finally:
            session.close()
        
        return {
            "success": result.success,
            "target": result.target,
            "total_hops": result.total_hops,
            "target_reached": result.target_reached,
            "hops": [
                {
                    "hop_number": hop.hop_number,
                    "ip_address": hop.ip_address,
                    "hostname": hop.hostname,
                    "latency_ms": hop.latency_ms,
                    "timeout": hop.timeout,
                    "error_message": hop.error_message
                }
                for hop in result.hops
            ],
            "execution_time_ms": result.execution_time_ms,
            "error_message": result.error_message,
            "timestamp": result.timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# SNMP endpoints
@app.post("/api/snmp")
async def snmp_endpoint(request: SNMPRequest):
    """Get SNMP information from device"""
    try:
        result = await get_device_snmp_info(request.target, request.community)
        
        # Store result in database
        session = db_manager.get_session()
        try:
            test_result = TestResult(
                test_type="snmp",
                target=request.target,
                status="success" if result.success else "failed",
                latency_ms=result.response_time_ms,
                details={
                    "device_info": {
                        "system_description": result.device_info.system_description if result.device_info else None,
                        "system_name": result.device_info.system_name if result.device_info else None,
                        "system_uptime": result.device_info.system_uptime if result.device_info else None,
                        "cpu_usage_percent": result.device_info.cpu_usage_percent if result.device_info else None,
                        "memory_usage_percent": result.device_info.memory_usage_percent if result.device_info else None
                    } if result.device_info else None,
                    "interface_count": len(result.interfaces),
                    "interfaces": [
                        {
                            "name": iface.interface_name,
                            "admin_status": iface.admin_status,
                            "oper_status": iface.oper_status,
                            "speed_bps": iface.speed_bps,
                            "utilization_in_percent": iface.utilization_in_percent,
                            "utilization_out_percent": iface.utilization_out_percent
                        }
                        for iface in result.interfaces[:10]  # Limit to first 10 interfaces
                    ]
                },
                error_message=result.error_message
            )
            session.add(test_result)
            session.commit()
        finally:
            session.close()
        
        return {
            "success": result.success,
            "target": result.target,
            "device_info": {
                "system_description": result.device_info.system_description,
                "system_name": result.device_info.system_name,
                "system_uptime": result.device_info.system_uptime,
                "system_contact": result.device_info.system_contact,
                "system_location": result.device_info.system_location,
                "cpu_usage_percent": result.device_info.cpu_usage_percent,
                "memory_usage_percent": result.device_info.memory_usage_percent
            } if result.device_info else None,
            "interfaces": [
                {
                    "interface_name": iface.interface_name,
                    "interface_index": iface.interface_index,
                    "admin_status": iface.admin_status,
                    "oper_status": iface.oper_status,
                    "speed_bps": iface.speed_bps,
                    "mtu": iface.mtu,
                    "bytes_in": iface.bytes_in,
                    "bytes_out": iface.bytes_out,
                    "errors_in": iface.errors_in,
                    "errors_out": iface.errors_out,
                    "utilization_in_percent": iface.utilization_in_percent,
                    "utilization_out_percent": iface.utilization_out_percent
                }
                for iface in result.interfaces
            ],
            "response_time_ms": result.response_time_ms,
            "error_message": result.error_message,
            "timestamp": result.timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# SSH execution endpoints
@app.post("/api/ssh/execute")
async def ssh_execute_endpoint(request: SSHRequest):
    """Execute SSH command on remote device"""
    try:
        executor = SSHExecutor()
        credentials = DeviceCredentials(
            username=request.username,
            password=request.password,
            enable_password=request.enable_password
        )
        
        result = await executor.execute_command(
            request.host, 
            credentials, 
            request.command,
            enable_mode=bool(request.enable_password)
        )
        
        return {
            "success": result.success,
            "host": result.host,
            "command": result.command,
            "output": result.output,
            "error": result.error,
            "exit_code": result.exit_code,
            "execution_time_ms": result.execution_time_ms,
            "timestamp": result.timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chat/AI endpoints
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    """Process natural language query and provide troubleshooting assistance"""
    try:
        start_time = time.time()
        
        # Process query with intent handler
        intent_result = intent_handler.process_query(request.message)
        
        # Store query in database
        session = db_manager.get_session()
        processing_time = (time.time() - start_time) * 1000
        
        try:
            user_query = UserQuery(
                user_id=request.user_id,
                channel=request.channel,
                query_text=request.message,
                intent=intent_result.intent.value,
                response="",  # Will be updated after processing
                status="processing",
                processing_time_ms=processing_time
            )
            session.add(user_query)
            session.commit()
            query_id = user_query.id
        finally:
            session.close()
        
        # Generate response based on intent
        response = await process_intent(intent_result)
        
        # Update query record with response
        session = db_manager.get_session()
        try:
            query_record = session.query(UserQuery).get(query_id)
            if query_record:
                query_record.response = response.get("message", "")
                query_record.status = "processed"
                query_record.processing_time_ms = (time.time() - start_time) * 1000
                session.commit()
        finally:
            session.close()
        
        return {
            "query": request.message,
            "intent": intent_result.intent.value,
            "confidence": intent_result.confidence,
            "entities": intent_result.entities,
            "response": response,
            "suggested_action": intent_result.suggested_action,
            "processing_time_ms": (time.time() - start_time) * 1000
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_intent(intent_result):
    """Process intent and execute appropriate actions"""
    try:
        if intent_result.intent.value == "ping_test":
            target = intent_result.entities.get('ip_address') or intent_result.entities.get('hostname')
            if target:
                ping_result = await ping_host(target)
                return {
                    "message": f"Ping test to {target}: {'✅ Success' if ping_result.success else '❌ Failed'}",
                    "details": {
                        "target": ping_result.target,
                        "success": ping_result.success,
                        "packet_loss": ping_result.packet_loss_percent,
                        "avg_latency_ms": ping_result.avg_latency_ms
                    },
                    "action_taken": "ping_test"
                }
            else:
                return {
                    "message": "Please specify a target IP address or hostname for ping test.",
                    "suggestion": "Example: 'ping 8.8.8.8' or 'ping google.com'"
                }
        
        elif intent_result.intent.value == "traceroute":
            target = intent_result.entities.get('ip_address') or intent_result.entities.get('hostname')
            if target:
                trace_result = await traceroute_host(target)
                return {
                    "message": f"Traceroute to {target}: {'✅ Completed' if trace_result.success else '❌ Failed'}",
                    "details": {
                        "target": trace_result.target,
                        "success": trace_result.success,
                        "total_hops": trace_result.total_hops,
                        "target_reached": trace_result.target_reached,
                        "hops": trace_result.hops[:5]  # First 5 hops
                    },
                    "action_taken": "traceroute"
                }
            else:
                return {
                    "message": "Please specify a target IP address or hostname for traceroute.",
                    "suggestion": "Example: 'traceroute google.com'"
                }
        
        elif intent_result.intent.value == "general_help":
            return {
                "message": intent_handler.get_help_text(),
                "action_taken": "help"
            }
        
        else:
            return {
                "message": f"I understand you want to {intent_result.suggested_action}, but I need more information to proceed.",
                "suggestions": intent_handler.get_follow_up_questions(intent_result),
                "action_taken": "clarification_needed"
            }
    
    except Exception as e:
        return {
            "message": f"Sorry, I encountered an error while processing your request: {str(e)}",
            "action_taken": "error"
        }

# Device management endpoints
@app.get("/api/devices")
async def list_devices():
    """List all configured devices"""
    session = db_manager.get_session()
    try:
        devices = session.query(Device).all()
        return [
            {
                "id": device.id,
                "name": device.name,
                "ip_address": device.ip_address,
                "device_type": device.device_type,
                "vendor": device.vendor,
                "model": device.model,
                "location": device.location,
                "status": device.status,
                "created_at": device.created_at,
                "updated_at": device.updated_at
            }
            for device in devices
        ]
    finally:
        session.close()

@app.post("/api/devices/status")
async def check_device_status(request: DeviceStatusRequest):
    """Check status of a specific device"""
    try:
        # Determine device IP
        if request.device_id:
            session = db_manager.get_session()
            try:
                device = session.query(Device).get(request.device_id)
                if not device:
                    raise HTTPException(status_code=404, detail="Device not found")
                device_ip = device.ip_address
            finally:
                session.close()
        elif request.ip_address:
            device_ip = request.ip_address
        else:
            raise HTTPException(status_code=400, detail="Either device_id or ip_address must be provided")
        
        # Run multiple tests
        ping_result = await ping_host(device_ip)
        snmp_result = await get_device_snmp_info(device_ip)
        
        # Determine overall status
        device_status = "online" if ping_result.success else "offline"
        
        return {
            "device_ip": device_ip,
            "status": device_status,
            "ping_test": {
                "success": ping_result.success,
                "latency_ms": ping_result.avg_latency_ms,
                "packet_loss_percent": ping_result.packet_loss_percent
            },
            "snmp_test": {
                "success": snmp_result.success,
                "response_time_ms": snmp_result.response_time_ms,
                "device_info": {
                    "system_name": snmp_result.device_info.system_name if snmp_result.device_info else None,
                    "system_uptime": snmp_result.device_info.system_uptime if snmp_result.device_info else None,
                    "cpu_usage_percent": snmp_result.device_info.cpu_usage_percent if snmp_result.device_info else None
                } if snmp_result.success and snmp_result.device_info else None
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Interface management endpoints
@app.post("/api/interface/{action}")
async def interface_action(action: str, request: InterfaceActionRequest):
    """Perform actions on network interfaces"""
    try:
        if action not in ["check", "restart"]:
            raise HTTPException(status_code=400, detail="Action must be 'check' or 'restart'")
        
        # For demonstration, we'll simulate interface actions
        # In a real implementation, this would use SSH to execute commands
        
        return {
            "success": True,
            "device_ip": request.device_ip,
            "interface": request.interface,
            "action": action,
            "message": f"Interface {request.interface} {action} completed successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Troubleshooting endpoints
@app.post("/api/troubleshoot")
async def troubleshoot_endpoint(issue_data: Dict[str, Any]):
    """Run automated troubleshooting based on issue data"""
    try:
        result = troubleshoot_issue(issue_data, auto_execute=False)
        
        return {
            "issue_identified": result.issue_identified,
            "root_cause": result.root_cause,
            "severity": result.severity.value,
            "recommended_actions": [
                {
                    "action_type": action.action_type.value,
                    "command": action.command,
                    "description": action.description,
                    "confirmation_required": action.confirmation_required
                }
                for action in result.recommended_actions
            ],
            "automated_actions_taken": result.automated_actions_taken,
            "manual_intervention_required": result.manual_intervention_required,
            "escalation_needed": result.escalation_needed,
            "summary": result.summary
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics endpoints
@app.get("/api/analytics/summary")
async def analytics_summary():
    """Get analytics summary"""
    session = db_manager.get_session()
    try:
        # Get test counts by type
        test_counts = {}
        test_results = session.query(TestResult).all()
        
        for result in test_results:
            test_type = result.test_type
            if test_type not in test_counts:
                test_counts[test_type] = {"total": 0, "success": 0, "failed": 0}
            
            test_counts[test_type]["total"] += 1
            if result.status == "success":
                test_counts[test_type]["success"] += 1
            else:
                test_counts[test_type]["failed"] += 1
        
        # Get alert counts
        alert_counts = {}
        alerts = session.query(Alert).all()
        for alert in alerts:
            severity = alert.severity
            if severity not in alert_counts:
                alert_counts[severity] = 0
            alert_counts[severity] += 1
        
        return {
            "test_summary": test_counts,
            "alert_summary": alert_counts,
            "total_devices": session.query(Device).count(),
            "active_alerts": session.query(Alert).filter(Alert.status == 'open').count(),
            "timestamp": datetime.now().isoformat()
        }
    
    finally:
        session.close()

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    # Load configuration for uvicorn
    host = config.get("app", {}).get("host", "0.0.0.0")
    port = config.get("app", {}).get("port", 8000)
    debug = config.get("app", {}).get("debug", False)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )