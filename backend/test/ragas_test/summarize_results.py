# -*- coding: utf-8 -*-
"""
评估结果汇总脚本

功能：
1. 遍历指定测试类型目录下的所有 JSON 结果文件
2. 按配置（embedding_model-index_type-chunking_name）分组
3. 计算各指标的均值和标准差
4. 生成汇总报告
"""

import os
import sys
import io
import json
import argparse
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import statistics

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)


def parse_filename(filename: str) -> Tuple[str, int]:
    """
    解析文件名，返回 (base_name, seq)
    例如: bge-m3-IndexFlatL2-Paragraph(lines=5)-1.json -> ("bge-m3-IndexFlatL2-Paragraph(lines=5)", 1)
    """
    if not filename.endswith('.json'):
        return None, None
    
    # 去掉 .json 后缀
    name_without_ext = filename[:-5]
    
    # 查找最后一个 -序号 模式
    parts = name_without_ext.rsplit('-', 1)
    if len(parts) == 2:
        base_name, seq_str = parts
        try:
            seq = int(seq_str)
            return base_name, seq
        except ValueError:
            # 如果最后一部分不是数字，整个作为 base_name
            return name_without_ext, 1
    
    return name_without_ext, 1


def load_json_result(filepath: str) -> dict:
    """加载单个 JSON 结果文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def average_numbers(numbers: List[float]) -> Tuple[float, float]:
    """计算均值和标准差"""
    if not numbers:
        return 0.0, 0.0
    if len(numbers) == 1:
        return numbers[0], 0.0
    avg = statistics.mean(numbers)
    stdev = statistics.stdev(numbers)
    return avg, stdev


def aggregate_results(results: List[dict]) -> dict:
    """
    聚合多个结果，计算均值和标准差
    """
    if not results:
        return {}
    
    aggregated = {}
    
    # 提取所有 metrics
    all_metrics = [r.get('metrics', {}) for r in results]
    
    # 需要聚合的 metrics 字段
    metric_fields = [
        'precision_at_1', 'precision_at_3', 'mrr', 'hit_rate_at_3',
        'total', 'hits',
        'total_encode_time', 'total_search_time', 'total_retrieval_time',
        'avg_encode_time', 'avg_search_time', 'avg_retrieval_time',
    ]
    
    # 聚合 metrics
    aggregated_metrics = {}
    for field in metric_fields:
        values = [m.get(field, 0) for m in all_metrics if isinstance(m.get(field), (int, float))]
        if values:
            avg, stdev = average_numbers(values)
            aggregated_metrics[field] = {'avg': avg, 'stdev': stdev, 'count': len(values)}
    aggregated['metrics'] = aggregated_metrics
    
    # 提取 performance.stats
    all_stats = [r.get('performance', {}).get('stats', {}) for r in results]
    
    perf_fields = [
        'file_count', 'total_chunks', 'vector_count',
        'chunk_time', 'vector_time',
    ]
    
    aggregated_perf = {}
    for field in perf_fields:
        values = [s.get(field, 0) for s in all_stats if isinstance(s.get(field), (int, float))]
        if values:
            avg, stdev = average_numbers(values)
            aggregated_perf[field] = {'avg': avg, 'stdev': stdev, 'count': len(values)}
    aggregated['performance'] = {'stats': aggregated_perf}
    
    # 提取 memory（取平均值）
    all_memory = [r.get('performance', {}).get('memory', {}) for r in results]
    if all_memory and any(all_memory):
        memory_avg = {}
        for field in ['after_load_mb', 'peak_mb']:
            values = [m.get(field, 0) for m in all_memory if isinstance(m.get(field), (int, float))]
            if values:
                avg, stdev = average_numbers(values)
                memory_avg[field] = {'avg': avg, 'stdev': stdev}
        if memory_avg:
            aggregated['performance']['memory'] = memory_avg
    
    # 提取 meta（取第一个非空值，因为同一配置应该相同）
    all_meta = [r.get('performance', {}).get('meta', {}) for r in results]
    if all_meta and any(all_meta):
        meta_avg = {}
        for field in ['model_size', 'index_size', 'model_load_time', 'embedding_model']:
            values = [m.get(field) for m in all_meta if m.get(field)]
            if values:
                # 这些值通常相同，取第一个
                meta_avg[field] = values[0]
        if meta_avg:
            aggregated['performance']['meta'] = meta_avg
    
    aggregated['count'] = len(results)
    
    return aggregated


def summarize_test_type(type_dir: str, test_type: str) -> Dict[str, dict]:
    """
    汇总指定测试类型目录下的所有结果
    返回: {base_name: aggregated_result}
    """
    if not os.path.exists(type_dir):
        print(f"Directory not found: {type_dir}")
        return {}
    
    # 按 base_name 分组
    groups = defaultdict(list)
    
    # 排除汇总文件本身
    exclude_patterns = [f"{test_type}_summary.json", "summary.json"]
    
    for filename in os.listdir(type_dir):
        if not filename.endswith('.json'):
            continue
        
        # 排除汇总文件
        if filename in exclude_patterns:
            continue
        
        base_name, seq = parse_filename(filename)
        if base_name is None:
            continue
        
        filepath = os.path.join(type_dir, filename)
        try:
            result = load_json_result(filepath)
            groups[base_name].append(result)
        except Exception as e:
            print(f"Warning: Failed to load {filename}: {e}")
    
    # 聚合每个组
    summarized = {}
    for base_name, results in groups.items():
        summarized[base_name] = aggregate_results(results)
    
    return summarized


def generate_markdown_table(summarized: Dict[str, dict], test_type: str) -> str:
    """生成 Markdown 格式的汇总表格"""
    lines = []
    lines.append(f"# {test_type.upper()} 测试结果汇总")
    lines.append("")
    
    # 按 P@1 排序
    sorted_items = sorted(
        summarized.items(),
        key=lambda x: x[1].get('metrics', {}).get('precision_at_1', {}).get('avg', 0),
        reverse=True
    )
    
    # 检索指标表格
    headers = ["配置", "Chunks", "P@1", "P@3", "MRR", "HR@3"]
    lines.append("## 检索指标")
    lines.append("")
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    for name, data in sorted_items:
        perf = data.get('performance', {}).get('stats', {})
        chunks = perf.get('total_chunks', {}).get('avg', 0)
        m = data.get('metrics', {})
        p1 = m.get('precision_at_1', {}).get('avg', 0)
        p3 = m.get('precision_at_3', {}).get('avg', 0)
        mrr = m.get('mrr', {}).get('avg', 0)
        hr3 = m.get('hit_rate_at_3', {}).get('avg', 0)
        lines.append(f"| {name} | {chunks:.0f} | {p1:.4f} | {p3:.4f} | {mrr:.4f} | {hr3:.4f} |")
    
    # 性能指标表格
    lines.append("")
    lines.append("## 性能指标")
    lines.append("")
    perf_headers = ["配置", "Chunks", "内存(MB)", "索引大小", "模型大小", "分块耗时(s)", "向量化耗时(s)"]
    lines.append("| " + " | ".join(perf_headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(perf_headers)) + " |")
    
    for name, data in sorted_items:
        perf = data.get('performance', {})
        stats = perf.get('stats', {})
        memory = perf.get('memory', {})
        meta = perf.get('meta', {})
        
        chunks = stats.get('total_chunks', {}).get('avg', 0)
        peak_mem = memory.get('peak_mb', {}).get('avg', 0)
        index_size = meta.get('index_size', 'N/A')
        model_size = meta.get('model_size', 'N/A')
        chunk_time = stats.get('chunk_time', {}).get('avg', 0)
        vector_time = stats.get('vector_time', {}).get('avg', 0)
        
        lines.append(f"| {name} | {chunks:.0f} | {peak_mem:.1f} | {index_size} | {model_size} | {chunk_time:.3f} | {vector_time:.2f} |")
    
    # 详细信息表格
    lines.append("")
    lines.append("## 详细信息")
    lines.append("")
    detail_headers = ["配置", "P@1", "P@3", "MRR", "HR@3", "Files", "Chunks", "Peak Mem(MB)", "分块(s)", "向量化(s)"]
    lines.append("| " + " | ".join(detail_headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(detail_headers)) + " |")
    
    for name, data in sorted_items:
        m = data.get('metrics', {})
        perf = data.get('performance', {})
        stats = perf.get('stats', {})
        memory = perf.get('memory', {})
        
        p1 = m.get('precision_at_1', {}).get('avg', 0)
        p3 = m.get('precision_at_3', {}).get('avg', 0)
        mrr = m.get('mrr', {}).get('avg', 0)
        hr3 = m.get('hit_rate_at_3', {}).get('avg', 0)
        files = stats.get('file_count', {}).get('avg', 0)
        chunks = stats.get('total_chunks', {}).get('avg', 0)
        peak_mem = memory.get('peak_mb', {}).get('avg', 0)
        chunk_time = stats.get('chunk_time', {}).get('avg', 0)
        vector_time = stats.get('vector_time', {}).get('avg', 0)
        
        lines.append(f"| {name} | {p1:.4f} | {p3:.4f} | {mrr:.4f} | {hr3:.4f} | {files:.0f} | {chunks:.0f} | {peak_mem:.1f} | {chunk_time:.3f} | {vector_time:.2f} |")
    
    return "\n".join(lines)


def generate_summary_json(summarized: Dict[str, dict], test_type: str) -> dict:
    """生成汇总 JSON"""
    result = {
        'test_type': test_type,
        'summary': {}
    }
    
    for name, data in summarized.items():
        summary_item = {
            'count': data.get('count', 1),
            'metrics': {},
            'performance': {}
        }
        
        for field, values in data.get('metrics', {}).items():
            summary_item['metrics'][field] = round(values['avg'], 4)
        
        for field, values in data.get('performance', {}).get('stats', {}).items():
            summary_item['performance'][field] = round(values['avg'], 4)
        
        # 添加 memory
        for field, values in data.get('performance', {}).get('memory', {}).items():
            summary_item['performance'][field] = round(values['avg'], 2)
        
        # 添加 meta
        meta = data.get('performance', {}).get('meta', {})
        if meta:
            summary_item['performance']['meta'] = meta
        
        result['summary'][name] = summary_item
    
    return result


def main():
    parser = argparse.ArgumentParser(description='汇总评估结果')
    parser.add_argument('--type', '-t', 
                       choices=['txt', 'md', 'pdf', 'doc', 'ppt', 'xls'],
                       default='txt',
                       help='测试类型 (默认: txt)')
    parser.add_argument('--input', '-i', 
                       help='输入目录路径 (覆盖 --type)')
    parser.add_argument('--output', '-o',
                       help='输出文件路径 (默认: {type}_summary.md)')
    parser.add_argument('--json-output',
                       help='输出 JSON 汇总文件路径')
    
    args = parser.parse_args()
    
    # 确定输入目录
    if args.input:
        type_dir = args.input
        test_type = os.path.basename(os.path.dirname(type_dir.rstrip('/\\'))) or test_type
    else:
        result_dir = os.path.join(backend_dir, "test", "ragas_test", "result")
        type_dir = os.path.join(result_dir, args.type)
        test_type = args.type
    
    print(f"扫描目录: {type_dir}")
    
    # 汇总结果
    summarized = summarize_test_type(type_dir, test_type)
    
    if not summarized:
        print("未找到任何结果文件")
        return
    
    print(f"找到 {len(summarized)} 个配置组合")
    
    # 生成 Markdown 报告
    md_content = generate_markdown_table(summarized, test_type)
    
    # 确定输出路径
    if args.output:
        md_output = args.output
    else:
        md_output = os.path.join(type_dir, f"{test_type}_summary.md")
    
    with open(md_output, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"Markdown 报告已保存: {md_output}")
    
    # 生成 JSON 汇总
    if args.json_output:
        json_output = args.json_output
    else:
        json_output = os.path.join(type_dir, f"{test_type}_summary.json")
    
    summary_json = generate_summary_json(summarized, test_type)
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(summary_json, f, ensure_ascii=False, indent=2)
    print(f"JSON 汇总已保存: {json_output}")
    
    # 打印预览
    print("\n" + "=" * 60)
    print("汇总预览")
    print("=" * 60)
    print(md_content[:2000])


if __name__ == "__main__":
    main()
