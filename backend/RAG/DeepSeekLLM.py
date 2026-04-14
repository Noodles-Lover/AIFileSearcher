"""
DeepSeek API LLM 封装
"""
from openai import OpenAI
import os
import winreg


def disable_system_proxy():
    """临时禁用 Windows 系统代理"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                            0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        # 强制刷新
        import ctypes
        INTERNET_OPTION_SETTINGS_CHANGED = 39
        INTERNET_OPTION_REFRESH = 37
        ctypes.windll.wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, None, 0)
        ctypes.windll.wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, None, 0)
        return True
    except Exception:
        return False


def restore_system_proxy(enabled, server):
    """恢复 Windows 系统代理"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                            0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, enabled)
        if server:
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, server)
        winreg.CloseKey(key)
        import ctypes
        INTERNET_OPTION_SETTINGS_CHANGED = 39
        INTERNET_OPTION_REFRESH = 37
        ctypes.windll.wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, None, 0)
        ctypes.windll.wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, None, 0)
    except Exception:
        pass


class DeepSeekLLM:
    """DeepSeek API 调用封装"""
    
    BASE_URL = "https://api.deepseek.com"
    MODEL = "deepseek-chat"
    
    def __init__(self, api_key: str = ""):
        # 如果没有提供 API Key，使用默认的
        if not api_key:
            api_key = "PROTECTED_KEY_REMOVED"
        
        # 禁用系统代理
        self._proxy_enabled = 0
        self._proxy_server = ""
        self._disable_proxy()
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.BASE_URL,
        )
    
    def _disable_proxy(self):
        """禁用 Windows 系统代理"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                                0, winreg.KEY_ALL_ACCESS)
            try:
                self._proxy_enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
                self._proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
            except FileNotFoundError:
                self._proxy_enabled = 0
                self._proxy_server = ""
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            # 强制刷新
            import ctypes
            ctypes.windll.wininet.InternetSetOptionW(0, 39, None, 0)
            ctypes.windll.wininet.InternetSetOptionW(0, 37, None, 0)
        except Exception:
            pass
    
    def _restore_proxy(self):
        """恢复 Windows 系统代理"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                                0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, self._proxy_enabled)
            if self._proxy_server:
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, self._proxy_server)
            winreg.CloseKey(key)
            import ctypes
            ctypes.windll.wininet.InternetSetOptionW(0, 39, None, 0)
            ctypes.windll.wininet.InternetSetOptionW(0, 37, None, 0)
        except Exception:
            pass
    
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """
        调用 DeepSeek API 生成文本
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示（可选）
            **kwargs: 其他参数 (max_tokens, temperature, top_p)
        
        Returns:
            str: 生成的文本
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        max_tokens = kwargs.get("max_tokens", 256)
        temperature = kwargs.get("temperature", 0.7)
        top_p = kwargs.get("top_p", 0.9)
        
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        
        return response.choices[0].message.content
