#!/usr/bin/env python3
"""
Test script to verify file merging functionality
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_file_merge():
    """Test file merging logic"""
    try:
        print("Testing file merge functionality...")
        
        from backend.api.search import merge_chunks_by_file
        
        # 模拟搜索结果 (同一文件的多个分块)
        mock_chunks = [
            {
                'file_path': 'file1.txt',
                'chunk_text': 'This is chunk 1 with good content about AI',
                'score': 0.6,
                'chunk_index': 0
            },
            {
                'file_path': 'file2.txt', 
                'chunk_text': 'This is chunk 1 about machine learning',
                'score': 0.59,
                'chunk_index': 0
            },
            {
                'file_path': 'file1.txt',
                'chunk_text': 'This is chunk 2 with less relevant content',
                'score': 0.5,
                'chunk_index': 1
            },
            {
                'file_path': 'file2.txt',
                'chunk_text': 'This is chunk 2 about deep learning',
                'score': 0.57,
                'chunk_index': 1
            },
            {
                'file_path': 'file3.txt',
                'chunk_text': 'Content about neural networks',
                'score': 0.4,
                'chunk_index': 0
            }
        ]
        
        print("原始分块结果:")
        for i, chunk in enumerate(mock_chunks):
            print(f"  [{i+1}] {chunk['file_path']} (chunk {chunk['chunk_index']}) - score: {chunk['score']}")
        
        # 执行合并
        merged_results = merge_chunks_by_file(mock_chunks)
        
        print(f"\n合并后的文件结果 (共 {len(merged_results)} 个文件):")
        for i, result in enumerate(merged_results):
            print(f"  [{i+1}] {result['file_path']} - score: {result['score']} ({result['chunk_count']} 个分块)")
            print(f"      Content: {result['chunk_text'][:50]}...")
        
        # 验证排序正确性
        expected_order = ['file1.txt', 'file2.txt', 'file3.txt']  # 按最佳分块分数排序
        actual_order = [r['file_path'] for r in merged_results]
        
        if actual_order == expected_order:
            print("\n✅ 文件排序正确!")
        else:
            print(f"\n❌ 文件排序错误! 期望: {expected_order}, 实际: {actual_order}")
        
        # 验证每个文件只出现一次
        file_paths = [r['file_path'] for r in merged_results]
        if len(file_paths) == len(set(file_paths)):
            print("✅ 每个文件只出现一次!")
        else:
            print("❌ 有文件重复出现!")
        
        # 验证最佳分块选择
        file1_result = next(r for r in merged_results if r['file_path'] == 'file1.txt')
        if file1_result['score'] == 0.5:  # 应该选择最佳分块的分数
            print("✅ 正确选择了文件的最佳分块!")
        else:
            print(f"❌ 最佳分块选择错误! 期望: 0.5, 实际: {file1_result['score']}")
        
        print("\n🎉 文件合并测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 文件合并测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_file_merge()
    sys.exit(0 if success else 1)
