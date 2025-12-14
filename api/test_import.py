#!/usr/bin/env python3

# Test script to check imports step by step
import traceback

def test_import(name, import_func):
    try:
        print(f"Testing {name}...")
        import_func()
        print(f"✅ {name} successful")
        return True
    except Exception as e:
        print(f"❌ {name} failed: {e}")
        traceback.print_exc()
        return False

# Test each import individually
test_import("BaseRepository", lambda: __import__('services.infrastructure.database.base_repository', fromlist=['BaseRepository']))
test_import("DatabaseService direct", lambda: __import__('services.infrastructure.database.database_service', fromlist=['DatabaseService']))
test_import("RedisService", lambda: __import__('services.infrastructure.redis_service', fromlist=['RedisService']))
test_import("SimpleCache", lambda: __import__('services.infrastructure.cache', fromlist=['SimpleCache']))
test_import("cache_decorator", lambda: __import__('services.infrastructure.cache_decorator', fromlist=['cache_decorator']))
test_import("encryption_service", lambda: __import__('services.infrastructure.encryption', fromlist=['encryption_service']))
test_import("MonitoringService", lambda: __import__('services.infrastructure.monitoring', fromlist=['MonitoringService']))

print("\nTesting full infrastructure import...")
test_import("Infrastructure __init__", lambda: __import__('services.infrastructure', fromlist=['DatabaseService']))