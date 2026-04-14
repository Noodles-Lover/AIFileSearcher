#!/usr/bin/env python3
"""
Test script to verify search results contain content field
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_search_content():
    """Test if search results contain content field"""
    try:
        print("Testing search content field...")
        
        from backend.RAG.SystemManager import SystemManager

        sm = SystemManager.get_instance()
        embedder = sm.get_embedding_model()
        store = sm.get_vector_store()
        
        if not store or store.index.ntotal == 0:
            print("⚠️ No vectors in database, adding test data...")
            
            # Add test data
            test_vectors = [[0.1] * 1024, [0.2] * 1024]
            test_metas = [
                {
                    'file_path': 'test1.txt',
                    'file_name': 'test1.txt',
                    'chunk_index': 0,
                    'chunk_text': 'This is a test chunk about artificial intelligence',
                    'total_chunks': 1
                },
                {
                    'file_path': 'test2.txt',
                    'file_name': 'test2.txt',
                    'chunk_index': 0,
                    'chunk_text': 'This is another test about machine learning',
                    'total_chunks': 1
                }
            ]
            
            store.add(test_vectors, test_metas, "test_file")
            store.save()
            print("✓ Test data added")
        
        # Test search
        query = "artificial intelligence"
        query_vector = embedder.encode(query)[0]
        results = store.search(query_vector, k=5)
        
        print(f"\n🔍 Search results for '{query}':")
        for i, result in enumerate(results):
            print(f"[{i+1}] File: {result.get('file_path')}")
            print(f"    Score: {result.get('score')}")
            print(f"    chunk_text: {result.get('chunk_text', 'MISSING')}")
            print(f"    content: {result.get('content', 'MISSING')}")
            print(f"    Has content field: {'content' in result}")
            print("-" * 40)
        
        # Test API endpoint
        print("\n🌐 Testing API endpoint...")
        import requests
        response = requests.get(f"http://localhost:8000/api/vector_search?q={query}&k=5")
        
        if response.status_code == 200:
            api_results = response.json().get('results', [])
            print(f"API returned {len(api_results)} results")
            
            for i, result in enumerate(api_results[:2]):
                print(f"[{i+1}] File: {result.get('file_path')}")
                print(f"    content: {result.get('content', 'MISSING')[:50]}...")
                print(f"    Has content_preview: {bool(result.get('content'))}")
                print("-" * 40)
        else:
            print(f"❌ API request failed: {response.status_code}")
        
        print("\n🎉 Search content test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Search content test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_search_content()
    sys.exit(0 if success else 1)
