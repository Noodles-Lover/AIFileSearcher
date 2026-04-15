# RAG 模块文档

## 概述

RAG 模块是 AI 文件搜索器的核心组件，负责文件处理、向量化、存储和检索功能。作为对外的 RAG 系统接口，统一管理 EmbeddingModel、LocalLLM、VectorStore 等组件。

## 架构说明

```
┌─────────────────────────────────────────────────────────┐
│                     SystemManager                        │
│              (RAG 系统对外统一接口)                       │
│  ┌─────────────┬─────────────┬─────────────────────┐   │
│  │ Embedding   │  LocalLLM   │    VectorStore      │   │
│  │   Model     │             │                     │   │
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
- LLM 管理 (LocalLLM)
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

**配置读取**：
- `embedding_model`: 嵌入模型名称（默认 bge-m3）
- `llm_model`: LLM 模型名称
- `index_type`: 向量索引类型（默认 IndexFlatL2）

---

### EmbeddingModel - 嵌入模型

负责将文本转换为向量。

**主要功能**：
- 加载 HuggingFace sentence-transformers 模型
- 文本向量化
- 图像向量化（多模态模型）

**关键方法**：
- `encode(texts)` - 文本转向量
- `encode_images(images)` - 图像转向量

---

### LocalLLM - 本地 LLM

负责 LLM 推理。

**主要功能**：
- 加载 HuggingFace 因果语言模型
- 文本生成

**关键方法**：
- `generate(prompt, system_prompt)` - 生成文本

---

### VectorStore - 向量存储

负责向量数据的存储和检索。

**主要功能**：
- FAISS 索引管理
- 向量添加和删除
- 相似度搜索
- 元数据管理

**关键方法**：

| 方法 | 说明 |
|------|------|
| `add(vectors, metadata, file_name)` | 添加向量 |
| `search(query_vector, top_k)` | 搜索相似向量 |
| `remove_vectors_by_file(file_path)` | 删除指定文件的向量 |

**存储文件**：
- `local_data/faiss_index.bin` - FAISS 索引文件
- `local_data/metadata.json` - 元数据文件

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

**缓存文件**：`local_data/file_cache.json`

---

### 分块策略 (ChunkingStrategy)

提供多种文本分块策略，支持灵活的内容切分。

**支持的策略**：

| 策略 | 说明 |
|------|------|
| `FixedSizeChunking` | 固定字符数分块 |
| `ParagraphChunking` | 按段落分块 |
| `SentenceChunking` | 按句子分块 |
| `SlidingWindowChunking` | 滑动窗口分块（带重叠） |

**默认策略映射**：不同文件类型使用不同的默认分块策略。

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

embedding_model = sm.get_embedding_model()
vectors = embedding_model.encode(["hello world"])

vector_store = sm.get_vector_store()
vector_store.add(vectors, metadata, file_name)

results = vector_store.search(query_vector, top_k=5)

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
