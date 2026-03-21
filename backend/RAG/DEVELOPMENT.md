# RAG (Retrieval-Augmented Generation) 模块文档

## 概述

RAG模块是AI文件搜索器的核心组件，负责文件处理、向量化、存储和检索功能。

## 文件结构

### 📁 SystemManager.py
**系统管理器** - 负责全局系统组件的初始化和管理

**主要功能**：
- 嵌入模型管理
- 向量存储管理
- 系统状态跟踪
- 单例模式确保全局唯一实例

**关键方法**：
- `get_embedding_model()` - 获取嵌入模型
- `get_vector_store()` - 获取向量存储
- `initialize_system()` - 初始化系统组件

---

### 📁 FileCache.py
**文件缓存管理器** - 负责文件修改时间跟踪和缓存管理

**主要功能**：
- 文件修改时间缓存
- 智能缓存清理
- 避免重复处理未修改文件

**关键方法**：
- `should_process_file(file_path)` - 判断文件是否需要处理
- `update_file_cache(file_path)` - 更新文件缓存
- `clean_nonexistent_files()` - 清理不存在文件的缓存

**缓存文件**：`local_data/file_cache.json`

---

### 📁 VectorStore.py
**向量存储管理器** - 负责向量数据的存储和检索

**主要功能**：
- FAISS索引管理
- 向量添加和删除
- 相似度搜索
- 元数据管理

**关键方法**：
- `add(vectors, metadata, file_name)` - 添加向量
- `search(query_vector, top_k)` - 搜索相似向量
- `remove_vectors_by_file(file_path)` - 删除指定文件的向量

**存储文件**：
- `local_data/faiss_index.bin` - FAISS索引文件
- `local_data/metadata.json` - 元数据文件

---

### 📁 FileProcessor.py
**文件处理器** - 负责各种文件格式的解析和内容提取

**支持格式**：
- `.md` - Markdown文件
- `.txt` - 纯文本文件
- `.pdf` - PDF文档
- `.docx` - Word文档
- `.pptx` - PowerPoint演示文稿
- `.xlsx` - Excel表格

**处理流程**：
1. 文件格式检测
2. 内容提取
3. 文本分块
4. 向量化处理
5. 返回处理结果

**关键方法**：
- `is_supported_file(file_path)` - 检查文件是否支持
- `process_file(file_path)` - 处理文件并返回向量

---

### 📁 core.py
**RAG核心组件** - 提供高级RAG功能

**主要功能**：
- 文档检索
- 上下文生成
- 答案合成
- 相关性排序

**关键方法**：
- `retrieve(query, top_k)` - 检索相关文档
- `generate_answer(query, context)` - 基于上下文生成答案

---

## 数据流

```
用户输入 → 文件处理 → 向量化 → 存储 → 检索 → 结果返回
    ↓           ↓         ↓        ↓        ↓
  文件解析    文本分块   嵌入模型  向量搜索  相似度排序
```

## 配置说明

### 嵌入模型配置
- **模型路径**：`models/bge-m3`
- **向量维度**：1024
- **支持语言**：多语言（中英文）

### 存储配置
- **索引类型**：FAISS
- **存储路径**：`local_data/`
- **自动保存**：每次更新后保存

## 性能优化

### 缓存策略
- **文件级缓存**：避免重复处理未修改文件
- **向量级缓存**：FAISS索引提供快速检索
- **内存管理**：懒加载和及时释放

### 并发处理
- **异步处理**：支持大文件并发处理
- **批量操作**：向量批量添加提高效率
- **流式输出**：实时进度反馈

## 故障排除

### 常见问题

**1. 模型加载失败**
- 检查模型文件是否存在
- 确认模型路径配置正确
- 检查内存是否充足

**2. 向量存储错误**
- 检查磁盘空间
- 确认写入权限
- 验证数据格式

**3. 文件处理失败**
- 检查文件格式是否支持
- 确认文件没有损坏
- 检查编码格式

### 调试方法

**启用详细日志**：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**性能监控**：
- 监控内存使用情况
- 跟踪处理时间
- 记录错误统计

## 扩展开发

### 添加新文件格式支持
1. 在`FileProcessor.py`中添加解析器
2. 更新`is_supported_file()`方法
3. 添加相应的测试用例

### 集成新嵌入模型
1. 在`SystemManager.py`中添加模型加载逻辑
2. 更新配置文件
3. 测试模型兼容性

### 自定义存储后端
1. 实现`VectorStore`接口
2. 在`SystemManager.py`中注册
3. 添加相应的配置选项

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

---

**更新日期**：2026年3月19日  
**版本**：1.0.0  
**维护者**：AI File Searcher Team
