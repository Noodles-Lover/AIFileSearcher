# 测试文件说明

本文件夹包含AI文件搜索器的所有测试脚本，按功能分类：

## 🧮 算法测试
- **`test_algorithm_simple.py`** - 动态分块提取算法测试
  - 测试简单对数函数：`y = 7 * log_k(x)`
  - 用户衰减率1-10映射到对数底数1.25-1.55
  - 验证单调递增性能
  - 运行：`python test_algorithm_simple.py`

- **`test_decay_rates.py`** - 衰减率参数测试
  - 测试不同衰减率对提取数量的影响
  - 验证衰减率映射关系
  - 运行：`python test_decay_rates.py`

- **`test_decay_mapping.py`** - 衰减率映射测试
  - 详细测试衰减率1-10到对数底数的映射
  - 验证不同数据量下的提取效果
  - 运行：`python test_decay_mapping.py`

## 🔧 功能测试
- **`test_file_merge.py`** - 文件合并功能测试
  - 测试语义搜索结果按文件合并
  - 验证每个文件只保留最佳分块
  - 运行：`python test_file_merge.py`

- **`test_local_data.py`** - 本地数据功能测试
  - 测试local_data目录的文件读取
  - 验证路径配置正确性
  - 运行：`python test_local_data.py`

- **`test_list_api.py`** - 文件列表API测试
  - 测试/api/list端点功能
  - 验证Everything和备用实现
  - 运行：`python test_list_api.py`

- **`test_icon_fix.py`** - 图标功能测试
  - 测试系统图标获取和缓存
  - 验证不同文件类型图标显示
  - 运行：`python test_icon_fix.py`

- **`test_search_content.py`** - 搜索内容测试
  - 测试搜索结果是否包含content字段
  - 验证前后端数据一致性
  - 运行：`python test_search_content.py`

## 🔗 核心组件测试
- **`test_embedding.py`** - 嵌入模型测试
  - 测试文本向量化功能
  - 验证嵌入模型加载和推理
  - 运行：`python test_embedding.py`

- **`test_faiss.py`** - FAISS向量搜索测试
  - 测试向量索引和搜索
  - 验证相似度计算准确性
  - 运行：`python test_faiss.py`

- **`test_sse.py`** - 服务器发送事件测试
  - 测试索引进度实时更新
  - 验证SSE连接和数据流
  - 运行：`python test_sse.py`

## 📝 使用说明

### 运行单个测试
```bash
cd backend/test
python test_algorithm_simple.py
```

### 运行所有算法测试
```bash
cd backend/test
python test_algorithm_simple.py && python test_decay_rates.py && python test_decay_mapping.py
```

### 运行所有功能测试
```bash
cd backend/test
python test_file_merge.py && python test_local_data.py && python test_list_api.py
```
