"""
Slack Notification System for Network Troubleshooting Bot
Sends Slack alerts and notifications for network issues
"""
import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SlackConfig:
    webhook_url: str
    channel: str
    username: str = "Network Bot"
    icon_emoji: str = ":robot_face:"

@dataclass
class SlackMessage:
    text: str
    channel: Optional[str] = None
    username: Optional[str] = None
    icon_emoji: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    blocks: Optional[List[Dict[str, Any]]] = None

class SlackNotifier:
    def __init__(self, config: SlackConfig):
        self.config = config
    
    async def send_message(self, message: SlackMessage) -> bool:
        """Send message to Slack"""
        try:
            payload = {
                "text": message.text,
                "channel": message.channel or self.config.channel,
                "username": message.username or self.config.username,
                "icon_emoji": message.icon_emoji or self.config.icon_emoji
            }
            
            if message.attachments:
                payload["attachments"] = message.attachments
            
            if message.blocks:
                payload["blocks"] = message.blocks
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.webhook_url,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(payload)
                ) as response:
                    if response.status == 200:
                        logger.info("Slack message sent successfully")
                        return True
                    else:
                        logger.error(f"Slack message failed: {response.status} - {await response.text()}")
                        return False
        
        except Exception as e:
            logger.error(f"Error sending Slack message: {str(e)}")
            return False
    
    def create_alert_message(self, alert_type: str, device: str, 
                           details: Dict[str, Any], severity: str = "medium") -> SlackMessage:
        """Create a formatted alert message for Slack"""
        
        # Emoji and color based on severity
        severity_config = {
            "critical": {"emoji": ":rotating_light:", "color": "#FF0000"},
            "high": {"emoji": ":warning:", "color": "#FF6600"},
            "medium": {"emoji": ":exclamation:", "color": "#FFCC00"},
            "low": {"emoji": ":information_source:", "color": "#0099FF"}
        }
        
        config = severity_config.get(severity, severity_config["medium"])
        emoji = config["emoji"]
        color = config["color"]
        
        # Main message text
        text = f"{emoji} *Network Alert: {alert_type}*"
        
        # Create attachment with details
        attachment = {
            "color": color,
            "title": f"{alert_type} - {device}",
            "fields": [
                {
                    "title": "Severity",
                    "value": severity.upper(),
                    "short": True
                },
                {
                    "title": "Device",
                    "value": device,
                    "short": True
                },
                {
                    "title": "Timestamp",
                    "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "short": True
                }
            ],
            "footer": "Network Troubleshooting Bot",
            "ts": int(datetime.now().timestamp())
        }
        
        # Add detail fields
        for key, value in details.items():
            attachment["fields"].append({
                "title": key,
                "value": str(value),
                "short": len(str(value)) < 30
            })
        
        return SlackMessage(
            text=text,
            attachments=[attachment]
        )
    
    def create_ping_failure_alert(self, target: str, packet_loss: float, 
                                avg_latency: Optional[float] = None) -> SlackMessage:
        """Create ping failure alert"""
        
        details = {
            "Target": target,
            "Packet Loss": f"{packet_loss}%"
        }
        
        if avg_latency is not None:
            details["Average Latency"] = f"{avg_latency:.2f}ms"
        
        severity = "critical" if packet_loss >= 50 else "high" if packet_loss >= 20 else "medium"
        
        return self.create_alert_message("Ping Failure", target, details, severity)
    
    def create_interface_down_alert(self, device: str, interface: str, 
                                  duration: Optional[str] = None) -> SlackMessage:
        """Create interface down alert"""
        
        details = {
            "Interface": interface,
            "Status": "DOWN"
        }
        
        if duration:
            details["Down Duration"] = duration
        
        return self.create_alert_message("Interface Down", device, details, "high")
    
    def create_device_unreachable_alert(self, device: str, 
                                      last_seen: Optional[str] = None) -> SlackMessage:
        """Create device unreachable alert"""
        
        details = {
            "Status": "UNREACHABLE",
            "Last Ping": "Failed"
        }
        
        if last_seen:
            details["Last Seen"] = last_seen
        
        return self.create_alert_message("Device Unreachable", device, details, "critical")
    
    def create_high_cpu_alert(self, device: str, cpu_usage: float, 
                            threshold: float = 90) -> SlackMessage:
        """Create high CPU usage alert"""
        
        details = {
            "CPU Usage": f"{cpu_usage:.1f}%",
            "Threshold": f"{threshold}%",
            "Exceeded By": f"{cpu_usage - threshold:.1f}%"
        }
        
        severity = "critical" if cpu_usage >= 95 else "high"
        
        return self.create_alert_message("High CPU Usage", device, details, severity)
    
    def create_troubleshooting_report(self, session_id: str, 
                                    issues_found: List[Dict[str, Any]], 
                                    actions_taken: List[Dict[str, Any]]) -> SlackMessage:
        """Create troubleshooting session report"""
        
        text = f":clipboard: *Troubleshooting Session Complete*"
        
        # Create blocks for rich formatting
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Troubleshooting Session Summary"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Session ID:*\n{session_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Timestamp:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
        
        # Add issues section
        if issues_found:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Issues Found ({len(issues_found)}):*"
                }
            })
            
            for i, issue in enumerate(issues_found[:5], 1):  # Limit to 5 issues
                severity_emoji = {
                    'critical': ':rotating_light:',
                    'high': ':warning:',
                    'medium': ':exclamation:',
                    'low': ':information_source:'
                }.get(issue.get('severity', '').lower(), ':question:')
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{severity_emoji} {issue.get('description', 'Unknown issue')}\n" +
                               f"_Device: {issue.get('device', 'Unknown')} | " +
                               f"Severity: {issue.get('severity', 'Unknown')}_"
                    }
                })
        
        # Add actions section
        if actions_taken:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Actions Taken ({len(actions_taken)}):*"
                }
            })
            
            for i, action in enumerate(actions_taken[:5], 1):  # Limit to 5 actions
                status_emoji = ':white_check_mark:' if action.get('status') == 'success' else ':x:'
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{status_emoji} {action.get('description', 'Unknown action')}\n" +
                               f"_Status: {action.get('status', 'Unknown')}_"
                    }
                })
        
        # Add footer
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Generated by Network Troubleshooting Bot"
                }
            ]
        })
        
        return SlackMessage(
            text=text,
            blocks=blocks
        )
    
    def create_status_update(self, message: str, status_type: str = "info") -> SlackMessage:
        """Create a simple status update message"""
        
        emoji_map = {
            "info": ":information_source:",
            "success": ":white_check_mark:",
            "warning": ":warning:",
            "error": ":x:"
        }
        
        emoji = emoji_map.get(status_type, ":information_source:")
        text = f"{emoji} {message}"
        
        return SlackMessage(text=text)
    
    def create_interactive_troubleshooting_message(self, issue: str, 
                                                 suggested_actions: List[str]) -> SlackMessage:
        """Create interactive message with action buttons"""
        
        text = f":thinking_face: *Troubleshooting Assistance Needed*"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Network Issue Detected"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Issue:* {issue}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Suggested Actions:*"
                }
            }
        ]
        
        # Add action buttons (limit to 5)
        if suggested_actions:
            actions_element = {
                "type": "actions",
                "elements": []
            }
            
            for i, action in enumerate(suggested_actions[:5]):
                actions_element["elements"].append({
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": action[:75]  # Slack button text limit
                    },
                    "value": f"action_{i}",
                    "action_id": f"troubleshoot_action_{i}"
                })
            
            blocks.append(actions_element)
        
        return SlackMessage(
            text=text,
            blocks=blocks
        )
    
    async def send_alert(self, alert_type: str, device: str, details: Dict[str, Any], 
                        severity: str = "medium") -> bool:
        """Convenience method to send an alert"""
        message = self.create_alert_message(alert_type, device, details, severity)
        return await self.send_message(message)
    
    async def send_status_update(self, message: str, status_type: str = "info") -> bool:
        """Convenience method to send a status update"""
        slack_message = self.create_status_update(message, status_type)
        return await self.send_message(slack_message)

# Convenience functions
def create_slack_notifier_from_config(config_dict: Dict[str, Any]) -> SlackNotifier:
    """Create SlackNotifier from configuration dictionary"""
    slack_config = SlackConfig(
        webhook_url=config_dict.get('webhook_url', ''),
        channel=config_dict.get('channel', '#network-alerts'),
        username=config_dict.get('username', 'Network Bot'),
        icon_emoji=config_dict.get('icon_emoji', ':robot_face:')
    )
    
    return SlackNotifier(slack_config)

async def send_quick_slack_alert(webhook_url: str, channel: str, 
                                message: str, severity: str = "info") -> bool:
    """Quick function to send a Slack alert"""
    config = SlackConfig(
        webhook_url=webhook_url,
        channel=channel
    )
    
    notifier = SlackNotifier(config)
    slack_message = notifier.create_status_update(message, severity)
    return await notifier.send_message(slack_message)