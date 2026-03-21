#!/usr/bin/env python3
"""
Simple test script to verify backend imports work correctly
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_imports():
    """Test if all modules can be imported without errors"""
    try:
        print("Testing basic imports...")
        
        # Test path utils
        from backend.utils.path_utils import get_project_root, get_models_path, get_data_path
        print("✓ path_utils imported successfully")
        
        # Test core modules
        from backend.RAG.SystemManager import SystemManager
        print("✓ SystemManager imported successfully")
        
        from backend.RAG.EmbeddingModel import EmbeddingModel
        print("✓ EmbeddingModel imported successfully")
        
        from backend.RAG.VectorStore import VectorStore
        print("✓ VectorStore imported successfully")
        
        # Test API modules
        from api.server import app
        print("✓ FastAPI app imported successfully")
        
        print("\n🎉 All imports successful!")
        print("Backend should start without issues.")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
