# Elasticsearch Configuration

## Overview

The Elasticsearch provider is configured through Django settings with sensible defaults. All configuration is environment-driven with no hardcoded values.

## Configuration Structure

```python
# Django settings.py
SEARCH_PROVIDER = "elasticsearch"

SEARCH_CONFIG = {
    "elasticsearch": {
        # Connection settings
        "hosts": ["http://localhost:9200"],
        "username": None,
        "password": None,
        "api_key": None,
        "cloud_id": None,

        # SSL/TLS settings
        "verify_certs": True,
        "ca_certs": None,
        "client_cert": None,
        "client_key": None,
        "ssl_show_warn": True,

        # Timeout and retry settings
        "request_timeout": 30,
        "max_retries": 3,
        "retry_on_timeout": True,
        "retry_on_status": [502, 503, 504],

        # Connection pool settings
        "http_compress": False,
        "max_connections": 10,
        "max_connections_per_host": 10,
        "connection_class": None,

        # Index settings
        "index_prefix": "matchhire",
        "use_aliases": True,
        "refresh_interval": "1s",
        "number_of_shards": 3,
        "number_of_replicas": 1,
    }
}
```

## Connection Settings

### Hosts

List of Elasticsearch node URLs.

```python
"hosts": ["http://localhost:9200"]
```

**Examples:**
- Single node: `["http://localhost:9200"]`
- Multiple nodes: `["http://es1:9200", "http://es2:9200", "http://es3:9200"]`
- HTTPS: `["https://elasticsearch.example.com:9200"]`

### Authentication

#### Basic Auth

```python
"username": "elastic",
"password": "changeme"
```

#### API Key

```python
"api_key": "base64_encoded_api_key"
```

#### Cloud ID (Elastic Cloud)

```python
"cloud_id": "my_cluster:abc123..."
```

## SSL/TLS Settings

### Certificate Verification

```python
"verify_certs": True  # Verify SSL certificates
```

**Security Note:** Set to `False` only for development with self-signed certificates.

### Custom CA Certificates

```python
"ca_certs": "/path/to/ca.crt"
```

### Client Certificates

```python
"client_cert": "/path/to/client.crt",
"client_key": "/path/to/client.key"
```

### SSL Warnings

```python
"ssl_show_warn": True  # Show SSL warnings
```

## Timeout and Retry Settings

### Request Timeout

```python
"request_timeout": 30  # seconds
```

**Recommendations:**
- Development: 30 seconds
- Production: 10-30 seconds
- Bulk operations: 60-120 seconds

### Max Retries

```python
"max_retries": 3
```

**Recommendations:**
- Development: 1-2 retries
- Production: 3-5 retries

### Retry on Timeout

```python
"retry_on_timeout": True
```

### Retry on Status

```python
"retry_on_status": [502, 503, 504]
```

**Common Status Codes:**
- `502`: Bad Gateway
- `503`: Service Unavailable
- `504`: Gateway Timeout

## Connection Pool Settings

### HTTP Compression

```python
"http_compress": False
```

**Recommendations:**
- Enable for large payloads
- Disable for small frequent requests

### Max Connections

```python
"max_connections": 10
```

**Recommendations:**
- Development: 5-10 connections
- Production: 20-50 connections

### Max Connections Per Host

```python
"max_connections_per_host": 10
```

**Recommendations:**
- Match or exceed `max_connections`
- Distribute across cluster nodes

## Index Settings

### Index Prefix

```python
"index_prefix": "matchhire"
```

**Examples:**
- Development: `matchhire_dev`
- Staging: `matchhire_staging`
- Production: `matchhire`

### Use Aliases

```python
"use_aliases": True
```

**Benefits:**
- Zero-downtime index updates
- Easy index switching
- Simplified index management

### Refresh Interval

```python
"refresh_interval": "1s"
```

**Recommendations:**
- Development: `1s`
- Production: `1s` or `30s` for bulk indexing
- Near real-time: `100ms`

### Number of Shards

```python
"number_of_shards": 3
```

**Guidelines:**
- Small datasets (< 10GB): 1-3 shards
- Medium datasets (10-100GB): 3-5 shards
- Large datasets (> 100GB): 5-10 shards
- Formula: `shards = max(1, data_size_gb / 20)`

### Number of Replicas

```python
"number_of_replicas": 1
```

**Guidelines:**
- Development: 0 replicas
- Production: 1-2 replicas
- High availability: 2-3 replicas

## Environment-Specific Configuration

### Development

```python
SEARCH_PROVIDER = "elasticsearch"

SEARCH_CONFIG = {
    "elasticsearch": {
        "hosts": ["http://localhost:9200"],
        "verify_certs": False,
        "request_timeout": 30,
        "max_retries": 1,
        "index_prefix": "matchhire_dev",
        "use_aliases": False,
        "number_of_shards": 1,
        "number_of_replicas": 0,
    }
}
```

### Staging

```python
SEARCH_PROVIDER = "elasticsearch"

SEARCH_CONFIG = {
    "elasticsearch": {
        "hosts": ["http://staging-es:9200"],
        "username": os.getenv("ES_USERNAME"),
        "password": os.getenv("ES_PASSWORD"),
        "verify_certs": True,
        "request_timeout": 30,
        "max_retries": 3,
        "index_prefix": "matchhire_staging",
        "use_aliases": True,
        "number_of_shards": 3,
        "number_of_replicas": 1,
    }
}
```

### Production

```python
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

### Elastic Cloud

```python
SEARCH_PROVIDER = "elasticsearch"

SEARCH_CONFIG = {
    "elasticsearch": {
        "cloud_id": os.getenv("ES_CLOUD_ID"),
        "api_key": os.getenv("ES_API_KEY"),
        "request_timeout": 30,
        "max_retries": 3,
        "index_prefix": "matchhire",
        "use_aliases": True,
        "number_of_shards": 3,
        "number_of_replicas": 1,
    }
}
```

## Environment Variables

Using environment variables for sensitive configuration:

```python
import os
from decouple import config

SEARCH_CONFIG = {
    "elasticsearch": {
        "hosts": config("ES_HOSTS", default="http://localhost:9200", cast=lambda x: x.split(",")),
        "username": config("ES_USERNAME", default=None),
        "password": config("ES_PASSWORD", default=None),
        "api_key": config("ES_API_KEY", default=None),
        "cloud_id": config("ES_CLOUD_ID", default=None),
        "verify_certs": config("ES_VERIFY_CERTS", default=True, cast=bool),
        "ca_certs": config("ES_CA_CERTS", default=None),
        "request_timeout": config("ES_REQUEST_TIMEOUT", default=30, cast=int),
        "max_retries": config("ES_MAX_RETRIES", default=3, cast=int),
        "index_prefix": config("ES_INDEX_PREFIX", default="matchhire"),
        "use_aliases": config("ES_USE_ALIASES", default=True, cast=bool),
        "number_of_shards": config("ES_NUMBER_OF_SHARDS", default=3, cast=int),
        "number_of_replicas": config("ES_NUMBER_OF_REPLICAS", default=1, cast=int),
    }
}
```

## Configuration Validation

The provider validates configuration during initialization:

1. **Connection Verification**: Pings the cluster
2. **Cluster Health**: Checks cluster status
3. **Index Creation**: Creates indices if they don't exist

If validation fails, the provider raises `ProviderUnavailable`.

## Switching Providers

Switch between PostgreSQL and Elasticsearch via configuration:

```python
# Use PostgreSQL
SEARCH_PROVIDER = "postgresql"

# Use Elasticsearch
SEARCH_PROVIDER = "elasticsearch"
```

No code changes required in services or business logic.

## Monitoring Configuration

Monitor the following metrics:

- Connection pool usage
- Request latency
- Retry rate
- Error rate
- Index refresh time
- Cluster health

## Troubleshooting

### Connection Refused

**Problem:** Cannot connect to Elasticsearch

**Solutions:**
1. Check Elasticsearch is running: `curl http://localhost:9200`
2. Verify host and port configuration
3. Check firewall rules
4. Verify SSL/TLS settings

### Authentication Failed

**Problem:** Authentication errors

**Solutions:**
1. Verify username and password
2. Check API key is valid
3. Verify cloud ID is correct
4. Check user permissions

### SSL Certificate Error

**Problem:** SSL certificate verification failed

**Solutions:**
1. Set `verify_certs: False` for development only
2. Provide correct CA certificate path
3. Check certificate validity
4. Update system certificates

### Timeout Errors

**Problem:** Requests timing out

**Solutions:**
1. Increase `request_timeout`
2. Check cluster health
3. Verify network connectivity
4. Check cluster load

### Index Creation Failed

**Problem:** Cannot create indices

**Solutions:**
1. Check user has `create_index` permission
2. Verify cluster has sufficient disk space
3. Check index settings are valid
4. Review cluster logs

## Best Practices

1. **Use environment variables** for sensitive configuration
2. **Separate configurations** per environment
3. **Enable SSL/TLS** in production
4. **Use connection pooling** for performance
5. **Configure appropriate timeouts** for your workload
6. **Monitor cluster health** regularly
7. **Use aliases** for zero-downtime deployments
8. **Set appropriate shard counts** based on data volume
9. **Enable compression** for large payloads
10. **Configure retries** for resilience
