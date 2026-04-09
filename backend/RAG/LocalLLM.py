import os
from typing import Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from backend.utils.path_utils import get_models_path


class LocalLLM:
    """
    Minimal local LLM wrapper for loading a Hugging Face causal LM and running
    prompt -> text generation.
    """

    def __init__(self, model_name: str, device: str | None = None, trust_remote_code: bool = True):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.trust_remote_code = trust_remote_code
        self.model_path = self._resolve_model_path(model_name)

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=trust_remote_code,
        )

        model_kwargs = {
            "trust_remote_code": trust_remote_code,
            "low_cpu_mem_usage": True,
        }

        if self.device == "cuda" and torch.cuda.is_available():
            model_kwargs["torch_dtype"] = torch.float16
            model_kwargs["device_map"] = "auto"
        else:
            model_kwargs["torch_dtype"] = torch.float32

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            **model_kwargs,
        )

        if self.device != "cuda":
            self.model.to(self.device)

        if self.tokenizer.pad_token_id is None and self.tokenizer.eos_token_id is not None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _resolve_model_path(self, model_name: str) -> str:
        local_path = get_models_path(model_name)
        if os.path.exists(local_path):
            return local_path
        return model_name

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        final_prompt = self._build_prompt(prompt, system_prompt)

        inputs = self.tokenizer(final_prompt, return_tensors="pt")
        inputs = {key: value.to(self.model.device) for key, value in inputs.items()}

        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        generated_ids = output[0][inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

    def _build_prompt(self, prompt: str, system_prompt: str) -> str:
        if hasattr(self.tokenizer, "apply_chat_template"):
            messages = []
            if system_prompt.strip():
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            return self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )

        if system_prompt.strip():
            return f"System: {system_prompt}\n\nUser: {prompt}\nAssistant:"
        return prompt
