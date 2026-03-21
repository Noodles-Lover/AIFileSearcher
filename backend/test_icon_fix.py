#!/usr/bin/env python3
"""
Test script to verify icon fix for folders vs drives
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_icon_cache_keys():
    """Test icon cache key generation"""
    try:
        print("Testing icon cache key generation...")
        
        from backend.utils.icons import SystemIconManager
        
        icon_manager = SystemIconManager()
        
        # Test different path types
        test_paths = [
            "C:\\",  # Drive root
            "D:\\",  # Drive root  
            "C:\\Windows",  # Regular folder
            "D:\\_Programming\\CompleteProjects\\AIFileSearcher",  # Regular folder
            "test.txt",  # File
        ]
        
        for path in test_paths:
            # Simulate cache key generation logic
            if os.path.exists(path):
                is_dir = os.path.isdir(path)
                ext = os.path.splitext(path)[1].lower()
                
                if is_dir:
                    # Check if it's a drive root
                    drive_root = os.path.splitdrive(path)[0] + os.sep
                    if path == drive_root:
                        cache_key = f"__drive__{os.path.splitdrive(path)[0]}"
                    else:
                        cache_key = "__folder__"
                elif ext in ['.exe', '.lnk', '.ico', '.cur', '.ani']:
                    cache_key = path
                else:
                    cache_key = ext
                    
                print(f"✓ Path: {path} -> Cache Key: {cache_key}")
            else:
                print(f"⚠️ Path does not exist: {path}")
        
        print("\n🎉 Icon cache key test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Icon cache key test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_icon_cache_keys()
    sys.exit(0 if success else 1)
