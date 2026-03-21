#!/usr/bin/env python3
"""
Simple test for list API without Everything dependency
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_simple_list():
    """Test simple list functionality"""
    try:
        print("Testing simple file listing...")
        
        # Test the format functions directly
        from backend.api.search import format_size, format_time
        
        # Test format_size
        print(f"✓ format_size(1024): {format_size(1024)}")
        print(f"✓ format_size(1048576): {format_size(1048576)}")
        print(f"✓ format_size(0): {format_size(0)}")
        
        # Test format_time
        import time
        test_timestamp = time.time()
        print(f"✓ format_time({test_timestamp}): {format_time(test_timestamp)}")
        
        # Test os.listdir functionality
        test_path = "D:\\_Programming\\CompleteProjects\\AIFileSearcher\\testFiles"
        if os.path.exists(test_path):
            print(f"✓ Test path exists: {test_path}")
            
            files = []
            for item in os.listdir(test_path):
                item_path = os.path.join(test_path, item)
                if os.path.exists(item_path):
                    stat = os.stat(item_path)
                    is_dir = os.path.isdir(item_path)
                    
                    file_info = {
                        "name": item,
                        "path": item_path,
                        "size": "0 B" if is_dir else format_size(stat.st_size),
                        "size_bytes": 0 if is_dir else stat.st_size,
                        "modified": format_time(stat.st_mtime),
                        "type": "folder" if is_dir else "file"
                    }
                    files.append(file_info)
            
            print(f"✓ Found {len(files)} items in test directory:")
            for file_info in files[:5]:  # Show first 5
                print(f"  - {file_info['name']} ({file_info['type']}, {file_info['size']})")
                
        else:
            print(f"⚠️ Test path does not exist: {test_path}")
        
        print("\n🎉 Simple list test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Simple list test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_list()
    sys.exit(0 if success else 1)
