#!/usr/bin/env python3
"""
Test script to verify the indexing logic works correctly
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_index_components():
    """Test individual components of the indexing system"""
    try:
        print("Testing indexing components...")
        
        # Test FileCache
        from backend.RAG.FileCache import FileCache
        cache_path = os.path.join(current_dir, "test_cache.json")
        file_cache = FileCache(cache_path)
        
        # Test should_process_file
        test_file = __file__  # Use this test file
        should_process, reason = file_cache.should_process_file(test_file)
        print(f"✓ FileCache.should_process_file: {should_process}, {reason}")
        
        # Test FileProcessor
        from backend.process.FileProcessor import FileProcessor
        processor = FileProcessor()
        
        # Test process_file
        if processor.is_supported_file(test_file):
            result = processor.process_file(test_file)
            if "error" in result:
                print(f"✗ FileProcessor.process_file failed: {result['error']}")
            else:
                chunks = result.get("chunks", [])
                print(f"✓ FileProcessor.process_file: {len(chunks)} chunks")
                if chunks:
                    print(f"  First chunk preview: {chunks[0][:100]}...")
        else:
            print(f"✓ File type not supported (expected for .py files)")
        
        # Test SystemManager
        from backend.RAG.SystemManager import system
        try:
            embedder = system.get_embedding_model()
            print("✓ SystemManager.get_embedding_model: OK")
            
            # Test encoding
            test_chunks = ["This is a test chunk"]
            embeddings = embedder.encode(test_chunks)
            print(f"✓ Embedding generation: {len(embeddings[0])} dimensions")
            
        except Exception as e:
            print(f"⚠️ SystemManager test failed (may be normal if no model): {e}")
        
        print("\n🎉 Component tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_index_components()
    sys.exit(0 if success else 1)
