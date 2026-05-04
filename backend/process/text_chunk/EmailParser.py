import os
import email
import re
from email.header import decode_header
from typing import Dict, Any
from .TextChunkProcessor import TextChunkProcessor


class EmailParser(TextChunkProcessor):
    """
    邮件文件解析器 (.eml)
    提取邮件头和正文为自然语言文本后分块
    """

    type = "email"

    def __init__(self, file_path: str, **kwargs):
        super().__init__(file_path, **kwargs)
        self._subject: str = ""
        self._sender: str = ""
        self._date: str = ""
        self._recipients: str = ""

    @staticmethod
    def _decode_header_value(value: str) -> str:
        """解码邮件头部字段"""
        if not value:
            return ""
        decoded_parts = decode_header(value)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                # charset 可能是 'unknown-8bit' 等无效编码，需逐个尝试
                encodings = [charset, "utf-8", "gbk", "gb2312", "latin-1"]
                decoded = None
                for enc in encodings:
                    if not enc or enc == "unknown-8bit":
                        continue
                    try:
                        decoded = part.decode(enc, errors="replace")
                        break
                    except (LookupError, UnicodeDecodeError):
                        continue
                result.append(decoded or part.decode("utf-8", errors="replace"))
            else:
                result.append(part)
        return "".join(result)

    @staticmethod
    def _get_payload_text(part) -> str:
        """安全提取邮件 part 的文本内容"""
        charset = part.get_content_charset()

        # 优先使用 get_payload(decode=True) 正确解码
        try:
            raw = part.get_payload(decode=True)
            if raw is not None:
                enc = charset or "utf-8"
                # 某些邮件声明了错误编码，逐个尝试
                for attempt_enc in [enc, "utf-8", "gbk", "gb2312", "latin-1"]:
                    try:
                        return raw.decode(attempt_enc, errors="replace")
                    except (LookupError, UnicodeDecodeError):
                        continue
                return raw.decode("utf-8", errors="replace")
        except Exception:
            pass

        # 降级：直接获取 payload（可能是 string 或 list）
        payload = part.get_payload()
        if isinstance(payload, str):
            return payload
        if isinstance(payload, list):
            # multipart 的子 part 列表，拼接文本
            texts = []
            for sub in payload:
                if hasattr(sub, "get_content_type"):
                    if sub.get_content_type() == "text/plain":
                        texts.append(EmailParser._get_payload_text(sub))
            return "\n".join(texts)
        return str(payload) if payload else ""

    def _extract_content(self) -> str:
        try:
            # 优先从二进制解析（标准邮件格式）
            try:
                with open(self.file_path, "rb") as f:
                    raw_bytes = f.read()
                msg = email.message_from_bytes(raw_bytes)
            except Exception:
                # 降级：从字符串解析（非标准格式，如手写 eml）
                with open(self.file_path, "r", encoding="utf-8", errors="replace") as f:
                    raw_text = f.read()
                msg = email.message_from_string(raw_text)

            # 提取头部信息
            self._subject = self._decode_header_value(msg.get("Subject", ""))
            self._sender = self._decode_header_value(msg.get("From", ""))
            self._date = msg.get("Date", "")
            to_str = self._decode_header_value(msg.get("To", ""))
            cc_str = self._decode_header_value(msg.get("Cc", ""))
            self._recipients = ", ".join(filter(None, [to_str, cc_str]))

            # 组装自然语言文本
            text_parts = []
            text_parts.append(f"主题: {self._subject}")
            text_parts.append(f"发件人: {self._sender}")
            if self._date:
                text_parts.append(f"日期: {self._date}")
            if self._recipients:
                text_parts.append(f"收件人: {self._recipients}")
            text_parts.append("")

            # 解析邮件正文
            if msg.is_multipart():
                html_fallback = ""
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))

                    if "attachment" in content_disposition:
                        continue

                    if content_type == "text/plain":
                        body = self._get_payload_text(part)
                        if body:
                            text_parts.append(body)
                    elif content_type == "text/html" and not html_fallback:
                        html = self._get_payload_text(part)
                        clean = re.sub(r"<[^>]+>", " ", html)
                        clean = re.sub(r"\s+", " ", clean).strip()
                        html_fallback = clean

                # 如果没有纯文本，使用 HTML 降级
                if len(text_parts) <= 4 and html_fallback:
                    text_parts.append(html_fallback)
            else:
                body = self._get_payload_text(msg)
                if body:
                    text_parts.append(body)

            extracted = "\n".join(text_parts)
            return extracted if extracted.strip() else ""

        except Exception as e:
            print(f"❌ 读取邮件文件失败 {self.file_path}: {e}")
            return ""

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            **self._metadata,
            "subject": self._subject,
            "sender": self._sender,
            "date": self._date,
            "recipients": self._recipients,
            "content_length": len(self._parsed_content),
            "chunk_count": len(self._chunks),
        }
