"""
AI Module initialization file
"""

from .intent_handler import NetworkIntentHandler, Intent, IntentResult, process_user_query, get_intent_suggestions
from .rules_engine import NetworkRulesEngine, Rule, Action, Condition, TroubleshootingResult, troubleshoot_issue, create_default_rules_file

__all__ = [
    # Intent handling
    'NetworkIntentHandler', 'Intent', 'IntentResult', 'process_user_query', 'get_intent_suggestions',
    
    # Rules engine
    'NetworkRulesEngine', 'Rule', 'Action', 'Condition', 'TroubleshootingResult', 
    'troubleshoot_issue', 'create_default_rules_file'
]