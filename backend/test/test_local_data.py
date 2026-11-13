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
        state_path = get_data_path("index_state.json")

        print(f"✓ Index path: {index_path}")
        print(f"✓ State path: {state_path}")

        # Verify paths use local_data
        assert "local_data" in index_path, f"Index path should use local_data: {index_path}"
        assert "local_data" in state_path, f"State path should use local_data: {state_path}"

        # Test SystemManager
        from backend.RAG.SystemManager import SystemManager

        sm = SystemManager.get_instance()
        embedder = sm.get_embedding_model()
        store = sm.get_vector_store()

        print("✓ SystemManager initialized successfully with local_data paths")

        # Test FileCache
        file_cache = sm.get_file_cache()
        print("✓ FileCache initialized successfully")
        
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
