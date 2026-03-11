#!/usr/bin/env python3
"""
Analytics Module

Tracks performance metrics, user engagement, and system efficiency.
Provides dashboards for monitoring key performance indicators.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class EventType(Enum):
    SYSTEM = "system"
    USER = "user"
    INTEGRATION = "integration"
    ERROR = "error"
    PERFORMANCE = "performance"


@dataclass
class Metric:
    name: str
    type: MetricType
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    event_id: str
    type: EventType
    source: str
    description: str
    metadata: Dict[str, Any]
    timestamp: float
    user: Optional[str] = None


@dataclass
class KPI:
    name: str
    value: float
    trend: float
    target: Optional[float] = None
    status: str = "normal"


class AnalyticsEngine:
    def __init__(self):
        self.metrics: List[Metric] = []
        self.events: List[Event] = []
        self.kpis: Dict[str, KPI] = {}
        self.logger = logging.getLogger("AnalyticsEngine")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record a metric"""
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        )
        self.metrics.append(metric)
        self.logger.debug(f"Recorded metric: {name} = {value}")

    def record_event(
        self,
        event_type: EventType,
        source: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None
    ):
        """Record an event"""
        event = Event(
            event_id=f"event_{int(time.time() * 1000)}_{len(self.events)}",
            type=event_type,
            source=source,
            description=description,
            metadata=metadata or {},
            timestamp=time.time(),
            user=user
        )
        self.events.append(event)
        self.logger.info(f"Recorded event: {event_type.value} - {description}")

    def calculate_kpis(self):
        """Calculate key performance indicators"""
        # Clear existing KPIs
        self.kpis.clear()

        # Calculate system health KPI
        system_health = self._calculate_system_health()
        self.kpis["system_health"] = KPI(
            name="System Health",
            value=system_health,
            trend=self._calculate_trend("system_health", system_health),
            target=95.0,
            status="good" if system_health >= 90 else "warning" if system_health >= 75 else "critical"
        )

        # Calculate event processing efficiency
        efficiency = self._calculate_processing_efficiency()
        self.kpis["processing_efficiency"] = KPI(
            name="Processing Efficiency",
            value=efficiency,
            trend=self._calculate_trend("processing_efficiency", efficiency),
            target=90.0,
            status="good" if efficiency >= 85 else "warning" if efficiency >= 70 else "critical"
        )

        # Calculate average response time
        avg_response_time = self._calculate_avg_response_time()
        self.kpis["avg_response_time"] = KPI(
            name="Average Response Time",
            value=avg_response_time,
            trend=self._calculate_trend("avg_response_time", avg_response_time),
            target=100.0,  # ms
            status="good" if avg_response_time <= 100 else "warning" if avg_response_time <= 500 else "critical"
        )

        # Calculate error rate
        error_rate = self._calculate_error_rate()
        self.kpis["error_rate"] = KPI(
            name="Error Rate",
            value=error_rate,
            trend=self._calculate_trend("error_rate", error_rate),
            target=0.05,
            status="good" if error_rate <= 0.02 else "warning" if error_rate <= 0.05 else "critical"
        )

        # Calculate user engagement
        engagement = self._calculate_user_engagement()
        self.kpis["user_engagement"] = KPI(
            name="User Engagement",
            value=engagement,
            trend=self._calculate_trend("user_engagement", engagement),
            target=80.0,
            status="good" if engagement >= 75 else "warning" if engagement >= 50 else "critical"
        )

    def _calculate_system_health(self) -> float:
        """Calculate system health percentage"""
        # Get last 100 metrics
        recent_metrics = self.metrics[-100:]

        # Calculate based on different metric types
        counter_metrics = [m.value for m in recent_metrics if m.type == MetricType.COUNTER]
        gauge_metrics = [m.value for m in recent_metrics if m.type == MetricType.GAUGE]
        timer_metrics = [m.value for m in recent_metrics if m.type == MetricType.TIMER]

        # Simple weighted health calculation
        health_components = []
        if counter_metrics:
            health_components.append(min(100.0, sum(counter_metrics) / len(counter_metrics)))
        if gauge_metrics:
            health_components.append(min(100.0, sum(gauge_metrics) / len(gauge_metrics)))
        if timer_metrics:
            avg_timer = statistics.mean(timer_metrics)
            # Convert timer (ms) to health (100 = <100ms, 0 = >1000ms)
            timer_health = max(0.0, 100.0 - (avg_timer - 100.0) * 0.1)
            health_components.append(timer_health)

        return statistics.mean(health_components) if health_components else 0.0

    def _calculate_processing_efficiency(self) -> float:
        """Calculate processing efficiency"""
        # Get events from last hour
        one_hour_ago = time.time() - 3600
        recent_events = [e for e in self.events if e.timestamp >= one_hour_ago]

        if not recent_events:
            return 0.0

        # Calculate based on event types
        system_events = len([e for e in recent_events if e.type == EventType.SYSTEM])
        user_events = len([e for e in recent_events if e.type == EventType.USER])
        integration_events = len([e for e in recent_events if e.type == EventType.INTEGRATION])
        total_events = len(recent_events)

        # Efficiency: more system/integration events relative to user events is better
        if user_events == 0:
            return 100.0 if total_events > 0 else 0.0

        efficiency_ratio = (system_events + integration_events) / user_events
        return min(100.0, efficiency_ratio * 10.0)

    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time in milliseconds"""
        # Get timer metrics from last hour
        one_hour_ago = time.time() - 3600
        timer_metrics = [
            m.value for m in self.metrics
            if m.type == MetricType.TIMER and m.timestamp >= one_hour_ago
        ]

        return statistics.mean(timer_metrics) if timer_metrics else 0.0

    def _calculate_error_rate(self) -> float:
        """Calculate error rate (errors per total events)"""
        # Get events from last hour
        one_hour_ago = time.time() - 3600
        recent_events = [e for e in self.events if e.timestamp >= one_hour_ago]

        if not recent_events:
            return 0.0

        error_events = len([e for e in recent_events if e.type == EventType.ERROR])
        return error_events / len(recent_events)

    def _calculate_user_engagement(self) -> float:
        """Calculate user engagement percentage"""
        # Get user events from last 24 hours
        one_day_ago = time.time() - 86400
        user_events = [e for e in self.events if e.type == EventType.USER and e.timestamp >= one_day_ago]

        if not user_events:
            return 0.0

        # Engagement based on frequency and recency
        now = time.time()
        recency_factor = max(0.0, 1.0 - (now - max(e.timestamp for e in user_events)) / 86400.0)
        frequency_factor = min(100.0, len(user_events) / 10.0)  # Cap at 10 events per day

        return (recency_factor + frequency_factor) * 50.0

    def _calculate_trend(self, metric_name: str, current_value: float) -> float:
        """Calculate trend for a metric"""
        # Get historical values for the metric
        historical_values = [
            m.value for m in self.metrics
            if m.name == metric_name and m.timestamp < time.time() - 300  # Last 5 minutes
        ][-10:]  # Last 10 values

        if len(historical_values) < 2:
            return 0.0

        # Calculate simple trend (slope)
        avg_historical = statistics.mean(historical_values)
        return (current_value - avg_historical) / avg_historical

    def get_kpis(self) -> Dict[str, KPI]:
        """Get all KPIs"""
        return self.kpis.copy()

    def get_metrics_summary(self, time_window: int = 3600) -> Dict:
        """Get metrics summary for a time window"""
        window_start = time.time() - time_window
        window_metrics = [m for m in self.metrics if m.timestamp >= window_start]

        if not window_metrics:
            return {}

        summary = {}
        for metric_type in MetricType:
            type_metrics = [m for m in window_metrics if m.type == metric_type]
            if type_metrics:
                values = [m.value for m in type_metrics]
                summary[metric_type.value] = {
                    "count": len(values),
                    "average": statistics.mean(values) if values else 0.0,
                    "min": min(values) if values else 0.0,
                    "max": max(values) if values else 0.0
                }

        return summary

    def get_events_by_type(self, event_type: EventType, time_window: int = 3600) -> List[Event]:
        """Get events by type within time window"""
        window_start = time.time() - time_window
        return [
            e for e in self.events
            if e.type == event_type and e.timestamp >= window_start
        ]

    def generate_report(self, time_window: int = 86400) -> Dict:
        """Generate comprehensive analytics report"""
        self.calculate_kpis()

        return {
            "timestamp": datetime.now().isoformat(),
            "time_window": time_window,
            "kpis": {name: asdict(kpi) for name, kpi in self.kpis.items()},
            "metrics_summary": self.get_metrics_summary(time_window),
            "event_counts": {
                str(event_type.value): len(self.get_events_by_type(event_type, time_window))
                for event_type in EventType
            },
            "recent_events": [
                {
                    "type": e.type.value,
                    "source": e.source,
                    "description": e.description,
                    "timestamp": datetime.fromtimestamp(e.timestamp).isoformat(),
                    "user": e.user
                }
                for e in self.events[-10:]
            ]
        }


# CLI interface for analytics engine
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analytics Engine")
    parser.add_argument("--record", action="store_true", help="Record sample metrics and events")
    parser.add_argument("--report", action="store_true", help="Generate analytics report")
    parser.add_argument("--status", action="store_true", help="Show current KPIs")
    parser.add_argument("--test", action="store_true", help="Run test analytics")

    args = parser.parse_args()

    engine = AnalyticsEngine()

    if args.test:
        print("Testing analytics engine...")

        # Record sample metrics
        engine.record_metric("cpu_usage", 23.5, MetricType.GAUGE)
        engine.record_metric("memory_usage", 1.2, MetricType.GAUGE)
        engine.record_metric("api_response_time", 45.2, MetricType.TIMER)
        engine.record_metric("file_operations", 15, MetricType.COUNTER)

        # Record sample events
        engine.record_event(EventType.SYSTEM, "orchestrator", "System startup completed")
        engine.record_event(EventType.USER, "admin", "User logged in", metadata={"role": "admin"})
        engine.record_event(EventType.INTEGRATION, "gmail_watcher", "Email processing completed", metadata={"emails_processed": 5})
        engine.record_event(EventType.ERROR, "filesystem_watcher", "File access error", metadata={"file": "/path/to/file", "error": "Permission denied"})

        print("Sample metrics and events recorded!")

    if args.record:
        print("Recording metrics and events...")

        # Simulate continuous recording
        for i in range(10):
            engine.record_metric(f"test_metric_{i}", i * 1.5, MetricType.GAUGE)
            engine.record_event(EventType.PERFORMANCE, "analytics", f"Test event {i}")
            time.sleep(0.1)

        print("Recording complete!")

    if args.status:
        engine.calculate_kpis()
        print("Current KPIs:")
        for name, kpi in engine.get_kpis().items():
            print(f"  {name}: {kpi.value:.2f} ({kpi.status}) - Trend: {kpi.trend:.2f}")

    if args.report:
        report = engine.generate_report()
        print(json.dumps(report, indent=2))