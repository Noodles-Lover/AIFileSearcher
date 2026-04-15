"""评估结果导出模块"""

import os
import json
from datetime import datetime


class EvalReporter:
    """评估结果导出器"""

    def __init__(self, result_dir: str = None):
        if result_dir is None:
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            result_dir = os.path.join(backend_dir, "test", "ragas_test", "result")
        
        self.base_result_dir = result_dir
        os.makedirs(result_dir, exist_ok=True)

    def _get_type_dir(self, test_type: str) -> str:
        """获取指定类型的子目录"""
        type_dir = os.path.join(self.base_result_dir, test_type)
        os.makedirs(type_dir, exist_ok=True)
        return type_dir

    def _get_next_seq(self, base_name: str, type_dir: str) -> int:
        """获取下一个序号（检查指定类型目录）"""
        existing = []
        for f in os.listdir(type_dir):
            if f.startswith(base_name):
                # 匹配 base_name-X.json 或 base_name-X.txt
                try:
                    # 去掉前缀和后缀，获取序号
                    rest = f[len(base_name)+1:]
                    seq = int(rest.replace(".json", "").replace(".txt", ""))
                    existing.append(seq)
                except ValueError:
                    continue
        
        next_seq = 1
        if existing:
            next_seq = max(existing) + 1
        
        return next_seq

    def export(self, 
               test_type: str,
               embedding_model: str,
               index_type: str,
               chunking_name: str,
               metrics: dict,
               performance: dict,
               config: dict = None) -> tuple:
        """
        导出评估结果到 JSON 文件
        
        Returns:
            tuple: (filepath, seq) 导出文件的完整路径和序号
        """
        type_dir = self._get_type_dir(test_type)
        base_name = f"{embedding_model}-{index_type}-{chunking_name}"
        seq = self._get_next_seq(base_name, type_dir)
        filename = f"{base_name}-{seq}.json"
        filepath = os.path.join(type_dir, filename)

        result = {
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "test_type": test_type,
                "embedding_model": embedding_model,
                "index_type": index_type,
                "chunking_strategy": chunking_name,
            },
            "config": config or {},
            "metrics": metrics,
            "performance": performance
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return filepath, seq

    def export_text(self,
                    test_type: str,
                    embedding_model: str,
                    index_type: str,
                    chunking_name: str,
                    metrics: dict,
                    performance: dict,
                    seq: int = None,
                    query_results: list = None) -> str:
        """
        导出评估结果到文本文件
        
        Returns:
            str: 导出文件的完整路径
        """
        type_dir = self._get_type_dir(test_type)
        base_name = f"{embedding_model}-{index_type}-{chunking_name}"
        if seq is None:
            seq = self._get_next_seq(base_name, type_dir)
        filename = f"{base_name}-{seq}.txt"
        filepath = os.path.join(type_dir, filename)

        memory = performance.get('memory', {})
        perf_stats = performance.get('stats', {})

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("EVALUATION METRICS\n")
            f.write("=" * 60 + "\n")
            f.write(f"Total queries:       {metrics.get('total', 0)}\n")
            f.write(f"Hits (top-3):        {metrics.get('hits', 0)}/{metrics.get('total', 0)}\n")
            f.write(f"Precision@1:        {metrics.get('precision_at_1', 0):.4f}\n")
            f.write(f"Precision@3:        {metrics.get('precision_at_3', 0):.4f}\n")
            f.write(f"MRR:                {metrics.get('mrr', 0):.4f}\n")
            f.write(f"Hit Rate@3:         {metrics.get('hit_rate_at_3', 0):.4f}\n")
            f.write("\n")
            f.write("Retrieval Time (Total):\n")
            f.write(f"  Encode:          {metrics.get('total_encode_time', 0)*1000:.2f}ms\n")
            f.write(f"  Search:          {metrics.get('total_search_time', 0)*1000:.2f}ms\n")
            f.write(f"  Total:           {metrics.get('total_retrieval_time', 0)*1000:.2f}ms\n")
            f.write("\n")
            f.write("Retrieval Time (Avg):\n")
            f.write(f"  Encode:          {metrics.get('avg_encode_time', 0)*1000:.2f}ms\n")
            f.write(f"  Search:          {metrics.get('avg_search_time', 0)*1000:.2f}ms\n")
            f.write(f"  Total:           {metrics.get('avg_retrieval_time', 0)*1000:.2f}ms\n")
            f.write("\n")
            f.write("=" * 60 + "\n")
            f.write("PERFORMANCE STATISTICS\n")
            f.write("=" * 60 + "\n")
            
            # 从顶层 meta 参数获取模型信息（与 JSON 导出保持一致）
            f.write(f"\n【Index Config】\n")
            f.write(f"  Index Type: {index_type}\n")
            f.write(f"  Chunking Strategy: {chunking_name}\n")
            
            f.write(f"\n【Index Stats】\n")
            f.write(f"  Files Processed: {perf_stats.get('file_count', 0)}\n")
            f.write(f"  Total Chunks: {perf_stats.get('total_chunks', 0)}\n")
            f.write(f"  Index Vectors: {perf_stats.get('vector_count', 0)}\n")
            
            f.write(f"\n【Time Stats】\n")
            f.write(f"  Total Chunking Time: {perf_stats.get('chunk_time', 0):.3f}s\n")
            f.write(f"  Total Vectorization Time: {perf_stats.get('vector_time', 0):.3f}s\n")
            
            if perf_stats.get('file_count', 0) > 0:
                f.write(f"\n【Average Times】\n")
                f.write(f"  Per File Chunking: {perf_stats.get('avg_chunk_per_file', 0):.1f}ms\n")
                f.write(f"  Per File Vectorization: {perf_stats.get('avg_vector_per_file', 0):.1f}ms\n")
            
            if perf_stats.get('total_chunks', 0) > 0:
                f.write(f"  Per Chunk Vectorization: {perf_stats.get('avg_vector_per_chunk', 0):.2f}ms\n")

        return filepath
