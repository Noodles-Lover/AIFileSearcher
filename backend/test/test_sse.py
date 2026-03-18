#!/usr/bin/env python3
"""
Test SSE streaming functionality
"""

import requests
import json
import time

def test_sse():
    """Test SSE streaming"""
    print("=" * 60)
    print("Test SSE Streaming")
    print("=" * 60)
    
    test_folder = "D:\\_Programming\\CompleteProjects\\AIFileSearcher\\testFiles\\small"
    
    try:
        print(f"Testing SSE to: {test_folder}")
        response = requests.post(
            "http://localhost:8000/api/index_folder",
            json={"path": test_folder},
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            print("Connected, monitoring real-time flow...")
            print("-" * 60)
            
            event_count = 0
            start_time = time.time()
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    event_count += 1
                    current_time = time.time()
                    elapsed = current_time - start_time
                    
                    try:
                        data = json.loads(line[6:])
                        status = data.get('status', 'unknown')
                        current = data.get('current', 0)
                        total = data.get('total', 0)
                        percent = data.get('percent', 0)
                        msg = data.get('msg', '')
                        file_name = data.get('file', '')
                        
                        print(f"[{elapsed:.1f}s] Event {event_count}: {status}")
                        if file_name:
                            print(f"    File: {file_name}")
                        print(f"    Progress: {current}/{total} ({percent}%)")
                        print(f"    Message: {msg}")
                        print("-" * 40)
                        
                        if status == 'complete':
                            print(f"✅ Total time: {elapsed:.1f}s, Events: {event_count}")
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"[{elapsed:.1f}s] ❌ JSON error: {e}")
                        
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_sse()
