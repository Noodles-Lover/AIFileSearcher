#!/usr/bin/env python3
"""
Test script to verify API routes are working correctly
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_routes():
    """Test if all routes are properly configured"""
    try:
        from api.server import app
        
        print("Testing API routes...")
        
        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        print("\n📋 Available routes:")
        for route in sorted(routes):
            print(f"  - {route}")
        
        # Check for specific routes
        required_routes = [
            "/api/index_folder",
            "/api/clear_cache", 
            "/api/clear_index",
            "/api/search",
            "/api/list",
            "/api/vector_search",
            "/api/icon",
            "/api/preview"
        ]
        
        print("\n✅ Checking required routes:")
        missing_routes = []
        for required_route in required_routes:
            if required_route in routes:
                print(f"  ✓ {required_route}")
            else:
                print(f"  ❌ {required_route} - MISSING")
                missing_routes.append(required_route)
        
        if missing_routes:
            print(f"\n❌ Missing routes: {missing_routes}")
            return False
        else:
            print("\n🎉 All required routes are available!")
            return True
            
    except Exception as e:
        print(f"❌ Error testing routes: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_routes()
    sys.exit(0 if success else 1)
