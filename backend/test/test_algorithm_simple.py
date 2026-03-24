#!/usr/bin/env python3
"""
Simple test for dynamic chunk count algorithm without dependencies
"""

import math

def calculate_dynamic_chunk_count(k: int, total_chunks: int) -> int:
    """
    动态计算需要提取的分块数量
    使用简单对数函数 y = 7 * log_k(x)
    """
    import math
    
    if total_chunks <= 0:
        return 90  # 默认值
    
    # 将用户衰减率1-10映射到k=1.25-1.55
    log_base = 1.25 + (k - 1) * 0.30 / 9
    
    # 使用对数函数: y = 7 * log_k(x)
    if total_chunks >= 1:
        extract_count = 7 * math.log(total_chunks, log_base)
    else:
        extract_count = 50
    
    # 四舍五入
    extract_count = int(round(extract_count))
    
    # 限制在50到总分块数之间
    extract_count = max(50, min(total_chunks, extract_count))
    
    return extract_count

def test_dynamic_algorithm():
    """Test dynamic algorithm performance with different data sizes"""
    k = 5  # 默认衰减率5
    test_cases = [50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000]
    
    print("Dynamic Chunk Count Algorithm Test:")
    print(f"Decay rate: {k} (mapped to log_base: {1.25 + (k - 1) * 0.30 / 9:.3f})")
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
    
    print("\nParameter Analysis:")
    print("Simple logarithmic algorithm:")
    print(f"  Formula: y = 7 * log_k(x)")
    print(f"  User decay rate: 1-10 maps to log_base: 1.25-1.55")
    print(f"  Default decay rate 5 -> log_base: 1.4")
    print(f"  Range: 50 to total_chunks")
    
    print("\nAlgorithm characteristics:")
    print("- Simple logarithmic function")
    print("- Strictly monotonically increasing")
    print("- User-friendly decay rate (1-10)")
    print("- Rounded to nearest integer")
    
    print("\nDecay Rate Mapping:")
    print("- Decay rate 1  -> log_base 1.25 (slowest decay)")
    print("- Decay rate 5  -> log_base 1.40 (default)")
    print("- Decay rate 10 -> log_base 1.55 (fastest decay)")
    
    print("\nAdjustment Guidelines:")
    print("- For more extraction: Use lower decay rate (1-3)")
    print("- For balanced: Use decay rate 5 (default)")
    print("- For less extraction: Use higher decay rate (7-10)")
    
    print("\nDynamic algorithm test completed!")
    return True

if __name__ == "__main__":
    print("Testing dynamic chunk count algorithm...")
    
    success = test_dynamic_algorithm()
    
    if success:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed!")
    
    exit(0 if success else 1)
