#!/usr/bin/env python3
"""
Security and Audit Logging System

Implements comprehensive audit logging with timestamped, categorized logs,
security features like rate limiting, and anomaly detection for watcher activities.
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib


class AuditCategory(Enum):
    SYSTEM = "system"
    SECURITY = "security"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    CONFIGURATION = "configuration"
    PERFORMANCE = "performance"
    ERROR = "error"


class SecurityLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    ALERT = "alert"


@dataclass
class AuditLog:
    timestamp: str
    category: AuditCategory
    security_level: SecurityLevel
    event_id: str
    source: str
    user: Optional[str]
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: Optional[str]
    session_id: Optional[str]


@dataclass
class RateLimitRule:
    name: str
    window_seconds: int
    max_requests: int
    current_count: int = 0
    reset_time: float = 0.0


class AnomalyDetector:
    def __init__(self):
        self.patterns = {
            "brute_force": {
                "pattern": "authentication.*failed",
                "threshold": 5,
                "window": 300  # 5 minutes
            },
            "data_exfiltration": {
                "pattern": "data_access.*large.*file",
                "threshold": 10,
                "window": 600  # 10 minutes
            },
            "config_changes": {
                "pattern": "configuration.*modified",
                "threshold": 3,
                "window": 1800  # 30 minutes
            }
        }

    def detect_anomalies(self, logs: List[AuditLog]) -> List[Dict]:
        """Detect anomalies in audit logs"""
        anomalies = []

        for name, config in self.patterns.items():
            # Filter logs by pattern and time window
            pattern = re.compile(config["pattern"], re.IGNORECASE)
            window_start = time.time() - config["window"]

            matching_logs = [
                log for log in logs
                if pattern.search(log.action) and
                   datetime.fromisoformat(log.timestamp).timestamp() >= window_start
            ]

            if len(matching_logs) >= config["threshold"]:
                anomalies.append({
                    "type": name,
                    "count": len(matching_logs),
                    "threshold": config["threshold"],
                    "window": config["window"],
                    "logs": [asdict(log) for log in matching_logs]
                })

        return anomalies


class AuditLogger:
    def __init__(self, log_file: str = "audit.log", max_file_size: int = 10 * 1024 * 1024):
        self.log_file = log_file
        self.max_file_size = max_file_size
        self.rate_limits: Dict[str, RateLimitRule] = {}
        self.anomaly_detector = AnomalyDetector()
        self.logs: List[AuditLog] = []

        # Configure logging
        self.logger = logging.getLogger("AuditLogger")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Initialize rate limits
        self._init_rate_limits()

    def _init_rate_limits(self):
        """Initialize rate limiting rules"""
        self.rate_limits = {
            "api_requests": RateLimitRule(
                name="api_requests",
                window_seconds=60,
                max_requests=100
            ),
            "authentication_attempts": RateLimitRule(
                name="authentication_attempts",
                window_seconds=300,
                max_requests=10
            ),
            "file_access": RateLimitRule(
                name="file_access",
                window_seconds=300,
                max_requests=50
            ),
            "email_requests": RateLimitRule(
                name="email_requests",
                window_seconds=300,
                max_requests=30
            ),
            "whatsapp_requests": RateLimitRule(
                name="whatsapp_requests",
                window_seconds=300,
                max_requests=20
            )
        }

    def _check_rate_limit(self, rule_name: str) -> bool:
        """Check if a request is within rate limits"""
        if rule_name not in self.rate_limits:
            return True

        rule = self.rate_limits[rule_name]
        current_time = time.time()

        # Reset counter if window has expired
        if current_time >= rule.reset_time:
            rule.current_count = 0
            rule.reset_time = current_time + rule.window_seconds

        # Check if we're within limits
        if rule.current_count >= rule.max_requests:
            return False

        # Increment counter
        rule.current_count += 1
        return True

    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        return hashlib.sha256(f"{time.time()}{os.urandom(16)}".encode()).hexdigest()[:16]

    def log_event(
        self,
        category: AuditCategory,
        security_level: SecurityLevel,
        action: str,
        resource: str,
        details: Dict[str, Any] = None,
        user: Optional[str] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        rate_limit_category: Optional[str] = None
    ) -> bool:
        """Log an audit event"""
        # Check rate limiting if applicable
        if rate_limit_category and not self._check_rate_limit(rate_limit_category):
            self.logger.warning(f"Rate limit exceeded for category: {rate_limit_category}")
            return False

        # Create audit log entry
        event_id = self._generate_event_id()
        timestamp = datetime.now().isoformat()

        audit_log = AuditLog(
            timestamp=timestamp,
            category=category,
            security_level=security_level,
            event_id=event_id,
            source="personal-ai-employee",
            user=user,
            action=action,
            resource=resource,
            details=details or {},
            ip_address=ip_address,
            session_id=session_id
        )

        # Add to in-memory logs
        self.logs.append(audit_log)

        # Write to file
        self._write_to_log_file(audit_log)

        # Log to console
        self.logger.log(
            logging.INFO if security_level == SecurityLevel.INFO else
            logging.WARNING if security_level == SecurityLevel.WARNING else
            logging.ERROR,
            f"[{category.value.upper()}] {action} on {resource} by {user or 'system'}"
        )

        return True

    def _write_to_log_file(self, audit_log: AuditLog):
        """Write audit log to file"""
        # Check if file needs rotation
        if os.path.exists(self.log_file) and os.path.getsize(self.log_file) >= self.max_file_size:
            self._rotate_log_file()

        # Write log entry
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(asdict(audit_log)) + "\n")

    def _rotate_log_file(self):
        """Rotate log file"""
        backup_file = f"{self.log_file}.{int(time.time())}"
        os.rename(self.log_file, backup_file)
        self.logger.info(f"Rotated audit log: {self.log_file} -> {backup_file}")

    def get_logs(self, category: Optional[AuditCategory] = None) -> List[AuditLog]:
        """Get filtered logs"""
        if category:
            return [log for log in self.logs if log.category == category]
        return self.logs.copy()

    def get_security_alerts(self) -> List[AuditLog]:
        """Get security alerts"""
        return [
            log for log in self.logs
            if log.security_level in [SecurityLevel.WARNING, SecurityLevel.CRITICAL, SecurityLevel.ALERT]
        ]

    def detect_anomalies(self) -> List[Dict]:
        """Detect anomalies in current logs"""
        return self.anomaly_detector.detect_anomalies(self.logs)

    def generate_security_report(self) -> Dict:
        """Generate security report"""
        security_logs = self.get_security_alerts()
        anomalies = self.detect_anomalies()

        return {
            "total_logs": len(self.logs),
            "security_logs": len(security_logs),
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies,
            "recent_alerts": [
                {
                    "timestamp": log.timestamp,
                    "category": log.category.value,
                    "action": log.action,
                    "security_level": log.security_level.value,
                    "user": log.user
                }
                for log in security_logs[-10:]
            ]
        }


# CLI interface for audit logger
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Security and Audit Logger")
    parser.add_argument("--log-file", default="audit.log", help="Audit log file path")
    parser.add_argument("--max-size", type=int, default=10 * 1024 * 1024, help="Max log file size in bytes")
    parser.add_argument("--report", action="store_true", help="Generate security report")
    parser.add_argument("--test", action="store_true", help="Run test audit log")

    args = parser.parse_args()

    audit_logger = AuditLogger(log_file=args.log_file, max_file_size=args.max_size)

    if args.test:
        # Test audit logging
        print("Testing audit logger...")

        audit_logger.log_event(
            category=AuditCategory.SYSTEM,
            security_level=SecurityLevel.INFO,
            action="system_startup",
            resource="orchestrator",
            details={"version": "1.0.0"},
            user="system"
        )

        audit_logger.log_event(
            category=AuditCategory.AUTHENTICATION,
            security_level=SecurityLevel.INFO,
            action="user_login",
            resource="gmail_watcher",
            details={"success": True},
            user="admin",
            ip_address="192.168.1.100"
        )

        audit_logger.log_event(
            category=AuditCategory.SECURITY,
            security_level=SecurityLevel.WARNING,
            action="failed_login_attempt",
            resource="gmail_watcher",
            details={"attempts": 3},
            user="unknown",
            ip_address="10.0.0.5"
        )

        audit_logger.log_event(
            category=AuditCategory.DATA_ACCESS,
            security_level=SecurityLevel.INFO,
            action="file_access",
            resource="/mnt/d/Code/hackathon0/AI_Employee_Vault/config.json",
            details={"operation": "read"},
            user="filesystem_watcher",
            rate_limit_category="file_access"
        )

        print("Audit logs created successfully!")

    if args.report:
        report = audit_logger.generate_security_report()
        print(json.dumps(report, indent=2))