"""
Telegram Bot Integration for Network Troubleshooting Bot
Provides conversational interface via Telegram
"""
import asyncio
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logging.warning("python-telegram-bot not available. Telegram functionality disabled.")

from ai import process_user_query
from modules import ping_host, traceroute_host

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, bot_token: str, authorized_users: List[int] = None):
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot is required for Telegram functionality")
        
        self.bot_token = bot_token
        self.authorized_users = authorized_users or []
        self.application = None
        self.troubleshooting_sessions = {}
        
    def setup_bot(self):
        """Setup the Telegram bot application"""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("ping", self.ping_command))
        self.application.add_handler(CommandHandler("traceroute", self.traceroute_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized to use the bot"""
        if not self.authorized_users:
            return True  # If no restrictions, allow all users
        return user_id in self.authorized_users
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("❌ Sorry, you are not authorized to use this bot.")
            return
        
        welcome_message = """
🤖 Welcome to Network Troubleshooting Bot!

I can help you diagnose and troubleshoot network issues. Here's what I can do:

🔍 **Network Testing:**
• `/ping <target>` - Test connectivity to a host
• `/traceroute <target>` - Trace network path
• `/status` - Get bot status

💬 **Natural Language:**
Just describe your network issue and I'll help! Examples:
• "Check connectivity to 8.8.8.8"
• "Why can't I reach google.com?"
• "Interface eth0 is down, what should I do?"

ℹ️ Use `/help` for more information.
        """
        
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        help_message = """
🤖 **Network Troubleshooting Bot Help**

**Commands:**
• `/start` - Start the bot and get welcome message
• `/help` - Show this help message
• `/ping <target>` - Ping a host (IP or domain)
• `/traceroute <target>` - Traceroute to a host
• `/status` - Show bot status

**Natural Language Queries:**
You can also just talk to me naturally! Examples:

🔍 **Connectivity Testing:**
• "ping 8.8.8.8"
• "test connectivity to google.com"
• "is server1 reachable?"

📊 **Network Analysis:**
• "traceroute to 1.1.1.1"
• "show path to cloudflare.com"
• "check route to server"

🔧 **Troubleshooting:**
• "interface eth0 is down"
• "high latency to server"
• "packet loss issues"

💡 **Tips:**
• Be specific with IP addresses or hostnames
• Describe symptoms clearly for better assistance
• I can suggest troubleshooting steps based on your issues

Just type your question or issue, and I'll help you troubleshoot it!
        """
        
        await update.message.reply_text(help_message)
    
    async def ping_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ping command"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Please provide a target to ping.\nUsage: `/ping <target>`\nExample: `/ping 8.8.8.8`")
            return
        
        target = context.args[0]
        
        # Send "working" message
        working_msg = await update.message.reply_text(f"🔄 Pinging {target}...")
        
        try:
            result = await ping_host(target)
            
            if result.success:
                message = f"""
✅ **Ping to {target} - SUCCESS**

📊 **Statistics:**
• Packets Sent: {result.packets_sent}
• Packets Received: {result.packets_received}
• Packet Loss: {result.packet_loss_percent:.1f}%

⏱️ **Latency:**
• Min: {result.min_latency_ms:.2f}ms
• Max: {result.max_latency_ms:.2f}ms
• Avg: {result.avg_latency_ms:.2f}ms

🕐 Timestamp: {datetime.fromtimestamp(result.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
                """
            else:
                message = f"""
❌ **Ping to {target} - FAILED**

📊 **Statistics:**
• Packets Sent: {result.packets_sent}
• Packets Received: {result.packets_received}
• Packet Loss: {result.packet_loss_percent:.1f}%

⚠️ **Error:** {result.error_message or 'Unknown error'}

🕐 Timestamp: {datetime.fromtimestamp(result.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
                """
            
            await context.bot.edit_message_text(
                chat_id=working_msg.chat_id,
                message_id=working_msg.message_id,
                text=message
            )
            
        except Exception as e:
            await context.bot.edit_message_text(
                chat_id=working_msg.chat_id,
                message_id=working_msg.message_id,
                text=f"❌ Error performing ping: {str(e)}"
            )
    
    async def traceroute_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /traceroute command"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Please provide a target for traceroute.\nUsage: `/traceroute <target>`\nExample: `/traceroute google.com`")
            return
        
        target = context.args[0]
        
        # Send "working" message
        working_msg = await update.message.reply_text(f"🔄 Running traceroute to {target}...")
        
        try:
            result = await traceroute_host(target)
            
            if result.success:
                message = f"✅ **Traceroute to {target}**\n\n"
                message += f"🎯 Target Reached: {'Yes' if result.target_reached else 'No'}\n"
                message += f"📊 Total Hops: {result.total_hops}\n\n"
                
                message += "🛤️ **Route Path:**\n"
                for hop in result.hops[:10]:  # Limit to first 10 hops
                    if hop.timeout:
                        message += f"{hop.hop_number:2d}. * * * (timeout)\n"
                    else:
                        avg_latency = sum(hop.latency_ms) / len(hop.latency_ms) if hop.latency_ms else 0
                        ip_display = hop.ip_address or "unknown"
                        hostname_display = f" ({hop.hostname})" if hop.hostname and hop.hostname != hop.ip_address else ""
                        message += f"{hop.hop_number:2d}. {ip_display}{hostname_display} - {avg_latency:.2f}ms\n"
                
                if result.total_hops > 10:
                    message += f"... and {result.total_hops - 10} more hops\n"
                
                message += f"\n🕐 Execution Time: {result.execution_time_ms:.0f}ms"
            else:
                message = f"❌ **Traceroute to {target} - FAILED**\n\n"
                message += f"⚠️ **Error:** {result.error_message or 'Unknown error'}"
            
            await context.bot.edit_message_text(
                chat_id=working_msg.chat_id,
                message_id=working_msg.message_id,
                text=message
            )
            
        except Exception as e:
            await context.bot.edit_message_text(
                chat_id=working_msg.chat_id,
                message_id=working_msg.message_id,
                text=f"❌ Error performing traceroute: {str(e)}"
            )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        message = f"""
🤖 **Network Troubleshooting Bot Status**

✅ **Status:** Online and Ready
🕐 **Current Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👤 **Your User ID:** {user_id}
🔐 **Authorization:** {'Authorized' if self.is_authorized(user_id) else 'Not Authorized'}

📊 **Available Functions:**
• Ping Testing
• Traceroute Analysis
• Natural Language Processing
• Network Troubleshooting

💬 **Usage:** Send me your network questions or use commands like `/ping` and `/traceroute`
        """
        
        await update.message.reply_text(message)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle natural language messages"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        user_message = update.message.text
        
        # Send "thinking" message
        thinking_msg = await update.message.reply_text("🤔 Analyzing your request...")
        
        try:
            # Process with AI intent handler
            intent_result = process_user_query(
                user_message, 
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                user_context={"user_id": user_id, "platform": "telegram"}
            )
            
            # Generate response based on intent
            response_text, keyboard = await self.process_intent_response(intent_result)
            
            if keyboard:
                await context.bot.edit_message_text(
                    chat_id=thinking_msg.chat_id,
                    message_id=thinking_msg.message_id,
                    text=response_text,
                    reply_markup=keyboard
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=thinking_msg.chat_id,
                    message_id=thinking_msg.message_id,
                    text=response_text
                )
            
        except Exception as e:
            await context.bot.edit_message_text(
                chat_id=thinking_msg.chat_id,
                message_id=thinking_msg.message_id,
                text=f"❌ Sorry, I encountered an error: {str(e)}\n\nPlease try rephrasing your question or use specific commands like `/ping` or `/traceroute`."
            )
    
    async def process_intent_response(self, intent_result) -> tuple:
        """Process intent result and generate appropriate response"""
        keyboard = None
        
        if intent_result.intent.value == "ping_test":
            target = (intent_result.entities.get('ip_address') or 
                     intent_result.entities.get('hostname') or 
                     intent_result.entities.get('device_name'))
            
            if target:
                result = await ping_host(target)
                if result.success:
                    response_text = f"""
✅ **Ping Test Result - SUCCESS**

🎯 **Target:** {target}
📊 **Statistics:**
• Packet Loss: {result.packet_loss_percent:.1f}%
• Average Latency: {result.avg_latency_ms:.2f}ms
• Packets: {result.packets_received}/{result.packets_sent}

The target is reachable and responding normally.
                    """
                else:
                    response_text = f"""
❌ **Ping Test Result - FAILED**

🎯 **Target:** {target}
⚠️ **Issue:** {result.error_message or 'Host unreachable'}
📊 **Packet Loss:** {result.packet_loss_percent:.1f}%

🔧 **Suggested Actions:**
• Check if the target IP/hostname is correct
• Verify network connectivity
• Check firewall settings
                    """
                    
                    # Add troubleshooting options
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔍 Traceroute", callback_data=f"traceroute_{target}")],
                        [InlineKeyboardButton("🔄 Retry Ping", callback_data=f"ping_{target}")],
                        [InlineKeyboardButton("ℹ️ More Help", callback_data="help_connectivity")]
                    ])
            else:
                response_text = """
🎯 **Ping Test Request**

I understand you want to test connectivity, but I need to know the target.

**Please specify:**
• IP address (e.g., 8.8.8.8)
• Hostname (e.g., google.com)
• Device name

**Example:** "ping 8.8.8.8" or "test connectivity to google.com"
                """
        
        elif intent_result.intent.value == "traceroute":
            target = (intent_result.entities.get('ip_address') or 
                     intent_result.entities.get('hostname') or 
                     intent_result.entities.get('device_name'))
            
            if target:
                result = await traceroute_host(target)
                if result.success:
                    response_text = f"✅ **Traceroute completed to {target}**\n\n"
                    response_text += f"🎯 Target reached: {'Yes' if result.target_reached else 'No'}\n"
                    response_text += f"📊 Total hops: {result.total_hops}\n\n"
                    response_text += "Use `/traceroute {target}` for detailed hop information."
                else:
                    response_text = f"❌ **Traceroute failed to {target}**\n\n"
                    response_text += f"⚠️ Error: {result.error_message or 'Unknown error'}"
            else:
                response_text = """
🛤️ **Traceroute Request**

I can trace the network path, but I need a target.

**Please specify:**
• IP address (e.g., 1.1.1.1)
• Hostname (e.g., cloudflare.com)

**Example:** "traceroute google.com" or "show path to 8.8.8.8"
                """
        
        elif intent_result.intent.value == "general_help":
            response_text = """
🤖 **How can I help you?**

I'm your network troubleshooting assistant! Here are some things you can ask:

🔍 **Connectivity Testing:**
• "ping 8.8.8.8"
• "test connectivity to server1"
• "is google.com reachable?"

🛤️ **Network Path Analysis:**
• "traceroute cloudflare.com"
• "show path to 1.1.1.1"

🔧 **Troubleshooting:**
• "interface eth0 is down"
• "high latency issues"
• "packet loss problems"

Just describe your network issue and I'll help diagnose it!
            """
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📚 More Help", callback_data="detailed_help")],
                [InlineKeyboardButton("🧪 Test Ping", callback_data="quick_ping")],
                [InlineKeyboardButton("📊 Bot Status", callback_data="bot_status")]
            ])
        
        else:
            response_text = f"""
🤔 **I understand you want to: {intent_result.suggested_action}**

Confidence: {intent_result.confidence:.0%}

However, I need more specific information to help you effectively.

**What I detected:**
            """
            
            if intent_result.entities:
                response_text += "\n**Entities found:**\n"
                for key, value in intent_result.entities.items():
                    response_text += f"• {key}: {value}\n"
            
            response_text += "\n**Please provide more details or try using specific commands like:**\n"
            response_text += "• `/ping <target>`\n"
            response_text += "• `/traceroute <target>`\n"
            response_text += "• `/help` for more options"
        
        return response_text, keyboard
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        if not self.is_authorized(user_id):
            await query.edit_message_text("❌ You are not authorized to use this bot.")
            return
        
        callback_data = query.data
        
        if callback_data.startswith("ping_"):
            target = callback_data.replace("ping_", "")
            await query.edit_message_text(f"🔄 Pinging {target}...")
            
            result = await ping_host(target)
            
            if result.success:
                message = f"✅ Ping to {target} successful!\nLatency: {result.avg_latency_ms:.2f}ms"
            else:
                message = f"❌ Ping to {target} failed!\nError: {result.error_message or 'Unknown'}"
            
            await query.edit_message_text(message)
        
        elif callback_data.startswith("traceroute_"):
            target = callback_data.replace("traceroute_", "")
            await query.edit_message_text(f"🔄 Running traceroute to {target}...")
            
            result = await traceroute_host(target)
            
            if result.success:
                message = f"✅ Traceroute to {target} completed!\nHops: {result.total_hops}"
            else:
                message = f"❌ Traceroute to {target} failed!\nError: {result.error_message or 'Unknown'}"
            
            await query.edit_message_text(message)
        
        elif callback_data == "detailed_help":
            help_text = """
🤖 **Detailed Help - Network Troubleshooting Bot**

**Natural Language Examples:**

🔍 **Connectivity:**
• "Check if 8.8.8.8 is reachable"
• "Ping test to google.com"
• "Is server1 responding?"

🛤️ **Path Analysis:**
• "Trace route to cloudflare.com"
• "Show network path to 1.1.1.1"
• "Route analysis to server"

🔧 **Problem Description:**
• "High latency to server"
• "Packet loss issues"
• "Interface eth0 is down"
• "Cannot reach 192.168.1.1"

**Commands:**
• `/ping <target>` - Test connectivity
• `/traceroute <target>` - Trace network path
• `/status` - Bot status
• `/help` - Show help

Just describe your issue in plain English!
            """
            await query.edit_message_text(help_text)
        
        elif callback_data == "quick_ping":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Google DNS", callback_data="ping_8.8.8.8")],
                [InlineKeyboardButton("Cloudflare DNS", callback_data="ping_1.1.1.1")],
                [InlineKeyboardButton("Google.com", callback_data="ping_google.com")]
            ])
            await query.edit_message_text("🔍 **Quick Ping Test**\n\nChoose a target:", reply_markup=keyboard)
        
        elif callback_data == "bot_status":
            status_text = f"""
🤖 **Bot Status**

✅ Status: Online
🕐 Time: {datetime.now().strftime('%H:%M:%S')}
👤 Your ID: {user_id}
🔐 Authorized: Yes

Ready to help with network troubleshooting!
            """
            await query.edit_message_text(status_text)
    
    async def send_notification(self, chat_id: int, message: str, 
                              alert_type: str = "info") -> bool:
        """Send notification to specific chat"""
        if not self.application:
            return False
        
        emoji_map = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        
        emoji = emoji_map.get(alert_type, "ℹ️")
        formatted_message = f"{emoji} **Network Alert**\n\n{message}"
        
        try:
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=formatted_message,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {str(e)}")
            return False
    
    async def run_bot(self):
        """Run the bot"""
        if not self.application:
            self.setup_bot()
        
        logger.info("Starting Telegram bot...")
        await self.application.run_polling()
    
    def stop_bot(self):
        """Stop the bot"""
        if self.application:
            self.application.stop()

# Convenience function
def create_telegram_notifier_from_config(config_dict: Dict[str, Any]) -> TelegramNotifier:
    """Create TelegramNotifier from configuration"""
    bot_token = config_dict.get('bot_token', '')
    chat_id = config_dict.get('chat_id')
    
    authorized_users = []
    if chat_id:
        try:
            authorized_users = [int(chat_id)]
        except ValueError:
            pass
    
    return TelegramNotifier(bot_token, authorized_users)