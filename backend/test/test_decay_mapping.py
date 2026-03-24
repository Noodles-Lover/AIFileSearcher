#!/usr/bin/env python3
"""
Test different decay rates and their mapping to log_base
"""

import math

def calculate_dynamic_chunk_count(k: int, total_chunks: int) -> int:
    """Dynamic chunk count with simple logarithmic function"""
    if total_chunks <= 0:
        return 90
    
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

def test_decay_rate_mapping():
    """Test how different decay rates map to log_base"""
    print("Decay Rate to Log Base Mapping:")
    print("User Rate -> Log Base -> Description")
    print("-" * 40)
    
    for rate in range(1, 11):
        log_base = 1.25 + (rate - 1) * 0.30 / 9
        if rate == 1:
            desc = "Slowest decay (most extraction)"
        elif rate == 5:
            desc = "Default (balanced)"
        elif rate == 10:
            desc = "Fastest decay (least extraction)"
        else:
            desc = ""
        
        print(f"{rate:3d} -> {log_base:.3f} -> {desc}")
    
    print("-" * 40)

def test_different_decay_rates():
    """Test extraction with different decay rates"""
    total_chunks = 10000
    decay_rates = [1, 3, 5, 7, 10]
    
    print(f"\nExtraction Test (Total chunks: {total_chunks}):")
    print("Decay Rate -> Log Base -> Extract Count -> Extract Ratio")
    print("-" * 55)
    
    for rate in decay_rates:
        log_base = 1.25 + (rate - 1) * 0.30 / 9
        extract_count = calculate_dynamic_chunk_count(rate, total_chunks)
        ratio = extract_count / total_chunks
        
        print(f"{rate:3d} -> {log_base:.3f} -> {extract_count:3d} -> {ratio:6.2%}")
    
    print("-" * 55)

def test_monotonic_increase():
    """Verify strict monotonic increase across different decay rates"""
    print("\nMonotonic Increase Test (Decay Rate = 5):")
    print("Total Chunks -> Extract Count")
    print("-" * 30)
    
    prev_count = 0
    is_monotonic = True
    test_cases = [50, 100, 200, 500, 1000, 2000, 5000, 10000, 50000]
    
    for total in test_cases:
        count = calculate_dynamic_chunk_count(5, total)
        print(f"{total:6d} -> {count:3d}")
        
        if count < prev_count:
            is_monotonic = False
            print(f"Not monotonic at {total} (count: {count} < prev: {prev_count})")
        
        prev_count = count
    
    print("-" * 30)
    if is_monotonic:
        print("Strictly monotonically increasing!")
    else:
        print("Monotonicity violated!")

if __name__ == "__main__":
    print("Testing simple logarithmic decay algorithm...")
    
    test_decay_rate_mapping()
    test_different_decay_rates()
    test_monotonic_increase()
    
    print("\nAll tests completed!")
