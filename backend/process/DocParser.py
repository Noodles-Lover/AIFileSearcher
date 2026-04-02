from pathlib import Path
from typing import List
from collections import defaultdict
import subprocess
import os

# 尝试导入 textract，失败时设置标志
HAS_EXTRACTOR = False
try:
    import textract
    HAS_EXTRACTOR = True
except ImportError:
    print("Warning: textract not installed, trying alternative methods for .doc files")

# 尝试导入 win32com，作为后备方案
try:
    import win32com.client
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False
    print("Warning: win32com not installed, .doc files may not be supported")

from .BaseParser import BaseParser

class DocParser(BaseParser):
    """
    DOC 文件解析器
    优先使用 textract，失败时使用 win32com 作为后备方案
    """
    type = 'doc'
    
    def _extract_content(self) -> str:
        """
        提取 DOC 文件內容
        优先使用 textract，失败时使用 win32com
        """
        # 优先使用 textract
        if HAS_EXTRACTOR:
            try:
                text = textract.process(self.file_path, encoding='utf-8').decode('utf-8')
                return text.strip()
            except Exception as e:
                print(f"Error using textract for {self.file_path}: {e}")
                # 失败时尝试 win32com
                if HAS_WIN32COM:
                    return self._extract_with_win32com()
                else:
                    return ""
        # 后备方案：使用 win32com
        elif HAS_WIN32COM:
            return self._extract_with_win32com()
        else:
            print("Error: No .doc file extractor available (textract or win32com)")
            return ""
    
    def _extract_with_win32com(self) -> str:
        """
        使用 win32com 提取 DOC 文件內容
        """
        try:
            word = win32com.client.Dispatch('Word.Application')
            word.Visible = False
            doc = word.Documents.Open(self.file_path)
            full_text = []
            
            # 提取段落
            for para in doc.Paragraphs:
                text = para.Range.Text.strip()
                if text:
                    full_text.append(text)
            
            # 关闭文档和应用
            doc.Close(False)
            word.Quit()
            
            return '\n'.join(full_text)
        except Exception as e:
            print(f"Error reading DOC file {self.file_path}: {e}")
            # 尝试清理 COM 对象
            try:
                word.Quit()
            except:
                pass
            return ""
    
    def _extract_metadata(self) -> defaultdict:
        metadata = defaultdict(str)
        # 尝试使用 win32com 提取元数据
        if HAS_WIN32COM:
            try:
                word = win32com.client.Dispatch('Word.Application')
                word.Visible = False
                doc = word.Documents.Open(self.file_path)
                
                # 提取文档属性
                properties = doc.BuiltInDocumentProperties
                try:
                    metadata['title'] = properties('Title').Value
                except:
                    pass
                try:
                    metadata['author'] = properties('Author').Value
                except:
                    pass
                try:
                    metadata['subject'] = properties('Subject').Value
                except:
                    pass
                try:
                    metadata['keywords'] = properties('Keywords').Value
                except:
                    pass
                try:
                    metadata['created'] = str(properties('Creation Date').Value)
                except:
                    pass
                try:
                    metadata['modified'] = str(properties('Last Save Time').Value)
                except:
                    pass
                
                doc.Close(False)
                word.Quit()
            except Exception as e:
                print(f"Error extracting DOC metadata: {e}")
                # 尝试清理 COM 对象
                try:
                    word.Quit()
                except:
                    pass
        return metadata
    
    def _check_format(self) -> bool:
        f_path: Path = Path(self.file_path)
        return f_path.exists() and f_path.suffix.lower() == '.doc'