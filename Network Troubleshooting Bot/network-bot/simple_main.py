#!/usr/bin/env python3
"""
Network Troubleshooting Bot - Simplified Main Application
FastAPI server with core network diagnostic capabilities
"""

import asyncio
import sys
import os
from typing import Optional, Dict, Any, List

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    print("FastAPI not available. Please install: pip install fastapi uvicorn")
    FASTAPI_AVAILABLE = False
    # Define dummy BaseModel to prevent errors
    class BaseModel:
        pass

# Core network modules (should work without external dependencies)
try:
    from modules.ping_test import ping_host, PingResult
    PING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Ping module not available: {e}")
    PING_AVAILABLE = False

try:
    from modules.traceroute import traceroute_host
    TRACEROUTE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Traceroute module not available: {e}")
    TRACEROUTE_AVAILABLE = False

try:
    from modules.log_parser import parse_log_content
    LOG_PARSER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Log parser not available: {e}")
    LOG_PARSER_AVAILABLE = False

# Request/Response Models
class PingRequest(BaseModel):
    target: str
    count: Optional[int] = 4
    timeout: Optional[int] = 5

class TracerouteRequest(BaseModel):
    target: str
    max_hops: Optional[int] = 30
    timeout: Optional[int] = 5

class ChatRequest(BaseModel):
    message: str

class HealthResponse(BaseModel):
    status: str
    version: str
    available_modules: Dict[str, bool]

# Initialize FastAPI app
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Network Troubleshooting Bot API",
        description="AI-powered network diagnostics and troubleshooting",
        version="1.0.0"
    )
    
    @app.get("/")
    async def root():
        return {
            "message": "Network Troubleshooting Bot API", 
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            available_modules={
                "ping": PING_AVAILABLE,
                "traceroute": TRACEROUTE_AVAILABLE,
                "log_parser": LOG_PARSER_AVAILABLE,
                "fastapi": FASTAPI_AVAILABLE
            }
        )
    
    if PING_AVAILABLE:
        @app.post("/api/ping")
        async def ping_endpoint(request: PingRequest):
            """Execute ping test to specified target"""
            try:
                result = await ping_host(request.target, request.timeout, request.count)
                return {
                    "success": result.success,
                    "target": request.target,
                    "packets_sent": result.packets_sent,
                    "packets_received": result.packets_received,
                    "packet_loss_percent": result.packet_loss_percent,
                    "avg_latency_ms": result.avg_latency_ms,
                    "min_latency_ms": result.min_latency_ms,
                    "max_latency_ms": result.max_latency_ms,
                    "error_message": result.error_message
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ping failed: {str(e)}")
    
    if TRACEROUTE_AVAILABLE:
        @app.post("/api/traceroute")
        async def traceroute_endpoint(request: TracerouteRequest):
            """Execute traceroute to specified target"""
            try:
                result = await traceroute_host(request.target, request.max_hops, request.timeout)
                return {
                    "success": result.success,
                    "target": request.target,
                    "total_hops": result.total_hops,
                    "target_reached": result.target_reached,
                    "execution_time_ms": result.execution_time_ms,
                    "hops": [
                        {
                            "hop_number": hop.hop_number,
                            "ip_address": hop.ip_address,
                            "hostname": hop.hostname,
                            "latency_ms": hop.latency_ms,
                            "timeout": hop.timeout
                        }
                        for hop in result.hops
                    ],
                    "error_message": result.error_message
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Traceroute failed: {str(e)}")
    
    @app.post("/api/chat")
    async def chat_endpoint(request: ChatRequest):
        """Simple chat interface for network troubleshooting"""
        message = request.message.lower()
        
        # Simple pattern matching for basic commands
        if "ping" in message:
            # Extract target from message
            words = message.split()
            target = None
            for i, word in enumerate(words):
                if word == "ping" and i + 1 < len(words):
                    target = words[i + 1]
                    break
            
            if target and PING_AVAILABLE:
                try:
                    result = await ping_host(target, timeout=3, count=2)
                    if result.success:
                        return {
                            "response": f"Ping to {target} successful! Average latency: {result.avg_latency_ms:.1f}ms, Packet loss: {result.packet_loss_percent:.0f}%",
                            "action_taken": "ping_test",
                            "result": "success"
                        }
                    else:
                        return {
                            "response": f"Ping to {target} failed: {result.error_message}",
                            "action_taken": "ping_test", 
                            "result": "failed"
                        }
                except Exception as e:
                    return {
                        "response": f"Error executing ping to {target}: {str(e)}",
                        "action_taken": "ping_test",
                        "result": "error"
                    }
            else:
                return {
                    "response": "I can help you ping a target. Please specify the target IP or hostname. Example: 'ping google.com'",
                    "action_taken": "none",
                    "result": "help"
                }
        
        elif "traceroute" in message or "trace" in message:
            # Extract target from message
            words = message.split()
            target = None
            for i, word in enumerate(words):
                if word in ["traceroute", "trace"] and i + 1 < len(words):
                    target = words[i + 1]
                    break
            
            if target and TRACEROUTE_AVAILABLE:
                try:
                    result = await traceroute_host(target, max_hops=15, timeout=3)
                    if result.success:
                        return {
                            "response": f"Traceroute to {target} completed! {result.total_hops} hops, target {'reached' if result.target_reached else 'not reached'}",
                            "action_taken": "traceroute_test",
                            "result": "success"
                        }
                    else:
                        return {
                            "response": f"Traceroute to {target} failed: {result.error_message}",
                            "action_taken": "traceroute_test",
                            "result": "failed"
                        }
                except Exception as e:
                    return {
                        "response": f"Error executing traceroute to {target}: {str(e)}",
                        "action_taken": "traceroute_test",
                        "result": "error"
                    }
            else:
                return {
                    "response": "I can help you trace the route to a target. Please specify the target. Example: 'traceroute google.com'",
                    "action_taken": "none",
                    "result": "help"
                }
        
        elif "help" in message:
            available_commands = []
            if PING_AVAILABLE:
                available_commands.append("ping <target>")
            if TRACEROUTE_AVAILABLE:
                available_commands.append("traceroute <target>")
            
            commands_str = ", ".join(available_commands) if available_commands else "No commands available"
            
            return {
                "response": f"I can help you with network troubleshooting. Available commands: {commands_str}. You can also ask general questions about network connectivity.",
                "action_taken": "help",
                "result": "info"
            }
        
        else:
            return {
                "response": "I'm a network troubleshooting bot. I can help you with ping tests, traceroute, and network diagnostics. Try asking 'ping google.com' or 'help' for more information.",
                "action_taken": "general_response",
                "result": "info"
            }

    @app.get("/api/status")
    async def status():
        """Get server status and available modules"""
        return {
            "server": "running",
            "modules": {
                "ping": PING_AVAILABLE,
                "traceroute": TRACEROUTE_AVAILABLE,
                "log_parser": LOG_PARSER_AVAILABLE
            },
            "endpoints": {
                "health": "/health",
                "ping": "/api/ping" if PING_AVAILABLE else None,
                "traceroute": "/api/traceroute" if TRACEROUTE_AVAILABLE else None,
                "chat": "/api/chat",
                "docs": "/docs"
            }
        }

def main():
    """Main application entry point"""
    print("Network Troubleshooting Bot - Starting...")
    print("=" * 50)
    
    if not FASTAPI_AVAILABLE:
        print("FastAPI not available. Please install required dependencies:")
        print("pip install fastapi uvicorn")
        return
    
    print(f"Available modules:")
    print(f"  - Ping: {'Yes' if PING_AVAILABLE else 'No'}")
    print(f"  - Traceroute: {'Yes' if TRACEROUTE_AVAILABLE else 'No'}")
    print(f"  - Log Parser: {'Yes' if LOG_PARSER_AVAILABLE else 'No'}")
    
    print(f"\nStarting API server...")
    print(f"API Documentation: http://localhost:8000/docs")
    print(f"Health Check: http://localhost:8000/health")
    print(f"Status: http://localhost:8000/api/status")
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()