# RAG 模块文档

## 概述

RAG 模块是 AI 文件搜索器的核心组件，负责文件处理、向量化、存储和检索功能。作为对外的 RAG 系统接口，统一管理 EmbeddingModel、LocalLLM、VectorStore 等组件。

## 架构说明

```
┌─────────────────────────────────────────────────────────┐
│                     SystemManager                        │
│              (RAG 系统对外统一接口)                       │
│  ┌─────────────┬─────────────┬─────────────────────┐   │
│  │ Embedding   │  LocalLLM    │    VectorStore       │   │
│  │   Model     │ DeepSeekLLM │                     │   │
│  └─────────────┴─────────────┴─────────────────────┘   │
└─────────────────────────────────────────────────────────┘
           │              │                │
           ▼              ▼                ▼
      文本向量化     LLM生成           向量存储
```

## 核心组件

### SystemManager - 系统管理器

RAG 系统对外统一接口，负责加载和管理各组件实例。

**主要功能**：
- 嵌入模型管理 (EmbeddingModel)
- LLM 管理 (LocalLLM / DeepSeekLLM)
- 向量存储管理 (VectorStore)
- 单例模式确保全局唯一实例

**关键方法**：

| 方法 | 说明 |
|------|------|
| `get_instance()` | 获取单例实例 |
| `load_embedding_model()` | 加载嵌入模型 |
| `get_embedding_model()` | 获取嵌入模型，不存在则加载 |
| `init_vector_store()` | 初始化向量存储 |
| `get_vector_store()` | 获取向量存储，不存在则初始化 |
| `load_llm()` | 加载 LLM 模型 |
| `get_llm()` | 获取 LLM，不存在则加载 |
| `unload_llm()` | 卸载 LLM |
| `generate_with_llm()` | 封装 LLM 生成接口 |

---

### EmbeddingModel - 嵌入模型

负责将文本转换为向量。

**主要功能**：
- 加载 HuggingFace sentence-transformers 模型
- 文本向量化
- 图像向量化（多模态模型）

**支持的模型**：
- BGE 系列 (bge-base-zh-v1.5, bge-large-zh-v1.5, bge-small-zh-v1.5)
- BGE-M3 (多语言、多模态)
- M3E 系列
- Qwen3-Embedding

**关键方法**：
- `encode(texts)` - 文本转向量
- `encode_images(images)` - 图像转向量

---

### LocalLLM - 本地 LLM

负责本地 LLM 推理。

**主要功能**：
- 加载 HuggingFace 因果语言模型
- 文本生成

**关键方法**：
- `generate(prompt, system_prompt)` - 生成文本

---

### DeepSeekLLM - DeepSeek API 封装

负责调用 DeepSeek API 进行 LLM 推理。

**主要功能**：
- 调用 DeepSeek API
- 支持流式输出
- 错误重试

**关键方法**：
- `generate(prompt, system_prompt)` - 生成文本

---

### VectorStore - 向量存储

负责向量数据的存储和检索，基于 FAISS。

**主要功能**：
- FAISS 索引管理
- 向量添加和删除
- 相似度搜索
- 元数据管理
- 标记删除模式（支持 LSH 等索引）

**支持的索引类型**：

| 索引类型 | 说明 | 特点 |
|---------|------|------|
| IndexFlatL2 | 精确 L2 距离 | 精确但慢 |
| IndexFlatIP | 内积相似度 | 精确但慢 |
| IndexIVFFlat | IVF 聚类加速 | 需训练数据 |
| IndexHNSWFlat | HNSW 图索引 | 高召回高速 |
| IndexLSH | 局部敏感哈希 | 二值向量压缩 |

**关键方法**：

| 方法 | 说明 |
|------|------|
| `add(vectors, metas)` | 添加向量 |
| `search(query_vector, k)` | 搜索相似向量 |
| `remove_vectors_by_indices(indices)` | 删除指定索引的向量 |
| `remove_vectors_by_file(file_path)` | 删除指定文件的向量 |
| `rebuild_index()` | 重建索引（清除标记删除的向量） |

**存储文件**：
- `data/faiss_index.bin` - FAISS 索引文件
- `data/metadata.json` - 元数据文件
- `data/faiss_index.info` - 索引信息文件

---

### FileCache - 文件缓存管理器

负责文件修改时间跟踪和缓存管理。

**主要功能**：
- 文件修改时间缓存
- 智能缓存清理
- 避免重复处理未修改文件

**关键方法**：

| 方法 | 说明 |
|------|------|
| `should_process_file(file_path)` | 判断文件是否需要处理 |
| `update_file_cache(file_path)` | 更新文件缓存 |
| `clean_nonexistent_files()` | 清理不存在文件的缓存 |

---

### 分块策略 (ChunkingStrategy)

提供多种文本分块策略，支持灵活的内容切分（策略模式）。

**支持的策略**：

| 策略 | 说明 |
|------|------|
| FixedSizeChunking | 固定字符数分块 |
| ParagraphChunking | 按段落分块 |
| SentenceChunking | 按句子分块 |
| SlidingWindowChunking | 滑动窗口分块（带重叠） |
| MDSemanticChunking | 按 Markdown 标题层级分块 |
| SlideChunking | 按 PPT 幻灯片分块 |

**默认策略映射**：

```python
DEFAULT_STRATEGIES = {
    '.md': ParagraphChunking(),       # 段落分块
    '.txt': ParagraphChunking(),      # 段落分块
    '.docx': SlidingWindowChunking(), # 滑动窗口分块
    '.doc': SlidingWindowChunking(),   # 滑动窗口分块
    '.pdf': SentenceChunking(),        # 句子分块
    '.pptx': SlideChunking(),         # 幻灯片分块
    '.ppt': SlideChunking(),          # 幻灯片分块
}
```

---

## 数据流

```
用户输入 → 文件处理 → 向量化 → 存储 → 检索 → 结果返回
    ↓           ↓         ↓        ↓        ↓
  文件解析    文本分块   嵌入模型  向量搜索  相似度排序
```

## 使用示例

```python
from backend.RAG.SystemManager import SystemManager

sm = SystemManager.get_instance()

# 嵌入模型
embedding_model = sm.get_embedding_model()
vectors = embedding_model.encode(["hello world"])

# 向量存储
vector_store = sm.get_vector_store()
vector_store.add(vectors, metadata, file_name)

# 搜索
results = vector_store.search(query_vector, top_k=5)

# LLM 生成
response = sm.generate_with_llm(prompt)
```

## 最佳实践

### 文件组织
- 保持模块化设计
- 使用依赖注入
- 遵循单一职责原则

### 错误处理
- 使用异常捕获
- 提供有意义的错误信息
- 实现优雅降级

### 性能优化
- 合理使用缓存
- 避免重复计算
- 及时释放资源
