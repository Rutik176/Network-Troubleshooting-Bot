"""
Rules Engine for Network Troubleshooting Bot
Implements decision logic for automated troubleshooting and self-healing
"""
import yaml
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ActionType(Enum):
    DIAGNOSTIC = "diagnostic"
    REMEDIATION = "remediation"
    NOTIFICATION = "notification"
    ESCALATION = "escalation"

class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Condition:
    parameter: str
    operator: str  # >, <, >=, <=, ==, !=, contains, not_contains
    value: Any
    description: str

@dataclass
class Action:
    action_type: ActionType
    command: str
    parameters: Dict[str, Any]
    confirmation_required: bool
    timeout_seconds: int
    description: str

@dataclass
class Rule:
    rule_id: str
    name: str
    description: str
    conditions: List[Condition]
    actions: List[Action]
    severity: Severity
    enabled: bool
    cooldown_seconds: int
    max_executions: int
    tags: List[str]

@dataclass
class RuleExecution:
    rule_id: str
    timestamp: datetime
    conditions_met: List[str]
    actions_executed: List[Dict[str, Any]]
    success: bool
    execution_time_ms: float
    error_message: Optional[str]

@dataclass
class TroubleshootingResult:
    issue_identified: bool
    root_cause: Optional[str]
    severity: Severity
    recommended_actions: List[Action]
    automated_actions_taken: List[Dict[str, Any]]
    manual_intervention_required: bool
    escalation_needed: bool
    summary: str

class NetworkRulesEngine:
    def __init__(self, rules_file: str = None):
        self.rules: List[Rule] = []
        self.execution_history: List[RuleExecution] = []
        self.rule_execution_count: Dict[str, int] = {}
        self.last_execution_time: Dict[str, datetime] = {}
        
        if rules_file:
            self.load_rules_from_file(rules_file)
        else:
            self._load_default_rules()
    
    def load_rules_from_file(self, file_path: str):
        """Load rules from YAML file"""
        try:
            with open(file_path, 'r') as f:
                rules_data = yaml.safe_load(f)
            
            self.rules = []
            for rule_data in rules_data.get('rules', []):
                rule = self._parse_rule_data(rule_data)
                if rule:
                    self.rules.append(rule)
            
            logger.info(f"Loaded {len(self.rules)} rules from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load rules from {file_path}: {str(e)}")
            self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default troubleshooting rules"""
        default_rules_data = {
            'rules': [
                {
                    'rule_id': 'ping_failure_basic',
                    'name': 'Basic Ping Failure',
                    'description': 'Handle basic ping failures with standard diagnostics',
                    'severity': 'medium',
                    'enabled': True,
                    'cooldown_seconds': 300,
                    'max_executions': 5,
                    'tags': ['connectivity', 'ping'],
                    'conditions': [
                        {
                            'parameter': 'ping_success',
                            'operator': '==',
                            'value': False,
                            'description': 'Ping test failed'
                        }
                    ],
                    'actions': [
                        {
                            'action_type': 'diagnostic',
                            'command': 'traceroute',
                            'parameters': {'target': '${target}'},
                            'confirmation_required': False,
                            'timeout_seconds': 60,
                            'description': 'Run traceroute to identify path issues'
                        },
                        {
                            'action_type': 'diagnostic',
                            'command': 'dns_lookup',
                            'parameters': {'target': '${target}'},
                            'confirmation_required': False,
                            'timeout_seconds': 30,
                            'description': 'Check DNS resolution'
                        }
                    ]
                },
                {
                    'rule_id': 'interface_down',
                    'name': 'Interface Down',
                    'description': 'Handle interface down events',
                    'severity': 'high',
                    'enabled': True,
                    'cooldown_seconds': 600,
                    'max_executions': 3,
                    'tags': ['interface', 'connectivity'],
                    'conditions': [
                        {
                            'parameter': 'interface_status',
                            'operator': '==',
                            'value': 'down',
                            'description': 'Interface is down'
                        }
                    ],
                    'actions': [
                        {
                            'action_type': 'diagnostic',
                            'command': 'check_interface_logs',
                            'parameters': {'interface': '${interface}'},
                            'confirmation_required': False,
                            'timeout_seconds': 30,
                            'description': 'Check interface logs for errors'
                        },
                        {
                            'action_type': 'remediation',
                            'command': 'restart_interface',
                            'parameters': {'interface': '${interface}'},
                            'confirmation_required': True,
                            'timeout_seconds': 60,
                            'description': 'Restart the interface'
                        }
                    ]
                },
                {
                    'rule_id': 'high_latency',
                    'name': 'High Latency',
                    'description': 'Handle high latency issues',
                    'severity': 'medium',
                    'enabled': True,
                    'cooldown_seconds': 300,
                    'max_executions': 10,
                    'tags': ['performance', 'latency'],
                    'conditions': [
                        {
                            'parameter': 'avg_latency_ms',
                            'operator': '>',
                            'value': 100,
                            'description': 'Average latency is high'
                        }
                    ],
                    'actions': [
                        {
                            'action_type': 'diagnostic',
                            'command': 'traceroute',
                            'parameters': {'target': '${target}'},
                            'confirmation_required': False,
                            'timeout_seconds': 60,
                            'description': 'Trace route to identify latency sources'
                        },
                        {
                            'action_type': 'diagnostic',
                            'command': 'check_interface_utilization',
                            'parameters': {'device': '${device}'},
                            'confirmation_required': False,
                            'timeout_seconds': 30,
                            'description': 'Check interface utilization'
                        }
                    ]
                },
                {
                    'rule_id': 'packet_loss',
                    'name': 'Packet Loss',
                    'description': 'Handle packet loss issues',
                    'severity': 'high',
                    'enabled': True,
                    'cooldown_seconds': 300,
                    'max_executions': 5,
                    'tags': ['performance', 'packet_loss'],
                    'conditions': [
                        {
                            'parameter': 'packet_loss_percent',
                            'operator': '>',
                            'value': 5,
                            'description': 'Packet loss is above threshold'
                        }
                    ],
                    'actions': [
                        {
                            'action_type': 'diagnostic',
                            'command': 'check_interface_errors',
                            'parameters': {'device': '${device}'},
                            'confirmation_required': False,
                            'timeout_seconds': 30,
                            'description': 'Check for interface errors'
                        },
                        {
                            'action_type': 'diagnostic',
                            'command': 'check_device_cpu',
                            'parameters': {'device': '${device}'},
                            'confirmation_required': False,
                            'timeout_seconds': 30,
                            'description': 'Check device CPU utilization'
                        }
                    ]
                },
                {
                    'rule_id': 'device_unreachable',
                    'name': 'Device Unreachable',
                    'description': 'Handle device unreachable scenarios',
                    'severity': 'critical',
                    'enabled': True,
                    'cooldown_seconds': 600,
                    'max_executions': 3,
                    'tags': ['connectivity', 'device'],
                    'conditions': [
                        {
                            'parameter': 'device_reachable',
                            'operator': '==',
                            'value': False,
                            'description': 'Device is not reachable'
                        }
                    ],
                    'actions': [
                        {
                            'action_type': 'diagnostic',
                            'command': 'ping_gateway',
                            'parameters': {'device': '${device}'},
                            'confirmation_required': False,
                            'timeout_seconds': 30,
                            'description': 'Check gateway connectivity'
                        },
                        {
                            'action_type': 'notification',
                            'command': 'send_alert',
                            'parameters': {
                                'message': 'Critical: Device ${device} is unreachable',
                                'severity': 'critical'
                            },
                            'confirmation_required': False,
                            'timeout_seconds': 10,
                            'description': 'Send critical alert'
                        },
                        {
                            'action_type': 'escalation',
                            'command': 'create_ticket',
                            'parameters': {
                                'title': 'Device ${device} unreachable',
                                'priority': 'high'
                            },
                            'confirmation_required': False,
                            'timeout_seconds': 30,
                            'description': 'Create incident ticket'
                        }
                    ]
                }
            ]
        }
        
        self.rules = []
        for rule_data in default_rules_data['rules']:
            rule = self._parse_rule_data(rule_data)
            if rule:
                self.rules.append(rule)
    
    def _parse_rule_data(self, rule_data: Dict[str, Any]) -> Optional[Rule]:
        """Parse rule data from dictionary"""
        try:
            # Parse conditions
            conditions = []
            for cond_data in rule_data.get('conditions', []):
                conditions.append(Condition(
                    parameter=cond_data['parameter'],
                    operator=cond_data['operator'],
                    value=cond_data['value'],
                    description=cond_data.get('description', '')
                ))
            
            # Parse actions
            actions = []
            for action_data in rule_data.get('actions', []):
                actions.append(Action(
                    action_type=ActionType(action_data['action_type']),
                    command=action_data['command'],
                    parameters=action_data.get('parameters', {}),
                    confirmation_required=action_data.get('confirmation_required', False),
                    timeout_seconds=action_data.get('timeout_seconds', 60),
                    description=action_data.get('description', '')
                ))
            
            return Rule(
                rule_id=rule_data['rule_id'],
                name=rule_data['name'],
                description=rule_data['description'],
                conditions=conditions,
                actions=actions,
                severity=Severity(rule_data.get('severity', 'medium')),
                enabled=rule_data.get('enabled', True),
                cooldown_seconds=rule_data.get('cooldown_seconds', 300),
                max_executions=rule_data.get('max_executions', 5),
                tags=rule_data.get('tags', [])
            )
            
        except Exception as e:
            logger.error(f"Failed to parse rule {rule_data.get('rule_id', 'unknown')}: {str(e)}")
            return None
    
    def evaluate_conditions(self, data: Dict[str, Any]) -> List[Rule]:
        """Evaluate all rules against provided data and return matching rules"""
        matching_rules = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # Check cooldown
            if not self._check_cooldown(rule):
                continue
            
            # Check max executions
            if not self._check_max_executions(rule):
                continue
            
            # Evaluate conditions
            if self._evaluate_rule_conditions(rule, data):
                matching_rules.append(rule)
        
        # Sort by severity (critical first)
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3
        }
        
        matching_rules.sort(key=lambda r: severity_order.get(r.severity, 3))
        
        return matching_rules
    
    def _evaluate_rule_conditions(self, rule: Rule, data: Dict[str, Any]) -> bool:
        """Evaluate if all conditions of a rule are met"""
        for condition in rule.conditions:
            if not self._evaluate_condition(condition, data):
                return False
        return True
    
    def _evaluate_condition(self, condition: Condition, data: Dict[str, Any]) -> bool:
        """Evaluate a single condition"""
        parameter_value = data.get(condition.parameter)
        
        if parameter_value is None:
            return False
        
        try:
            if condition.operator == '==':
                return parameter_value == condition.value
            elif condition.operator == '!=':
                return parameter_value != condition.value
            elif condition.operator == '>':
                return float(parameter_value) > float(condition.value)
            elif condition.operator == '<':
                return float(parameter_value) < float(condition.value)
            elif condition.operator == '>=':
                return float(parameter_value) >= float(condition.value)
            elif condition.operator == '<=':
                return float(parameter_value) <= float(condition.value)
            elif condition.operator == 'contains':
                return str(condition.value).lower() in str(parameter_value).lower()
            elif condition.operator == 'not_contains':
                return str(condition.value).lower() not in str(parameter_value).lower()
            else:
                logger.warning(f"Unknown operator: {condition.operator}")
                return False
        
        except (ValueError, TypeError) as e:
            logger.error(f"Error evaluating condition: {str(e)}")
            return False
    
    def _check_cooldown(self, rule: Rule) -> bool:
        """Check if rule is not in cooldown period"""
        last_execution = self.last_execution_time.get(rule.rule_id)
        if not last_execution:
            return True
        
        time_since_last = datetime.now() - last_execution
        return time_since_last.total_seconds() >= rule.cooldown_seconds
    
    def _check_max_executions(self, rule: Rule) -> bool:
        """Check if rule hasn't exceeded max executions"""
        execution_count = self.rule_execution_count.get(rule.rule_id, 0)
        return execution_count < rule.max_executions
    
    def execute_rule(self, rule: Rule, data: Dict[str, Any], 
                    confirmation_callback=None) -> RuleExecution:
        """Execute a rule's actions"""
        start_time = time.time()
        timestamp = datetime.now()
        
        conditions_met = [cond.description for cond in rule.conditions 
                         if self._evaluate_condition(cond, data)]
        
        actions_executed = []
        success = True
        error_message = None
        
        try:
            for action in rule.actions:
                # Check if confirmation is required
                if action.confirmation_required and confirmation_callback:
                    confirmed = confirmation_callback(rule, action, data)
                    if not confirmed:
                        actions_executed.append({
                            'action': action.command,
                            'status': 'skipped',
                            'reason': 'User did not confirm'
                        })
                        continue
                
                # Execute action
                action_result = self._execute_action(action, data)
                actions_executed.append(action_result)
                
                if not action_result.get('success', False):
                    success = False
        
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Error executing rule {rule.rule_id}: {str(e)}")
        
        execution_time = (time.time() - start_time) * 1000
        
        # Update execution tracking
        self.rule_execution_count[rule.rule_id] = self.rule_execution_count.get(rule.rule_id, 0) + 1
        self.last_execution_time[rule.rule_id] = timestamp
        
        # Create execution record
        execution = RuleExecution(
            rule_id=rule.rule_id,
            timestamp=timestamp,
            conditions_met=conditions_met,
            actions_executed=actions_executed,
            success=success,
            execution_time_ms=execution_time,
            error_message=error_message
        )
        
        self.execution_history.append(execution)
        
        return execution
    
    def _execute_action(self, action: Action, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action"""
        # Substitute variables in parameters
        substituted_params = self._substitute_variables(action.parameters, data)
        
        result = {
            'action': action.command,
            'action_type': action.action_type.value,
            'parameters': substituted_params,
            'description': action.description,
            'success': False,
            'output': None,
            'error': None
        }
        
        try:
            # Simulate action execution (in real implementation, this would call actual functions)
            if action.command == 'traceroute':
                result['success'] = True
                result['output'] = f"Traceroute to {substituted_params.get('target', 'unknown')} completed"
            
            elif action.command == 'restart_interface':
                result['success'] = True
                result['output'] = f"Interface {substituted_params.get('interface', 'unknown')} restarted"
            
            elif action.command == 'send_alert':
                result['success'] = True
                result['output'] = f"Alert sent: {substituted_params.get('message', 'Alert')}"
            
            elif action.command == 'create_ticket':
                result['success'] = True
                result['output'] = f"Ticket created: {substituted_params.get('title', 'Network Issue')}"
            
            else:
                # Default action execution
                result['success'] = True
                result['output'] = f"Executed {action.command} with parameters {substituted_params}"
        
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Action execution failed: {str(e)}")
        
        return result
    
    def _substitute_variables(self, parameters: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute variables in parameters using data values"""
        substituted = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                # Extract variable name
                var_name = value[2:-1]
                substituted[key] = data.get(var_name, value)
            else:
                substituted[key] = value
        
        return substituted
    
    def troubleshoot(self, issue_data: Dict[str, Any], 
                    auto_execute: bool = False, 
                    confirmation_callback=None) -> TroubleshootingResult:
        """
        Main troubleshooting function that analyzes issue and suggests/executes actions
        """
        # Find matching rules
        matching_rules = self.evaluate_conditions(issue_data)
        
        if not matching_rules:
            return TroubleshootingResult(
                issue_identified=False,
                root_cause=None,
                severity=Severity.LOW,
                recommended_actions=[],
                automated_actions_taken=[],
                manual_intervention_required=True,
                escalation_needed=False,
                summary="No matching rules found for the reported issue."
            )
        
        # Determine severity
        highest_severity = max(rule.severity for rule in matching_rules)
        
        # Collect all recommended actions
        recommended_actions = []
        for rule in matching_rules:
            recommended_actions.extend(rule.actions)
        
        # Execute rules if auto_execute is enabled
        automated_actions_taken = []
        if auto_execute:
            for rule in matching_rules:
                if rule.severity in [Severity.CRITICAL, Severity.HIGH]:
                    # Execute high-priority rules automatically
                    execution = self.execute_rule(rule, issue_data, confirmation_callback)
                    automated_actions_taken.extend(execution.actions_executed)
        
        # Determine if manual intervention or escalation is needed
        manual_intervention_required = any(
            action.confirmation_required for rule in matching_rules 
            for action in rule.actions
        )
        
        escalation_needed = (
            highest_severity == Severity.CRITICAL or
            len([rule for rule in matching_rules if rule.severity == Severity.HIGH]) > 2
        )
        
        # Generate summary
        rule_names = [rule.name for rule in matching_rules]
        summary = f"Identified {len(matching_rules)} potential issues: {', '.join(rule_names)}. "
        
        if automated_actions_taken:
            summary += f"Executed {len(automated_actions_taken)} automated actions. "
        
        if manual_intervention_required:
            summary += "Manual intervention may be required for some actions. "
        
        if escalation_needed:
            summary += "Escalation to senior staff recommended due to severity."
        
        return TroubleshootingResult(
            issue_identified=True,
            root_cause=matching_rules[0].description if matching_rules else None,
            severity=highest_severity,
            recommended_actions=recommended_actions,
            automated_actions_taken=automated_actions_taken,
            manual_intervention_required=manual_intervention_required,
            escalation_needed=escalation_needed,
            summary=summary.strip()
        )
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about rule executions"""
        return {
            'total_rules': len(self.rules),
            'enabled_rules': len([r for r in self.rules if r.enabled]),
            'total_executions': len(self.execution_history),
            'successful_executions': len([e for e in self.execution_history if e.success]),
            'execution_count_by_rule': dict(self.rule_execution_count),
            'recent_executions': self.execution_history[-10:] if self.execution_history else []
        }
    
    def reset_execution_counters(self):
        """Reset execution counters (useful for testing or periodic reset)"""
        self.rule_execution_count.clear()
        self.last_execution_time.clear()

# Convenience functions
def create_default_rules_file(file_path: str):
    """Create a default rules file for customization"""
    engine = NetworkRulesEngine()
    
    rules_data = {
        'rules': []
    }
    
    for rule in engine.rules:
        rule_dict = {
            'rule_id': rule.rule_id,
            'name': rule.name,
            'description': rule.description,
            'severity': rule.severity.value,
            'enabled': rule.enabled,
            'cooldown_seconds': rule.cooldown_seconds,
            'max_executions': rule.max_executions,
            'tags': rule.tags,
            'conditions': [
                {
                    'parameter': cond.parameter,
                    'operator': cond.operator,
                    'value': cond.value,
                    'description': cond.description
                }
                for cond in rule.conditions
            ],
            'actions': [
                {
                    'action_type': action.action_type.value,
                    'command': action.command,
                    'parameters': action.parameters,
                    'confirmation_required': action.confirmation_required,
                    'timeout_seconds': action.timeout_seconds,
                    'description': action.description
                }
                for action in rule.actions
            ]
        }
        rules_data['rules'].append(rule_dict)
    
    with open(file_path, 'w') as f:
        yaml.dump(rules_data, f, default_flow_style=False, indent=2)

def troubleshoot_issue(issue_data: Dict[str, Any], rules_file: str = None, 
                      auto_execute: bool = False) -> TroubleshootingResult:
    """Simple troubleshooting function"""
    engine = NetworkRulesEngine(rules_file)
    return engine.troubleshoot(issue_data, auto_execute)