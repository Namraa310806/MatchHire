"""
Dashboard Definitions.

This module provides dashboard definitions for visualizing observability data.
Dashboards are defined in a format compatible with Grafana and other visualization tools.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class DashboardType(Enum):
    """Types of dashboards."""
    SEARCH = "search"
    RANKING = "ranking"
    RECOMMENDATION = "recommendation"
    INFRASTRUCTURE = "infrastructure"
    PERFORMANCE = "performance"
    OPERATIONS = "operations"
    QUALITY = "quality"


class PanelType(Enum):
    """Types of dashboard panels."""
    GRAPH = "graph"
    STAT = "stat"
    TABLE = "table"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    BARCHART = "barchart"
    PIECHART = "piechart"


@dataclass
class DashboardPanel:
    """A single panel in a dashboard."""
    
    title: str
    panel_type: PanelType
    query: str
    description: Optional[str] = None
    width: int = 6  # Grid width (1-12)
    height: int = 4  # Grid height
    x: int = 0
    y: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "type": self.panel_type.value,
            "query": self.query,
            "description": self.description,
            "width": self.width,
            "height": self.height,
            "x": self.x,
            "y": self.y,
        }


@dataclass
class Dashboard:
    """Dashboard definition."""
    
    name: str
    dashboard_type: DashboardType
    panels: List[DashboardPanel] = field(default_factory=list)
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    refresh_interval: str = "30s"
    time_range: str = "1h"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.dashboard_type.value,
            "description": self.description,
            "tags": self.tags,
            "refresh_interval": self.refresh_interval,
            "time_range": self.time_range,
            "panels": [panel.to_dict() for panel in self.panels],
        }


class DashboardRegistry:
    """
    Registry for dashboard definitions.
    
    This registry provides pre-configured dashboards for monitoring
    the search, ranking, and recommendation systems.
    """
    
    def __init__(self):
        """Initialize the dashboard registry."""
        self._dashboards: Dict[str, Dashboard] = {}
        self._register_default_dashboards()
    
    def _register_default_dashboards(self) -> None:
        """Register default dashboards."""
        self.register_dashboard(self._create_search_dashboard())
        self.register_dashboard(self._create_ranking_dashboard())
        self.register_dashboard(self._create_recommendation_dashboard())
        self.register_dashboard(self._create_infrastructure_dashboard())
        self.register_dashboard(self._create_performance_dashboard())
        self.register_dashboard(self._create_operations_dashboard())
        self.register_dashboard(self._create_quality_dashboard())
    
    def _create_search_dashboard(self) -> Dashboard:
        """Create the search dashboard."""
        panels = [
            DashboardPanel(
                title="Search Request Rate",
                panel_type=PanelType.GRAPH,
                query="rate(search_requests_total[5m])",
                description="Rate of search requests per second",
                width=12,
                height=4,
            ),
            DashboardPanel(
                title="Search Latency (p50, p95, p99)",
                panel_type=PanelType.GRAPH,
                query="histogram_quantile(0.5, rate(search_latency_seconds_bucket[5m]))",
                description="Search latency percentiles",
                width=12,
                height=4,
                y=4,
            ),
            DashboardPanel(
                title="Search Error Rate",
                panel_type=PanelType.GRAPH,
                query="rate(search_errors_total[5m]) / rate(search_requests_total[5m])",
                description="Search error rate",
                width=6,
                height=4,
                y=8,
            ),
            DashboardPanel(
                title="Zero Result Searches",
                panel_type=PanelType.GRAPH,
                query="rate(zero_results_searches_total[5m])",
                description="Rate of searches returning zero results",
                width=6,
                height=4,
                x=6,
                y=8,
            ),
            DashboardPanel(
                title="Top Search Queries",
                panel_type=PanelType.TABLE,
                query='topk(10, count by (query) (search_requests_total))',
                description="Most frequent search queries",
                width=6,
                height=4,
                y=12,
            ),
            DashboardPanel(
                title="Search Results Distribution",
                panel_type=PanelType.HISTOGRAM,
                query="histogram(search_result_count)",
                description="Distribution of result counts",
                width=6,
                height=4,
                x=6,
                y=12,
            ),
        ]
        
        return Dashboard(
            name="Search Dashboard",
            dashboard_type=DashboardType.SEARCH,
            panels=panels,
            description="Monitoring for search operations",
            tags=["search", "core"],
            refresh_interval="30s",
            time_range="1h",
        )
    
    def _create_ranking_dashboard(self) -> Dashboard:
        """Create the ranking dashboard."""
        panels = [
            DashboardPanel(
                title="Ranking Request Rate",
                panel_type=PanelType.GRAPH,
                query="rate(ranking_requests_total[5m])",
                description="Rate of ranking requests per second",
                width=12,
                height=4,
            ),
            DashboardPanel(
                title="Ranking Latency (p50, p95, p99)",
                panel_type=PanelType.GRAPH,
                query="histogram_quantile(0.95, rate(ranking_latency_seconds_bucket[5m]))",
                description="Ranking latency percentiles",
                width=12,
                height=4,
                y=4,
            ),
            DashboardPanel(
                title="Active Ranking Signals",
                panel_type=PanelType.GAUGE,
                query="ranking_signals_active",
                description="Number of active ranking signals",
                width=4,
                height=4,
                y=8,
            ),
            DashboardPanel(
                title="Signal Execution Time",
                panel_type=PanelType.BARCHART,
                query="topk(10, signal_execution_time_seconds)",
                description="Execution time for top signals",
                width=8,
                height=4,
                x=4,
                y=8,
            ),
            DashboardPanel(
                title="Top Signals by Usage",
                panel_type=PanelType.TABLE,
                query='topk(10, count by (signal_name) (signal_executions_total))',
                description="Most frequently used signals",
                width=6,
                height=4,
                y=12,
            ),
            DashboardPanel(
                title="Signal Contribution Distribution",
                panel_type=PanelType.PIECHART,
                query="sum by (signal_name) (signal_contribution)",
                description="Distribution of signal contributions",
                width=6,
                height=4,
                x=6,
                y=12,
            ),
        ]
        
        return Dashboard(
            name="Ranking Dashboard",
            dashboard_type=DashboardType.RANKING,
            panels=panels,
            description="Monitoring for ranking pipeline",
            tags=["ranking", "core"],
            refresh_interval="30s",
            time_range="1h",
        )
    
    def _create_recommendation_dashboard(self) -> Dashboard:
        """Create the recommendation dashboard."""
        panels = [
            DashboardPanel(
                title="Recommendation Request Rate",
                panel_type=PanelType.GRAPH,
                query="rate(recommendation_requests_total[5m])",
                description="Rate of recommendation requests per second",
                width=12,
                height=4,
            ),
            DashboardPanel(
                title="Recommendation Latency (p50, p95, p99)",
                panel_type=PanelType.GRAPH,
                query="histogram_quantile(0.95, rate(recommendation_latency_seconds_bucket[5m]))",
                description="Recommendation latency percentiles",
                width=12,
                height=4,
                y=4,
            ),
            DashboardPanel(
                title="Recommendations Generated",
                panel_type=PanelType.GRAPH,
                query="rate(recommendations_generated_total[5m])",
                description="Rate of recommendations generated",
                width=8,
                height=4,
                y=8,
            ),
            DashboardPanel(
                title="Recommendation Acceptance Rate",
                panel_type=PanelType.GAUGE,
                query="recommendation_acceptance_rate",
                description="Rate of accepted recommendations",
                width=4,
                height=4,
                x=8,
                y=8,
            ),
            DashboardPanel(
                title="Strategy Usage",
                panel_type=PanelType.BARCHART,
                query="topk(10, count by (strategy) (recommendation_requests_total))",
                description="Usage by recommendation strategy",
                width=6,
                height=4,
                y=12,
            ),
            DashboardPanel(
                title="Recommendation Diversity Score",
                panel_type=PanelType.GRAPH,
                query="recommendation_diversity_score",
                description="Diversity score over time",
                width=6,
                height=4,
                x=6,
                y=12,
            ),
        ]
        
        return Dashboard(
            name="Recommendation Dashboard",
            dashboard_type=DashboardType.RECOMMENDATION,
            panels=panels,
            description="Monitoring for recommendation engine",
            tags=["recommendation", "core"],
            refresh_interval="30s",
            time_range="1h",
        )
    
    def _create_infrastructure_dashboard(self) -> Dashboard:
        """Create the infrastructure dashboard."""
        panels = [
            DashboardPanel(
                title="Provider Health",
                panel_type=PanelType.GAUGE,
                query="provider_health",
                description="Health status of search provider",
                width=4,
                height=4,
            ),
            DashboardPanel(
                title="Cache Hit Rate",
                panel_type=PanelType.GAUGE,
                query="rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))",
                description="Cache hit rate",
                width=4,
                height=4,
                x=4,
            ),
            DashboardPanel(
                title="Cache Size",
                panel_type=PanelType.GAUGE,
                query="cache_size",
                description="Current cache size",
                width=4,
                height=4,
                x=8,
            ),
            DashboardPanel(
                title="Provider Request Rate",
                panel_type=PanelType.GRAPH,
                query="rate(provider_requests_total[5m])",
                description="Rate of provider requests",
                width=12,
                height=4,
                y=4,
            ),
            DashboardPanel(
                title="Provider Latency",
                panel_type=PanelType.GRAPH,
                query="histogram_quantile(0.95, rate(provider_latency_seconds_bucket[5m]))",
                description="Provider latency percentiles",
                width=12,
                height=4,
                y=8,
            ),
            DashboardPanel(
                title="Index Size",
                panel_type=PanelType.GRAPH,
                query="index_size_bytes",
                description="Search index size over time",
                width=6,
                height=4,
                y=12,
            ),
            DashboardPanel(
                title="Document Count",
                panel_type=PanelType.GRAPH,
                query="document_count",
                description="Number of indexed documents",
                width=6,
                height=4,
                x=6,
                y=12,
            ),
        ]
        
        return Dashboard(
            name="Infrastructure Dashboard",
            dashboard_type=DashboardType.INFRASTRUCTURE,
            panels=panels,
            description="Monitoring for infrastructure components",
            tags=["infrastructure", "ops"],
            refresh_interval="30s",
            time_range="1h",
        )
    
    def _create_performance_dashboard(self) -> Dashboard:
        """Create the performance dashboard."""
        panels = [
            DashboardPanel(
                title="Overall Request Rate",
                panel_type=PanelType.GRAPH,
                query="sum(rate(requests_total[5m]))",
                description="Overall request rate",
                width=12,
                height=4,
            ),
            DashboardPanel(
                title="Overall Latency (p95)",
                panel_type=PanelType.GRAPH,
                query="histogram_quantile(0.95, sum(rate(request_latency_seconds_bucket[5m])))",
                description="Overall p95 latency",
                width=12,
                height=4,
                y=4,
            ),
            DashboardPanel(
                title="Error Rate by Component",
                panel_type=PanelType.GRAPH,
                query="sum by (component) (rate(errors_total[5m])) / sum by (component) (rate(requests_total[5m]))",
                description="Error rate by component",
                width=12,
                height=4,
                y=8,
            ),
            DashboardPanel(
                title="Slow Operations",
                panel_type=PanelType.TABLE,
                query="topk(10, slow_operations_total)",
                description="Top slow operations",
                width=6,
                height=4,
                y=12,
            ),
            DashboardPanel(
                title="Timeout Rate",
                panel_type=PanelType.GRAPH,
                query="rate(timeouts_total[5m])",
                description="Rate of timeout errors",
                width=6,
                height=4,
                x=6,
                y=12,
            ),
        ]
        
        return Dashboard(
            name="Performance Dashboard",
            dashboard_type=DashboardType.PERFORMANCE,
            panels=panels,
            description="Overall performance monitoring",
            tags=["performance", "ops"],
            refresh_interval="30s",
            time_range="1h",
        )
    
    def _create_operations_dashboard(self) -> Dashboard:
        """Create the operations dashboard."""
        panels = [
            DashboardPanel(
                title="System Health",
                panel_type=PanelType.GAUGE,
                query="system_health",
                description="Overall system health status",
                width=4,
                height=4,
            ),
            DashboardPanel(
                title="Active Connections",
                panel_type=PanelType.GAUGE,
                query="active_connections",
                description="Number of active connections",
                width=4,
                height=4,
                x=4,
            ),
            DashboardPanel(
                title="Queue Size",
                panel_type=PanelType.GAUGE,
                query="queue_size",
                description="Current queue size",
                width=4,
                height=4,
                x=8,
            ),
            DashboardPanel(
                title="Recent Errors",
                panel_type=PanelType.TABLE,
                query="topk(10, errors_total)",
                description="Recent error occurrences",
                width=12,
                height=4,
                y=4,
            ),
            DashboardPanel(
                title="Component Status",
                panel_type=PanelType.TABLE,
                query="component_status",
                description="Status of all components",
                width=6,
                height=4,
                y=8,
            ),
            DashboardPanel(
                title="Recent Diagnostics",
                panel_type=PanelType.TABLE,
                query="topk(10, diagnostics_total)",
                description="Recent diagnostic events",
                width=6,
                height=4,
                x=6,
                y=8,
            ),
        ]
        
        return Dashboard(
            name="Operations Dashboard",
            dashboard_type=DashboardType.OPERATIONS,
            panels=panels,
            description="Operations and health monitoring",
            tags=["operations", "health"],
            refresh_interval="30s",
            time_range="1h",
        )
    
    def _create_quality_dashboard(self) -> Dashboard:
        """Create the quality dashboard."""
        panels = [
            DashboardPanel(
                title="Click-Through Rate",
                panel_type=PanelType.GRAPH,
                query="quality_ctr",
                description="Click-through rate over time",
                width=6,
                height=4,
            ),
            DashboardPanel(
                title="Recommendation Acceptance Rate",
                panel_type=PanelType.GRAPH,
                query="quality_acceptance_rate",
                description="Recommendation acceptance rate",
                width=6,
                height=4,
                x=6,
            ),
            DashboardPanel(
                title="Search Success Rate",
                panel_type=PanelType.GRAPH,
                query="quality_success_rate",
                description="Search success rate",
                width=6,
                height=4,
                y=4,
            ),
            DashboardPanel(
                title="Search Abandonment Rate",
                panel_type=PanelType.GRAPH,
                query="quality_abandonment_rate",
                description="Search abandonment rate",
                width=6,
                height=4,
                x=6,
                y=4,
            ),
            DashboardPanel(
                title="Recommendation Diversity Score",
                panel_type=PanelType.GRAPH,
                query="quality_diversity_score",
                description="Diversity score over time",
                width=6,
                height=4,
                y=8,
            ),
            DashboardPanel(
                title="Coverage Score",
                panel_type=PanelType.GRAPH,
                query="quality_coverage_score",
                description="Coverage score over time",
                width=6,
                height=4,
                x=6,
                y=8,
            ),
        ]
        
        return Dashboard(
            name="Quality Dashboard",
            dashboard_type=DashboardType.QUALITY,
            panels=panels,
            description="Quality metrics monitoring",
            tags=["quality", "ml"],
            refresh_interval="5m",
            time_range="24h",
        )
    
    def register_dashboard(self, dashboard: Dashboard) -> None:
        """
        Register a dashboard.
        
        Args:
            dashboard: Dashboard to register
        """
        self._dashboards[dashboard.name] = dashboard
    
    def get_dashboard(self, name: str) -> Optional[Dashboard]:
        """
        Get a dashboard by name.
        
        Args:
            name: Dashboard name
            
        Returns:
            Dashboard or None
        """
        return self._dashboards.get(name)
    
    def get_all_dashboards(self) -> Dict[str, Dashboard]:
        """Get all registered dashboards."""
        return self._dashboards.copy()
    
    def get_dashboards_by_type(self, dashboard_type: DashboardType) -> List[Dashboard]:
        """
        Get dashboards by type.
        
        Args:
            dashboard_type: Dashboard type
            
        Returns:
            List of dashboards
        """
        return [
            dashboard for dashboard in self._dashboards.values()
            if dashboard.dashboard_type == dashboard_type
        ]
    
    def export_grafana(self, dashboard_name: str) -> Dict[str, Any]:
        """
        Export a dashboard in Grafana format.
        
        Args:
            dashboard_name: Name of dashboard to export
            
        Returns:
            Grafana-formatted dashboard
        """
        dashboard = self.get_dashboard(dashboard_name)
        if not dashboard:
            return {}
        
        return {
            "dashboard": {
                "title": dashboard.name,
                "description": dashboard.description,
                "tags": dashboard.tags,
                "refresh": dashboard.refresh_interval,
                "time": {
                    "from": f"now-{dashboard.time_range}",
                    "to": "now",
                },
                "panels": [
                    {
                        "title": panel.title,
                        "type": panel.panel_type.value,
                        "targets": [
                            {
                                "expr": panel.query,
                                "refId": "A",
                            }
                        ],
                        "description": panel.description,
                        "gridPos": {
                            "w": panel.width,
                            "h": panel.height,
                            "x": panel.x,
                            "y": panel.y,
                        },
                    }
                    for panel in dashboard.panels
                ],
            },
            "overwrite": True,
        }
    
    def export_all_grafana(self) -> List[Dict[str, Any]]:
        """
        Export all dashboards in Grafana format.
        
        Returns:
            List of Grafana-formatted dashboards
        """
        return [
            self.export_grafana(name)
            for name in self._dashboards.keys()
        ]
