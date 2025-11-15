"""
Integrations module initialization
"""

from .email_notify import EmailNotifier, EmailAlert, EmailConfig, create_email_notifier_from_config, send_quick_alert
from .slack_alerts import SlackNotifier, SlackMessage, SlackConfig, create_slack_notifier_from_config, send_quick_slack_alert
from .telegram_bot import TelegramNotifier, create_telegram_notifier_from_config

__all__ = [
    # Email notifications
    'EmailNotifier', 'EmailAlert', 'EmailConfig', 'create_email_notifier_from_config', 'send_quick_alert',
    
    # Slack notifications
    'SlackNotifier', 'SlackMessage', 'SlackConfig', 'create_slack_notifier_from_config', 'send_quick_slack_alert',
    
    # Telegram bot
    'TelegramNotifier', 'create_telegram_notifier_from_config'
]