"""
Database models for Network Troubleshooting Bot
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class Device(Base):
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    ip_address = Column(String(45), unique=True, index=True)
    device_type = Column(String(50))  # router, switch, firewall, server
    vendor = Column(String(50))
    model = Column(String(100))
    location = Column(String(100))
    status = Column(String(20), default='active')  # active, inactive, maintenance
    credentials = Column(Text)  # encrypted credentials
    protocols = Column(JSON)  # supported protocols and settings
    interfaces = Column(JSON)  # list of interfaces
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    test_results = relationship("TestResult", back_populates="device")
    alerts = relationship("Alert", back_populates="device")

class TestResult(Base):
    __tablename__ = 'test_results'
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey('devices.id'))
    test_type = Column(String(50))  # ping, traceroute, snmp, ssh, port_scan
    target = Column(String(255))  # target IP or hostname
    status = Column(String(20))  # success, failed, timeout, error
    latency_ms = Column(Float)
    packet_loss = Column(Float)
    details = Column(JSON)  # detailed test results
    error_message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    device = relationship("Device", back_populates="test_results")

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=True)
    alert_type = Column(String(50))  # latency, packet_loss, device_down, interface_down
    severity = Column(String(20))  # low, medium, high, critical
    title = Column(String(255))
    description = Column(Text)
    status = Column(String(20), default='open')  # open, acknowledged, resolved
    threshold_value = Column(Float)
    current_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    device = relationship("Device", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert")

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey('alerts.id'))
    channel = Column(String(50))  # email, telegram, slack
    recipient = Column(String(255))
    status = Column(String(20))  # sent, failed, pending
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    alert = relationship("Alert", back_populates="notifications")

class FixLog(Base):
    __tablename__ = 'fix_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey('devices.id'))
    issue_description = Column(Text)
    fix_action = Column(Text)
    status = Column(String(20))  # pending, executed, failed, cancelled
    confirmation_required = Column(Boolean, default=True)
    confirmed_by = Column(String(100), nullable=True)
    executed_at = Column(DateTime, nullable=True)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    device = relationship("Device")

class UserQuery(Base):
    __tablename__ = 'user_queries'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100))  # telegram user id, slack user id, etc.
    channel = Column(String(50))  # telegram, slack, web, cli
    query_text = Column(Text)
    intent = Column(String(100))  # detected intent
    response = Column(Text)
    status = Column(String(20))  # processed, failed, pending
    processing_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class NetworkMetric(Base):
    __tablename__ = 'network_metrics'
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey('devices.id'))
    metric_type = Column(String(50))  # cpu_usage, memory_usage, interface_utilization, bandwidth
    interface_name = Column(String(100), nullable=True)
    value = Column(Float)
    unit = Column(String(20))  # percent, mbps, packets, bytes
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    device = relationship("Device")

class TroubleshootingSession(Base):
    __tablename__ = 'troubleshooting_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100))
    session_id = Column(String(100), unique=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=True)
    issue_type = Column(String(100))
    status = Column(String(20))  # active, completed, cancelled
    steps = Column(JSON)  # list of troubleshooting steps
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    device = relationship("Device")

# Database connection and session management
class DatabaseManager:
    def __init__(self, database_url: str = None):
        if database_url is None:
            database_url = os.getenv("DATABASE_URL", "sqlite:///db/network_logs.db")
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all database tables"""
        os.makedirs("db", exist_ok=True)
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
        
    def close_session(self, session):
        """Close database session"""
        session.close()

# Global database manager instance
db_manager = DatabaseManager()