#!/usr/bin/env python3
"""
Test script to verify local_data directory is working correctly
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_local_data_paths():
    """Test that all paths use local_data directory"""
    try:
        print("Testing local_data directory paths...")
        
        from backend.utils.path_utils import get_data_path
        
        # Test get_data_path function
        index_path = get_data_path("faiss_index.bin")
        metadata_path = get_data_path("metadata.json")
        cache_path = get_data_path("file_cache.json")
        
        print(f"✓ Index path: {index_path}")
        print(f"✓ Metadata path: {metadata_path}")
        print(f"✓ Cache path: {cache_path}")
        
        # Verify paths use local_data
        assert "local_data" in index_path, f"Index path should use local_data: {index_path}"
        assert "local_data" in metadata_path, f"Metadata path should use local_data: {metadata_path}"
        assert "local_data" in cache_path, f"Cache path should use local_data: {cache_path}"
        
        # Verify files exist
        assert os.path.exists(index_path), f"Index file should exist: {index_path}"
        assert os.path.exists(metadata_path), f"Metadata file should exist: {metadata_path}"
        assert os.path.exists(cache_path), f"Cache file should exist: {cache_path}"
        
        print("✓ All files exist in local_data directory")
        
        # Test SystemManager
        from backend.RAG.SystemManager import system
        
        embedder = system.get_embedding_model()
        store = system.get_vector_store()
        
        print("✓ SystemManager initialized successfully with local_data paths")
        
        # Test FileCache
        from backend.RAG.FileCache import FileCache
        file_cache = FileCache(cache_path)
        print("✓ FileCache initialized successfully with local_data path")
        
        print("\n🎉 local_data directory test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ local_data directory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_local_data_paths()
    sys.exit(0 if success else 1)
