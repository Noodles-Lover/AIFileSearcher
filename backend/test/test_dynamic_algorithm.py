#!/usr/bin/env python3
"""
Test script for dynamic chunk count algorithm
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Add parent directory to path for backend module
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def test_dynamic_algorithm():
    """Test dynamic algorithm performance with different data sizes"""
    try:
        from backend.api.search import calculate_dynamic_chunk_count
        
        k = 30
        test_cases = [50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000]
        
        print("Dynamic Chunk Count Algorithm Test:")
        print(f"Target files: {k}")
        print("Total Chunks -> Extract Count -> Extract Ratio -> Multiplier")
        print("-" * 60)
        
        for total in test_cases:
            chunk_count = calculate_dynamic_chunk_count(k, total)
            ratio = chunk_count / total
            multiplier = chunk_count / k
            print(f"{total:8d} -> {chunk_count:8d} -> {ratio:6.2%} -> {multiplier:4.1f}x")
        
        print("-" * 60)
        
        # Test edge cases
        print("\nEdge Cases Test:")
        edge_cases = [
            (0, "Empty database"),
            (10, "Very small data"),
            (60, "Exactly 2x files"),
            (1000, "Transition point"),
            (1000000, "Large data")
        ]
        
        for total, desc in edge_cases:
            chunk_count = calculate_dynamic_chunk_count(k, total)
            print(f"{desc:15s} ({total:8d} chunks): Extract {chunk_count} chunks")
        
        print("\nDynamic algorithm test completed!")
        return True
        
    except Exception as e:
        print(f"Dynamic algorithm test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_algorithm_parameters():
    """Test different parameter configurations"""
    try:
        print("\nParameter Sensitivity Test:")
        print("Test different min_ratio values (k=30, total=10000):")
        print("-" * 50)
        
        from backend.api.search import calculate_dynamic_chunk_count
        k = 30
        total = 10000
        
        # Current parameter result
        current_result = calculate_dynamic_chunk_count(k, total)
        print(f"Current parameters: Extract {current_result} chunks ({current_result/total:.2%})")
        
        print("\nParameter adjustment suggestions:")
        print("- For more accuracy: Increase max_multiplier (e.g., 6.0)")
        print("- For faster speed: Reduce min_ratio (e.g., 0.05)")
        print("- For earlier transition: Reduce transition_point (e.g., 500)")
        
        return True
        
    except Exception as e:
        print(f"Parameter test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing dynamic chunk count algorithm...")
    
    success1 = test_dynamic_algorithm()
    success2 = test_algorithm_parameters()
    
    if success1 and success2:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed!")
    
    sys.exit(0 if (success1 and success2) else 1)
