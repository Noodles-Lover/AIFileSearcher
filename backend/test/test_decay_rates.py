#!/usr/bin/env python3
"""
Test different decay rate parameters
"""

import math

def calculate_dynamic_chunk_count(k: int, total_chunks: int) -> int:
    """Dynamic chunk count with decay rate"""
    if total_chunks <= 0:
        return 90
    
    base = 100
    log_x = math.log10(max(1, total_chunks))
    decay_factor = 1 + (k * log_x) / 100
    extract_count = int(base * log_x / decay_factor)
    
    min_count = 60
    max_count = total_chunks
    extract_count = max(min_count, min(max_count, extract_count))
    
    return extract_count

def test_different_k_values():
    """Test algorithm with different k values"""
    total_chunks = 10000
    k_values = [10, 20, 30, 40, 50, 100]
    
    print("Decay Rate Parameter Test:")
    print(f"Total chunks: {total_chunks}")
    print("k value -> Extract count -> Extract ratio")
    print("-" * 45)
    
    for k in k_values:
        extract_count = calculate_dynamic_chunk_count(k, total_chunks)
        ratio = extract_count / total_chunks
        print(f"{k:3d} -> {extract_count:3d} -> {ratio:6.2%}")
    
    print("-" * 45)
    print("\nObservations:")
    print("- Higher k = faster decay = less extraction")
    print("- Lower k = slower decay = more extraction")
    print("- All values maintain monotonic increase")

def test_monotonic_increase():
    """Verify strict monotonic increase"""
    k = 30
    test_cases = [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]
    
    print("\nMonotonic Increase Test:")
    print("Total chunks -> Extract count")
    print("-" * 30)
    
    prev_count = 0
    is_monotonic = True
    
    for total in test_cases:
        count = calculate_dynamic_chunk_count(k, total)
        print(f"{total:6d} -> {count:3d}")
        
        if count <= prev_count:
            is_monotonic = False
            print(f"Not monotonic at {total} (count: {count} <= prev: {prev_count})")
        
        prev_count = count
    
    print("-" * 30)
    if is_monotonic:
        print("Strictly monotonically increasing!")
    else:
        print("Monotonicity violated!")

if __name__ == "__main__":
    print("Testing decay rate algorithm...")
    
    test_different_k_values()
    test_monotonic_increase()
    
    print("\nAll tests completed!")
