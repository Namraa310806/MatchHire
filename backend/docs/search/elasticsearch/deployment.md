# Elasticsearch Deployment Guide

## Overview

This guide covers deploying the Elasticsearch provider in production environments, including infrastructure setup, configuration, and operational procedures.

## Prerequisites

### Software Requirements

- Elasticsearch 8.x or later
- Python 3.8+
- Django 5.1+
- MatchHire backend application

### Hardware Requirements

### Development
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB SSD

### Production (Small)
- CPU: 4 cores
- RAM: 8GB
- Disk: 100GB SSD

### Production (Medium)
- CPU: 8 cores
- RAM: 16GB
- Disk: 500GB SSD

### Production (Large)
- CPU: 16+ cores
- RAM: 32GB+
- Disk: 1TB+ SSD

## Installation

### Install Elasticsearch

#### Using Docker (Recommended for Development)

```bash
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" \
  -e "xpack.security.enabled=false" \
  docker.elastic.co/elasticsearch/elasticsearch:8.15.0
```

#### Using Docker Compose (Recommended for Production)

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.15.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms2g -Xmx2g
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=changeme
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    networks:
      - elastic

volumes:
  es_data:
    driver: local

networks:
  elastic:
    driver: bridge
```

#### Using Package Manager (Ubuntu/Debian)

```bash
# Add Elasticsearch repository
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
sudo apt-get install apt-transport-https
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-8.x.list

# Install Elasticsearch
sudo apt-get update
sudo apt-get install elasticsearch

# Start Elasticsearch
sudo systemctl start elasticsearch
sudo systemctl enable elasticsearch
```

### Install Python Dependencies

```bash
pip install elasticsearch==8.15.0
```

Or update requirements.txt:

```bash
pip install -r requirements.txt
```

## Configuration

### Production Configuration

Update Django settings:

```python
# settings.py
SEARCH_PROVIDER = "elasticsearch"

SEARCH_CONFIG = {
    "elasticsearch": {
        "hosts": [
            "https://es1.production.com:9200",
            "https://es2.production.com:9200",
            "https://es3.production.com:9200",
        ],
        "username": os.getenv("ES_USERNAME"),
        "password": os.getenv("ES_PASSWORD"),
        "verify_certs": True,
        "ca_certs": "/etc/ssl/certs/ca.crt",
        "request_timeout": 20,
        "max_retries": 5,
        "retry_on_timeout": True,
        "retry_on_status": [502, 503, 504],
        "http_compress": True,
        "max_connections": 50,
        "max_connections_per_host": 20,
        "index_prefix": "matchhire",
        "use_aliases": True,
        "refresh_interval": "1s",
        "number_of_shards": 5,
        "number_of_replicas": 2,
    }
}
```

### Environment Variables

Create `.env` file:

```bash
# Elasticsearch Configuration
ES_HOSTS=https://es1.production.com:9200,https://es2.production.com:9200,https://es3.production.com:9200
ES_USERNAME=elastic
ES_PASSWORD=changeme
ES_VERIFY_CERTS=true
ES_CA_CERTS=/etc/ssl/certs/ca.crt
ES_REQUEST_TIMEOUT=20
ES_MAX_RETRIES=5
ES_INDEX_PREFIX=matchhire
ES_USE_ALIASES=true
ES_NUMBER_OF_SHARDS=5
ES_NUMBER_OF_REPLICAS=2
```

## Cluster Setup

### Single Node Cluster

For development or small production deployments:

```yaml
# elasticsearch.yml
cluster.name: matchhire
node.name: node-1
network.host: 0.0.0.0
discovery.type: single-node
```

### Multi-Node Cluster

For production deployments:

```yaml
# elasticsearch.yml (Node 1)
cluster.name: matchhire
node.name: node-1
network.host: 0.0.0.0
discovery.seed_hosts: ["es2", "es3"]
cluster.initial_master_nodes: ["node-1", "node-2", "node-3"]

# elasticsearch.yml (Node 2)
cluster.name: matchhire
node.name: node-2
network.host: 0.0.0.0
discovery.seed_hosts: ["es1", "es3"]
cluster.initial_master_nodes: ["node-1", "node-2", "node-3"]

# elasticsearch.yml (Node 3)
cluster.name: matchhire
node.name: node-3
network.host: 0.0.0.0
discovery.seed_hosts: ["es1", "es2"]
cluster.initial_master_nodes: ["node-1", "node-2", "node-3"]
```

### Security Configuration

Enable security in production:

```yaml
# elasticsearch.yml
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.verification_mode: certificate
xpack.security.transport.ssl.keystore.path: elastic-certificates.p12
xpack.security.transport.ssl.truststore.path: elastic-certificates.p12
xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.keystore.path: elastic-certificates.p12
xpack.security.http.ssl.truststore.path: elastic-certificates.p12
```

Generate certificates:

```bash
/usr/share/elasticsearch/bin/elasticsearch-certutil ca
/usr/share/elasticsearch/bin/elasticsearch-certutil cert --ca elastic.p12
```

Set passwords:

```bash
/usr/share/elasticsearch/bin/elasticsearch-setup-passwords interactive
```

## Index Initialization

Indices are automatically created during provider initialization. To manually initialize:

```python
from apps.search.registry import get_registry

registry = get_registry()
provider = registry.get_provider("elasticsearch")

# Verify cluster is healthy
health = provider.health()
if not health.healthy:
    raise Exception("Cluster is not healthy")

# Indices are created automatically during initialization
print("Elasticsearch provider initialized successfully")
```

## Deployment Steps

### 1. Prepare Infrastructure

- Provision servers or containers
- Install Elasticsearch
- Configure cluster
- Enable security
- Set up monitoring

### 2. Configure Application

- Update Django settings
- Set environment variables
- Install Python dependencies
- Configure SSL certificates

### 3. Test Connection

```python
from apps.search.registry import get_registry

registry = get_registry()
provider = registry.get_provider("elasticsearch")

# Test connection
health = provider.health()
assert health.healthy, "Cluster is not healthy"

# Test search
results = provider.search(entity_type="job", query="test")
print("Connection test successful")
```

### 4. Initialize Indices

Indices are created automatically on first use. Verify:

```python
# List indices
indices = provider.index_lifecycle.list_indices()
print(f"Indices: {indices}")
```

### 5. Deploy Application

- Deploy Django application
- Run migrations
- Start application servers
- Verify search functionality

### 6. Monitor Deployment

- Monitor cluster health
- Monitor application logs
- Monitor search performance
- Set up alerts

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "matchhire_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.15.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms2g -Xmx2g
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=changeme
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    networks:
      - elastic

  web:
    build: .
    container_name: matchhire_web
    ports:
      - "8000:8000"
    environment:
      - SEARCH_PROVIDER=elasticsearch
      - ES_HOSTS=http://elasticsearch:9200
      - ES_USERNAME=elastic
      - ES_PASSWORD=changeme
    depends_on:
      - elasticsearch
    networks:
      - elastic

volumes:
  es_data:

networks:
  elastic:
    driver: bridge
```

## Kubernetes Deployment

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: elasticsearch-config
data:
  elasticsearch.yml: |
    cluster.name: matchhire
    network.host: 0.0.0.0
    discovery.type: single-node
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: elasticsearch-secret
type: Opaque
data:
  username: ZWxhc3RpYw==
  password: Y2hhbmdlbWU=
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: elasticsearch
spec:
  replicas: 1
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:8.15.0
        ports:
        - containerPort: 9200
        env:
        - name: discovery.type
          value: single-node
        - name: ES_JAVA_OPTS
          value: "-Xms2g -Xmx2g"
        volumeMounts:
        - name: config
          mountPath: /usr/share/elasticsearch/config/elasticsearch.yml
          subPath: elasticsearch.yml
        - name: data
          mountPath: /usr/share/elasticsearch/data
      volumes:
      - name: config
        configMap:
          name: elasticsearch-config
      - name: data
        emptyDir: {}
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch
spec:
  selector:
    app: elasticsearch
  ports:
  - port: 9200
    targetPort: 9200
  type: ClusterIP
```

## Monitoring

### Health Checks

```python
# Add to health check endpoint
from apps.search.registry import get_registry

def health_check():
    registry = get_registry()
    provider = registry.get_provider()
    health = provider.health()
    
    return {
        "status": "healthy" if health.healthy else "unhealthy",
        "cluster_status": health.details.get("status"),
        "nodes": health.details.get("number_of_nodes"),
    }
```

### Metrics

Use Prometheus for monitoring:

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
search_requests = Counter('search_requests_total', 'Total search requests')
search_latency = Histogram('search_latency_seconds', 'Search latency')
cluster_health = Gauge('cluster_health', 'Cluster health status')
document_count = Gauge('document_count', 'Document count', ['entity_type'])
```

### Alerts

Set up alerts for:
- Cluster status not green
- High error rate
- Slow queries
- High memory usage
- Disk space low

## Backup Strategy

### Snapshot Repository

```python
# Configure snapshot repository
provider.client.snapshot.create_repository(
    repository="matchhire_backup",
    body={
        "type": "s3",
        "settings": {
            "bucket": "matchhire-backups",
            "region": "us-east-1"
        }
    }
)
```

### Automated Snapshots

```python
# Create scheduled snapshot using cron
from celery import shared_task

@shared_task
def create_snapshot():
    provider.client.snapshot.create(
        repository="matchhire_backup",
        snapshot=f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        body={
            "indices": "matchhire_*",
            "include_global_state": False
        }
    )
```

### Snapshot Retention

```python
# Clean up old snapshots
snapshots = provider.client.snapshot.get(repository="matchhire_backup")
for snapshot in snapshots["snapshots"]:
    snapshot_date = datetime.strptime(snapshot["snapshot"], "snapshot_%Y%m%d_%H%M%S")
    if (datetime.now() - snapshot_date).days > 30:
        provider.client.snapshot.delete(
            repository="matchhire_backup",
            snapshot=snapshot["snapshot"]
        )
```

## Scaling

### Vertical Scaling

Increase resources:

```yaml
# Docker Compose
environment:
  - ES_JAVA_OPTS=-Xms4g -Xmx4g  # Increase heap
```

### Horizontal Scaling

Add more nodes:

```yaml
# Docker Compose
services:
  elasticsearch1:
    # ... configuration
  elasticsearch2:
    # ... configuration
  elasticsearch3:
    # ... configuration
```

### Shard Strategy

- Small datasets: 1-3 shards per index
- Medium datasets: 3-5 shards per index
- Large datasets: 5-10 shards per index
- Formula: `shards = max(1, data_size_gb / 20)`

## Rolling Updates

### Zero-Downtime Deployment

1. Create new versioned index
2. Reindex data to new index
3. Switch alias to new index
4. Verify new index
5. Cleanup old indices

```python
# Deployment script
def deploy_new_index_version(entity_type):
    provider = get_provider("elasticsearch")
    
    # Create new versioned index
    new_index = provider.create_versioned_index(
        entity_type=entity_type,
        switch_alias=False
    )
    
    # Reindex data
    reindex_data(entity_type, new_index)
    
    # Switch alias
    old_index = provider.index_lifecycle.get_index_name(entity_type)
    provider.index_lifecycle.switch_alias(
        entity_type=entity_type,
        old_index=old_index,
        new_index=new_index
    )
    
    # Cleanup
    provider.cleanup_old_indices(entity_type, keep_versions=2)
```

## Troubleshooting Deployment

### Connection Issues

```bash
# Test Elasticsearch is running
curl http://localhost:9200

# Check logs
docker logs elasticsearch

# Check cluster health
curl http://localhost:9200/_cluster/health
```

### Memory Issues

```bash
# Check JVM heap
curl http://localhost:9200/_nodes/stats/jvm

# Increase heap size
ES_JAVA_OPTS=-Xms4g -Xmx4g
```

### Disk Space Issues

```bash
# Check disk usage
curl http://localhost:9200/_cat/allocation?v

# Cleanup old indices
provider.cleanup_old_indices(entity_type="job", keep_versions=2)
```

## Best Practices

1. **Use Docker** for consistent deployments
2. **Enable security** in production
3. **Monitor cluster health** continuously
4. **Backup regularly** using snapshots
5. **Use aliases** for zero-downtime deployments
6. **Configure appropriate heap size** (50% of RAM)
7. **Use SSD storage** for better performance
8. **Set up monitoring and alerts**
9. **Test in staging** before production
10. **Document deployment procedures**
