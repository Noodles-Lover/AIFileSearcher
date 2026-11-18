"""模型权重格式工具：把 torch .bin 权重转换为 safetensors。

transformers 5.x 禁止 torch < 2.6 加载 .bin 权重，safetensors 不受该限制。
"""
import json
import os

import torch
from safetensors.torch import save_file


def _convert_one(bin_path: str, safe_path: str) -> dict:
    """转换单个权重文件，返回张量表（原子写，失败不留半成品）"""
    state_dict = torch.load(bin_path, map_location="cpu", weights_only=True)
    # 解除共享存储（tied embeddings），否则 save_file 拒绝写入
    state_dict = {k: v.contiguous().clone() for k, v in state_dict.items()}
    tmp_path = safe_path + ".tmp"
    save_file(state_dict, tmp_path, metadata={"format": "pt"})
    os.replace(tmp_path, safe_path)
    return state_dict


def ensure_safetensors(model_dir: str, remove_bin: bool = False) -> bool:
    """目录内只有 .bin 权重时转换为 safetensors，已是 safetensors 则跳过。

    :param remove_bin: 转换成功后删除原 .bin（下载流程使用，节省一倍磁盘）
    :return: 是否执行了转换
    """
    safe_single = os.path.join(model_dir, "model.safetensors")
    safe_index = os.path.join(model_dir, "model.safetensors.index.json")
    if os.path.exists(safe_single) or os.path.exists(safe_index):
        return False

    bin_index = os.path.join(model_dir, "pytorch_model.bin.index.json")
    converted = False

    if os.path.exists(bin_index):
        with open(bin_index, "r", encoding="utf-8") as f:
            index = json.load(f)
        weight_map = index.get("weight_map", {})
        new_weight_map = {}
        total_size = 0
        for bin_name in sorted(set(weight_map.values())):
            bin_path = os.path.join(model_dir, bin_name)
            if not os.path.exists(bin_path):
                continue
            safe_name = bin_name[:-4] + ".safetensors" if bin_name.endswith(".bin") else bin_name + ".safetensors"
            state_dict = _convert_one(bin_path, os.path.join(model_dir, safe_name))
            for key in state_dict:
                new_weight_map[key] = safe_name
            total_size += sum(v.numel() * v.element_size() for v in state_dict.values())
            if remove_bin:
                os.remove(bin_path)
            converted = True
        if converted:
            tmp_index = safe_index + ".tmp"
            with open(tmp_index, "w", encoding="utf-8") as f:
                json.dump({"metadata": {"total_size": total_size}, "weight_map": new_weight_map}, f, indent=2)
            os.replace(tmp_index, safe_index)
            if remove_bin:
                os.remove(bin_index)
    else:
        bin_path = os.path.join(model_dir, "pytorch_model.bin")
        if os.path.exists(bin_path):
            _convert_one(bin_path, safe_single)
            if remove_bin:
                os.remove(bin_path)
            converted = True

    return converted
