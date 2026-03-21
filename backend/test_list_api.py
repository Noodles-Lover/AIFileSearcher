#!/usr/bin/env python3
"""
Test script to verify list API works correctly
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_list_api():
    """Test list API endpoint"""
    try:
        print("Testing list API...")
        
        import requests
        
        # Test with a valid path
        test_path = "D:\\_Programming\\CompleteProjects\\AIFileSearcher\\testFiles"
        
        response = requests.get(f"http://localhost:8000/api/list?parent_path={test_path}")
        
        if response.status_code == 200:
            data = response.json()
            files = data.get('results', [])
            print(f"✓ List API returned {len(files)} files for path: {test_path}")
            
            for i, file in enumerate(files[:5]):  # Show first 5 files
                print(f"  [{i+1}] {file.get('name')} ({file.get('type')})")
            
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more files")
                
        else:
            print(f"❌ List API failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print("\n🎉 List API test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ List API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_list_api()
    sys.exit(0 if success else 1)
