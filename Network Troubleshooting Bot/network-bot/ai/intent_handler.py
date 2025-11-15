"""
Intent Handler for Network Troubleshooting Bot
Uses AI/NLP to understand user queries and route them to appropriate troubleshooting actions
"""
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

try:
    import openai
    from langchain.llms import OpenAI
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available. Using rule-based intent detection.")

logger = logging.getLogger(__name__)

class Intent(Enum):
    PING_TEST = "ping_test"
    TRACEROUTE = "traceroute"
    CHECK_INTERFACE = "check_interface"
    CHECK_DEVICE_STATUS = "check_device_status"
    RESTART_INTERFACE = "restart_interface"
    CHECK_ROUTING = "check_routing"
    ANALYZE_LOGS = "analyze_logs"
    MONITOR_PERFORMANCE = "monitor_performance"
    TROUBLESHOOT_CONNECTIVITY = "troubleshoot_connectivity"
    GET_DEVICE_INFO = "get_device_info"
    CHECK_BANDWIDTH = "check_bandwidth"
    SECURITY_CHECK = "security_check"
    GENERAL_HELP = "general_help"
    UNKNOWN = "unknown"

@dataclass
class IntentResult:
    intent: Intent
    confidence: float
    entities: Dict[str, Any]
    query: str
    suggested_action: str
    parameters: Dict[str, Any]

@dataclass
class Entity:
    name: str
    value: str
    entity_type: str
    confidence: float

class NetworkIntentHandler:
    def __init__(self, openai_api_key: str = None, use_llm: bool = True):
        self.openai_api_key = openai_api_key
        self.use_llm = use_llm and LANGCHAIN_AVAILABLE and openai_api_key
        
        if self.use_llm:
            self._setup_llm()
        
        # Intent patterns for rule-based fallback
        self.intent_patterns = {
            Intent.PING_TEST: [
                r'\b(ping|reachability|connectivity test)\b.*\b([\w.-]+)\b',
                r'can you ping\s+([\w.-]+)',
                r'test connectivity to\s+([\w.-]+)',
                r'is\s+([\w.-]+)\s+reachable'
            ],
            Intent.TRACEROUTE: [
                r'\b(traceroute|trace|path)\b.*\b([\w.-]+)\b',
                r'trace route to\s+([\w.-]+)',
                r'show path to\s+([\w.-]+)',
                r'route to\s+([\w.-]+)'
            ],
            Intent.CHECK_INTERFACE: [
                r'check interface\s+([\w/-]+)',
                r'interface\s+([\w/-]+)\s+(status|state)',
                r'show interface\s+([\w/-]+)',
                r'([\w/-]+)\s+interface.*status'
            ],
            Intent.CHECK_DEVICE_STATUS: [
                r'check\s+([\w.-]+)\s+(status|health)',
                r'device\s+([\w.-]+)\s+(status|state)',
                r'is\s+([\w.-]+)\s+(up|down|online|offline)',
                r'status of\s+([\w.-]+)'
            ],
            Intent.RESTART_INTERFACE: [
                r'restart interface\s+([\w/-]+)',
                r'bounce interface\s+([\w/-]+)',
                r'reset interface\s+([\w/-]+)',
                r'reload interface\s+([\w/-]+)'
            ],
            Intent.CHECK_ROUTING: [
                r'check routing.*\b([\w.-]+)\b',
                r'routing table.*\b([\w.-]+)\b',
                r'show route.*\b([\w.-]+)\b',
                r'route to\s+([\w.-]+)'
            ],
            Intent.ANALYZE_LOGS: [
                r'analyze logs?',
                r'check logs?',
                r'log analysis',
                r'what.*logs.*say',
                r'review.*logs'
            ],
            Intent.MONITOR_PERFORMANCE: [
                r'performance.*\b([\w.-]+)\b',
                r'monitor.*\b([\w.-]+)\b',
                r'utilization.*\b([\w.-]+)\b',
                r'bandwidth.*\b([\w.-]+)\b'
            ],
            Intent.TROUBLESHOOT_CONNECTIVITY: [
                r'troubleshoot.*connectivity.*\b([\w.-]+)\b',
                r'connectivity.*issue.*\b([\w.-]+)\b',
                r'cannot.*reach.*\b([\w.-]+)\b',
                r'network.*problem.*\b([\w.-]+)\b'
            ],
            Intent.GET_DEVICE_INFO: [
                r'device.*info.*\b([\w.-]+)\b',
                r'information.*\b([\w.-]+)\b',
                r'details.*\b([\w.-]+)\b',
                r'show.*\b([\w.-]+)\b.*info'
            ],
            Intent.GENERAL_HELP: [
                r'\b(help|usage|commands|what can you do)\b',
                r'how to',
                r'instructions',
                r'guide'
            ]
        }
        
        # Entity patterns
        self.entity_patterns = {
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'hostname': r'\b[a-zA-Z][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}\b',
            'interface': r'\b(?:eth|gi|fa|te|ge|lo|vlan)\d+(?:/\d+)*\b|(?:ethernet|gigabit|fastethernet|tengige|loopback|vlan)\s*\d+(?:/\d+)*',
            'device_name': r'\b(?:router|switch|firewall|server|host)\s*[a-zA-Z0-9-]+\b',
            'network': r'\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}\b',
            'port': r'\bport\s+(\d{1,5})\b'
        }
    
    def _setup_llm(self):
        """Setup LangChain LLM for advanced intent detection"""
        try:
            self.llm = OpenAI(
                openai_api_key=self.openai_api_key,
                temperature=0.1,
                max_tokens=150
            )
            
            # Intent classification prompt
            self.intent_prompt = PromptTemplate(
                input_variables=["query", "available_intents"],
                template="""
                You are a network troubleshooting assistant. Analyze the user query and determine the intent.
                
                Available intents:
                {available_intents}
                
                User query: "{query}"
                
                Respond with JSON format:
                {{
                    "intent": "most_likely_intent",
                    "confidence": 0.95,
                    "entities": {{"entity_type": "entity_value"}},
                    "reasoning": "brief explanation"
                }}
                """
            )
            
            self.intent_chain = LLMChain(
                llm=self.llm,
                prompt=self.intent_prompt
            )
            
        except Exception as e:
            logger.error(f"Failed to setup LLM: {str(e)}")
            self.use_llm = False
    
    def process_query(self, query: str, user_context: Dict[str, Any] = None) -> IntentResult:
        """
        Process user query and determine intent with entities
        """
        query = query.strip().lower()
        
        if self.use_llm:
            try:
                return self._process_query_with_llm(query, user_context)
            except Exception as e:
                logger.warning(f"LLM processing failed, falling back to rules: {str(e)}")
        
        return self._process_query_with_rules(query, user_context)
    
    def _process_query_with_llm(self, query: str, user_context: Dict[str, Any] = None) -> IntentResult:
        """Process query using LLM"""
        available_intents = [intent.value for intent in Intent]
        
        response = self.intent_chain.run(
            query=query,
            available_intents=", ".join(available_intents)
        )
        
        try:
            # Parse LLM response
            response_data = json.loads(response)
            intent_str = response_data.get('intent', 'unknown')
            confidence = response_data.get('confidence', 0.5)
            entities = response_data.get('entities', {})
            
            # Map intent string to enum
            try:
                intent = Intent(intent_str)
            except ValueError:
                intent = Intent.UNKNOWN
                confidence = 0.1
            
            # Extract additional entities using patterns
            extracted_entities = self._extract_entities(query)
            entities.update(extracted_entities)
            
            # Generate action suggestion
            suggested_action = self._generate_action_suggestion(intent, entities)
            
            # Generate parameters
            parameters = self._generate_parameters(intent, entities, user_context)
            
            return IntentResult(
                intent=intent,
                confidence=confidence,
                entities=entities,
                query=query,
                suggested_action=suggested_action,
                parameters=parameters
            )
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response: {response}")
            return self._process_query_with_rules(query, user_context)
    
    def _process_query_with_rules(self, query: str, user_context: Dict[str, Any] = None) -> IntentResult:
        """Process query using rule-based pattern matching"""
        best_intent = Intent.UNKNOWN
        best_confidence = 0.0
        entities = {}
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    confidence = 0.8  # Base confidence for rule-based matching
                    
                    # Extract entities from match groups
                    if match.groups():
                        # Determine what the matched group represents
                        matched_value = match.group(1)
                        entity_type = self._classify_entity(matched_value)
                        entities[entity_type] = matched_value
                    
                    # Higher confidence for more specific patterns
                    if len(pattern) > 30:
                        confidence += 0.1
                    
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
        
        # Extract additional entities
        extracted_entities = self._extract_entities(query)
        entities.update(extracted_entities)
        
        # Generate action suggestion
        suggested_action = self._generate_action_suggestion(best_intent, entities)
        
        # Generate parameters
        parameters = self._generate_parameters(best_intent, entities, user_context)
        
        return IntentResult(
            intent=best_intent,
            confidence=best_confidence,
            entities=entities,
            query=query,
            suggested_action=suggested_action,
            parameters=parameters
        )
    
    def _extract_entities(self, query: str) -> Dict[str, str]:
        """Extract entities using regex patterns"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                # Take the first match for simplicity
                entities[entity_type] = matches[0]
        
        return entities
    
    def _classify_entity(self, value: str) -> str:
        """Classify what type of entity a value represents"""
        # IP address pattern
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', value):
            return 'ip_address'
        
        # Interface pattern
        if re.match(r'^(?:eth|gi|fa|te|ge|lo|vlan)\d+(?:/\d+)*$', value.lower()):
            return 'interface'
        
        # Hostname pattern (contains dots)
        if '.' in value and not value.replace('.', '').replace('-', '').isdigit():
            return 'hostname'
        
        # Default to device name
        return 'device_name'
    
    def _generate_action_suggestion(self, intent: Intent, entities: Dict[str, str]) -> str:
        """Generate human-readable action suggestion"""
        action_templates = {
            Intent.PING_TEST: "Perform ping test to {target}",
            Intent.TRACEROUTE: "Run traceroute to {target}",
            Intent.CHECK_INTERFACE: "Check status of interface {interface}",
            Intent.CHECK_DEVICE_STATUS: "Check status of device {device}",
            Intent.RESTART_INTERFACE: "Restart interface {interface}",
            Intent.CHECK_ROUTING: "Check routing table for {target}",
            Intent.ANALYZE_LOGS: "Analyze system logs for issues",
            Intent.MONITOR_PERFORMANCE: "Monitor performance metrics for {target}",
            Intent.TROUBLESHOOT_CONNECTIVITY: "Troubleshoot connectivity to {target}",
            Intent.GET_DEVICE_INFO: "Get device information for {target}",
            Intent.GENERAL_HELP: "Provide help and usage information",
            Intent.UNKNOWN: "Unable to determine specific action"
        }
        
        template = action_templates.get(intent, "Process user request")
        
        # Replace placeholders with actual entity values
        target = (entities.get('ip_address') or 
                 entities.get('hostname') or 
                 entities.get('device_name') or 
                 'target')
        
        interface = entities.get('interface', 'interface')
        device = entities.get('device_name', target)
        
        return template.format(target=target, interface=interface, device=device)
    
    def _generate_parameters(self, intent: Intent, entities: Dict[str, str], 
                           user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate parameters for the intended action"""
        user_context = user_context or {}
        
        parameters = {
            'intent': intent.value,
            'entities': entities
        }
        
        # Add intent-specific parameters
        if intent in [Intent.PING_TEST, Intent.TRACEROUTE, Intent.TROUBLESHOOT_CONNECTIVITY]:
            target = (entities.get('ip_address') or 
                     entities.get('hostname') or 
                     entities.get('device_name'))
            if target:
                parameters['target'] = target
        
        if intent == Intent.CHECK_INTERFACE or intent == Intent.RESTART_INTERFACE:
            interface = entities.get('interface')
            if interface:
                parameters['interface'] = interface
        
        if intent == Intent.CHECK_DEVICE_STATUS or intent == Intent.GET_DEVICE_INFO:
            device = (entities.get('device_name') or 
                     entities.get('hostname') or 
                     entities.get('ip_address'))
            if device:
                parameters['device'] = device
        
        # Add user context
        if user_context:
            parameters['user_context'] = user_context
        
        return parameters
    
    def get_follow_up_questions(self, intent_result: IntentResult) -> List[str]:
        """Generate follow-up questions to gather missing information"""
        questions = []
        
        if intent_result.intent == Intent.UNKNOWN:
            questions.extend([
                "What specific network issue are you experiencing?",
                "Which device or IP address should I check?",
                "Would you like me to run a connectivity test, check device status, or analyze logs?"
            ])
        
        elif intent_result.intent in [Intent.PING_TEST, Intent.TRACEROUTE]:
            if not any(key in intent_result.entities for key in ['ip_address', 'hostname', 'device_name']):
                questions.append("What IP address or hostname should I test?")
        
        elif intent_result.intent in [Intent.CHECK_INTERFACE, Intent.RESTART_INTERFACE]:
            if 'interface' not in intent_result.entities:
                questions.append("Which interface should I check? (e.g., eth0, gi0/1)")
        
        elif intent_result.intent == Intent.CHECK_DEVICE_STATUS:
            if not any(key in intent_result.entities for key in ['device_name', 'hostname', 'ip_address']):
                questions.append("Which device should I check?")
        
        return questions
    
    def get_help_text(self) -> str:
        """Get help text explaining available commands"""
        return """
🤖 Network Troubleshooting Bot - Available Commands:

🔍 **Connectivity Testing:**
• "ping 8.8.8.8" - Test connectivity to a host
• "traceroute google.com" - Trace network path
• "check connectivity to server1" - Troubleshoot connection issues

📊 **Device Monitoring:**
• "check device status router1" - Check device health
• "show interface eth0" - Check interface status
• "monitor performance switch1" - Monitor device performance

🔧 **Automation:**
• "restart interface gi0/1" - Restart network interface
• "check routing to 192.168.1.0" - Check routing table
• "analyze logs" - Analyze system logs for issues

ℹ️ **Information:**
• "device info router1" - Get detailed device information
• "help" - Show this help message

📝 **Examples:**
• "Why is router A not reachable?"
• "Check latency between Mumbai and Pune routers"
• "Interface gi0/1 is down, what should I do?"
• "Analyze recent network errors"

Just describe your network issue in natural language, and I'll help troubleshoot it!
        """

# Convenience functions
def process_user_query(query: str, openai_api_key: str = None, 
                      user_context: Dict[str, Any] = None) -> IntentResult:
    """Simple function to process a user query"""
    handler = NetworkIntentHandler(openai_api_key=openai_api_key)
    return handler.process_query(query, user_context)

def get_intent_suggestions(partial_query: str) -> List[str]:
    """Get intent suggestions for autocomplete"""
    suggestions = [
        "ping 8.8.8.8",
        "traceroute google.com",
        "check interface eth0",
        "device status router1",
        "restart interface gi0/1",
        "check routing to 192.168.1.0",
        "analyze logs",
        "monitor performance switch1",
        "troubleshoot connectivity to server1",
        "device info router1",
        "help"
    ]
    
    # Filter suggestions based on partial query
    if partial_query:
        filtered_suggestions = [
            s for s in suggestions 
            if partial_query.lower() in s.lower()
        ]
        return filtered_suggestions[:5]
    
    return suggestions[:5]