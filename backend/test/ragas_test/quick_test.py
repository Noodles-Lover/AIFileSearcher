"""
RAG Retrieval Evaluation Script - Using ragas

Evaluates retrieval quality (without LLM answer generation)
"""
import sys
import os
import time

# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)
os.chdir(project_root)

from backend.utils.path_utils import ensure_project_path, get_data_path
ensure_project_path()

from backend.RAG.SystemManager import SystemManager
from backend.RAG.VectorStore import VectorStore
from backend.utils.IndexedFoldersManager import folders_manager
import numpy as np

# Test files path
TEST_FILES_DIR = os.path.join(project_root, "testFiles", "txt")


def clear_index_files():
    """Clear index files"""
    index_path = get_data_path("faiss_index.bin")
    metadata_path = get_data_path("metadata.json")
    cache_path = get_data_path("file_cache.json")
    info_path = get_data_path("faiss_index.info")
    
    files_deleted = []
    
    for path, name in [(index_path, "faiss_index.bin"), 
                       (metadata_path, "metadata.json"),
                       (cache_path, "file_cache.json"),
                       (info_path, "faiss_index.info")]:
        if os.path.exists(path):
            try:
                os.remove(path)
                files_deleted.append(name)
                print(f"  Deleted: {name}")
            except Exception as e:
                print(f"  Failed to delete {name}: {e}")
    
    folders_manager.clear()
    
    return files_deleted


def setup_test_index():
    """Setup test index"""
    print("=" * 60)
    print("Step 1: Clear existing index")
    print("=" * 60)
    
    # Clear files FIRST, before creating VectorStore
    files_deleted = clear_index_files()
    print(f"Total deleted: {len(files_deleted)} files")
    
    # Small delay to ensure file system sync
    time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("Step 2: Initialize new index")
    print("=" * 60)
    
    SystemManager.reset_instance()
    sm = SystemManager.get_instance()
    
    # Get embedding dimension
    embedder = sm.get_embedding_model()
    dimension = embedder.model.get_sentence_embedding_dimension()
    print(f"Embedding dimension: {dimension}")
    
    # Get paths for new VectorStore
    index_path = get_data_path("faiss_index.bin")
    metadata_path = get_data_path("metadata.json")
    
    # Create new VectorStore with correct dimension
    store = VectorStore(
        dimension=dimension,
        index_path=index_path,
        metadata_path=metadata_path
    )
    sm._vector_store = store
    
    print(f"VectorStore dimension: {store.dimension}")
    print(f"Index type: {type(store.index).__name__}")
    print(f"Initial vectors: {store.index.ntotal}")
    
    return sm, store


def get_test_files():
    """Get test files from testFiles/txt directory"""
    test_files = []
    categories = {}
    
    for filename in os.listdir(TEST_FILES_DIR):
        if filename.endswith('.txt'):
            file_path = os.path.join(TEST_FILES_DIR, filename)
            # Extract category from filename (before _)
            parts = filename.split('_')
            if len(parts) >= 1:
                category = parts[0]
                if category not in categories:
                    categories[category] = []
                categories[category].append(filename)
                test_files.append(file_path)
    
    return test_files, categories


def index_test_files(sm, store):
    """Index test files"""
    print("\n" + "=" * 60)
    print("Step 3: Index test files")
    print("=" * 60)
    
    embedder = sm.get_embedding_model()
    print(f"Embedding model: {type(embedder.model).__name__}")
    
    test_files, categories = get_test_files()
    print(f"Test files directory: {TEST_FILES_DIR}")
    print(f"Categories found: {list(categories.keys())}")
    print(f"Total files: {len(test_files)}")
    
    vectors = []
    metadata = []
    
    for i, file_path in enumerate(test_files):
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            vector = embedder.encode([content])[0]
            vectors.append(vector)
            
            # Extract category from filename
            filename = os.path.basename(file_path)
            category = filename.split('_')[0] if '_' in filename else 'unknown'
            
            metadata.append({
                "file_path": file_path,
                "file_name": filename,
                "content": content[:200],
                "category": category
            })
            
            print(f"  [{i+1}/{len(test_files)}] {filename} - dim: {len(vector)}")
        else:
            print(f"  [{i+1}/{len(test_files)}] MISSING: {file_path}")
    
    if vectors:
        vectors_array = np.array(vectors).astype('float32')
        store.add(vectors_array, metadata)
        print(f"\nIndexing completed: {store.index.ntotal} vectors")
    else:
        print("\nNo files were indexed!")
    
    return store


def test_retrieval(store):
    """Test retrieval"""
    print("\n" + "=" * 60)
    print("Step 4: Test retrieval")
    print("=" * 60)
    
    if store.index.ntotal == 0:
        print("No vectors in index! Skipping retrieval test.")
        return
    
    embedder = SystemManager.get_instance().get_embedding_model()
    
    queries = [
        ("健康管理", "健康医疗相关"),
        ("理财投资", "财务管理相关"),
        ("旅行计划", "生活记录相关"),
    ]
    
    for query, description in queries:
        print(f"\nQuery [{description}]: {query}")
        vector = embedder.encode([query])[0]
        results = store.search(vector, k=3)
        
        for i, r in enumerate(results):
            filename = r.get('file_name', 'unknown')
            category = r.get('category', 'unknown')
            print(f"  {i+1}. [{category}] {filename} (score: {r['score']:.4f})")


if __name__ == "__main__":
    sm, store = setup_test_index()
    store = index_test_files(sm, store)
    test_retrieval(store)
