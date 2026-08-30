from django.http import JsonResponse
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import redis


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    health_status = {
        'status': 'ok',
        'dependencies': {}
    }
    
    # Check PostgreSQL connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health_status['dependencies']['database'] = 'ok'
    except Exception as e:
        health_status['status'] = 'error'
        health_status['dependencies']['database'] = 'error'
    
    # Check Redis connectivity
    try:
        from config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, socket_connect_timeout=2)
        r.ping()
        health_status['dependencies']['redis'] = 'ok'
    except Exception as e:
        health_status['status'] = 'error'
        health_status['dependencies']['redis'] = 'error'
    
    return JsonResponse(health_status)
