#!/usr/bin/env python3
"""
Test script to verify VectorStore methods work correctly
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_vectorstore():
    """Test VectorStore methods"""
    try:
        print("Testing VectorStore...")
        
        from backend.RAG.VectorStore import VectorStore
        import tempfile
        
        # Create temporary files for testing
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as index_file, \
             tempfile.NamedTemporaryFile(suffix='.json', delete=False) as meta_file:
            
            # Initialize VectorStore
            store = VectorStore(dimension=1024, index_path=index_file.name, metadata_path=meta_file.name)
            print("✓ VectorStore initialized")
            
            # Test add method
            test_vectors = [[0.1] * 1024, [0.2] * 1024]  # 2 test vectors
            test_metas = [
                {'file_path': 'test1.txt', 'chunk_index': 0, 'chunk_text': 'test chunk 1'},
                {'file_path': 'test2.txt', 'chunk_index': 0, 'chunk_text': 'test chunk 2'}
            ]
            
            added_count = store.add(test_vectors, test_metas, "test_file")
            print(f"✓ VectorStore.add: {added_count} vectors added")
            
            # Test save method
            store.save()
            print("✓ VectorStore.save: OK")
            
            # Test load method
            new_store = VectorStore(dimension=1024, index_path=index_file.name, metadata_path=meta_file.name)
            print(f"✓ VectorStore.load: {len(new_store.metadata)} metadata entries loaded")
            
            # Clean up
            os.unlink(index_file.name)
            os.unlink(meta_file.name)
        
        print("\n🎉 VectorStore tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ VectorStore test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_vectorstore()
    sys.exit(0 if success else 1)
