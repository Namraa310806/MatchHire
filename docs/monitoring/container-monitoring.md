# Container Monitoring Integration

This document describes how to integrate MatchHire containers with the monitoring stack for production deployments.

## Overview

MatchHire containers expose metrics and health endpoints that can be scraped by Prometheus and monitored by orchestration systems.

## Container Metrics

### Application Metrics (Prometheus)

The web container exposes Prometheus metrics at `/api/v1/metrics/`.

**Endpoint**: `http://web:8000/api/v1/metrics/`
**Format**: Prometheus text format
**Scrape Interval**: 15 seconds

**Prometheus Configuration**:
```yaml
scrape_configs:
  - job_name: 'matchhire-web'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/api/v1/metrics/'
    scrape_interval: 15s
    scrape_timeout: 10s
```

### Container Metrics (cAdvisor)

cAdvisor provides container-level metrics for all containers.

**Endpoint**: `http://cadvisor:8080/metrics`
**Metrics Include**:
- CPU usage
- Memory usage
- Network I/O
- Disk I/O
- Container uptime

**Prometheus Configuration**:
```yaml
scrape_configs:
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Node Metrics (Node Exporter)

Node Exporter provides host-level metrics.

**Endpoint**: `http://node-exporter:9100/metrics`
**Metrics Include**:
- CPU
- Memory
- Disk
- Network
- Filesystem

**Prometheus Configuration**:
```yaml
scrape_configs:
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

## Health Checks

### Kubernetes Health Checks

**Liveness Probe**:
```yaml
livenessProbe:
  httpGet:
    path: /api/v1/health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

**Readiness Probe**:
```yaml
readinessProbe:
  httpGet:
    path: /api/v1/health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Docker Health Check

**Docker Compose Configuration**:
```yaml
services:
  web:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Docker Compose Integration

### Adding Monitoring Services

Add the following services to `docker-compose.yml` for local development:

```yaml
services:
  # Existing services...
  
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./docker/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - matchhire-network

  # Grafana
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./docs/monitoring/grafana-dashboards.json:/etc/grafana/provisioning/dashboards/dashboard.json
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    networks:
      - matchhire-network

  # cAdvisor
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    networks:
      - matchhire-network

  # Node Exporter
  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - matchhire-network

volumes:
  prometheus_data:
  grafana_data:

networks:
  matchhire-network:
    driver: bridge
```

### Prometheus Configuration

Create `docker/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'matchhire-web'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/api/v1/metrics/'
    scrape_interval: 15s

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

## Kubernetes Integration

### Service and Deployment

**Service**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: matchhire-web
  labels:
    app: matchhire
    component: web
spec:
  ports:
  - port: 8000
    name: http
  selector:
    app: matchhire
    component: web
```

**Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: matchhire-web
  labels:
    app: matchhire
    component: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: matchhire
      component: web
  template:
    metadata:
      labels:
        app: matchhire
        component: web
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/api/v1/metrics/"
    spec:
      containers:
      - name: web
        image: matchhire-backend:latest
        ports:
        - containerPort: 8000
          name: http
        livenessProbe:
          httpGet:
            path: /api/v1/health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: SENTRY_DSN
          valueFrom:
            secretKeyRef:
              name: matchhire-secrets
              key: sentry-dsn
```

### ServiceMonitor (Prometheus Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: matchhire-web
  labels:
    app: matchhire
    component: web
spec:
  selector:
    matchLabels:
      app: matchhire
      component: web
  endpoints:
  - port: http
    path: /api/v1/metrics/
    interval: 15s
    scrapeTimeout: 10s
```

### PodMonitor (Prometheus Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: matchhire-pods
  labels:
    app: matchhire
spec:
  selector:
    matchLabels:
      app: matchhire
  podMetricsEndpoints:
  - port: http
    path: /api/v1/metrics/
    interval: 15s
```

## Grafana Dashboards

### Import Dashboard

1. Navigate to Grafana UI
2. Go to Dashboards → Import
3. Upload `docs/monitoring/grafana-dashboards.json`
4. Select Prometheus data source
5. Save dashboard

### Dashboard Variables

Configure the following variables in Grafana:
- `instance`: Container instance
- `job`: Prometheus job name
- `environment`: Environment (production, staging)

## Alerting Configuration

### Prometheus Alert Rules

Create `docker/alerts.yml`:

```yaml
groups:
  - name: matchhire_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100 > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}% for the last 5 minutes"

      - alert: DatabaseDown
        expr: up{job="matchhire-web"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"
          description: "Database has been down for more than 2 minutes"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "P95 latency is {{ $value }}s"
```

### Alertmanager Configuration

Create `docker/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

  routes:
  - match:
      severity: critical
    receiver: 'pagerduty'
  - match:
      severity: warning
    receiver: 'slack'

receivers:
  - name: 'default'
  
  - name: 'pagerduty'
    pagerduty_configs:
    - service_key: '<PAGERDUTY_SERVICE_KEY>'
  
  - name: 'slack'
    slack_configs:
    - api_url: '<SLACK_WEBHOOK_URL>'
      channel: '#alerts'
      title: '{{ .GroupLabels.alertname }}'
      text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

## Monitoring Stack Deployment

### Docker Compose

```bash
# Start monitoring stack
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Access services
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
# cAdvisor: http://localhost:8080
# Node Exporter: http://localhost:9100
```

### Kubernetes

```bash
# Deploy Prometheus Operator
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml

# Deploy monitoring stack
kubectl apply -f k8s/monitoring/
```

## Verification

### Verify Metrics Endpoint

```bash
# Check metrics endpoint
curl http://localhost:8000/api/v1/metrics/

# Verify metrics are present
curl http://localhost:8000/api/v1/metrics/ | grep http_requests_total
```

### Verify Health Endpoints

```bash
# Check liveness
curl http://localhost:8000/api/v1/health/live

# Check readiness
curl http://localhost:8000/api/v1/health/ready

# Check detailed health
curl http://localhost:8000/api/v1/health/detailed
```

### Verify Prometheus Scraping

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify metrics in Prometheus
curl http://localhost:9090/api/v1/query?query=http_requests_total
```

## Troubleshooting

### Metrics Not Appearing

1. Check if metrics endpoint is accessible
2. Verify Prometheus configuration
3. Check Prometheus logs
4. Verify network connectivity

### Health Checks Failing

1. Check application logs
2. Verify database connectivity
3. Verify Redis connectivity
4. Check resource availability

### High Resource Usage

1. Check container metrics in cAdvisor
2. Review Grafana dashboards
3. Check for memory leaks
4. Scale resources if needed

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [cAdvisor Documentation](https://github.com/google/cadvisor)
- [Node Exporter Documentation](https://github.com/prometheus/node_exporter)
- [Kubernetes Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
