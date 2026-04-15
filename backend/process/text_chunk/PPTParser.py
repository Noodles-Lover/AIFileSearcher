import os
import pptx
from .TextChunkProcessor import TextChunkProcessor


class PPTParser(TextChunkProcessor):
    """
    PPT/PPTX 文件解析器
    支持 .ppt (旧版 PowerPoint 97-2003) 和 .pptx (新版)
    """
    type = 'ppt'

    def _extract_content(self) -> str:
        ext = os.path.splitext(self.file_path)[1].lower()
        
        if ext == '.pptx':
            return self._extract_pptx()
        elif ext == '.ppt':
            return self._extract_ppt()
        else:
            return ""

    def _extract_pptx(self) -> str:
        """使用 python-pptx 提取 .pptx 文本"""
        try:
            prs = pptx.Presentation(self.file_path)
            full_text = []

            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        full_text.append(shape.text)

            return '\n'.join(full_text)
        except Exception as e:
            print(f"Error reading PPTX file {self.file_path}: {e}")
            return ""

    def _extract_ppt(self) -> str:
        """使用 pywin32 + PowerPoint COM 提取 .ppt 文本"""
        try:
            import win32com.client
            
            ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            ppt_app.Visible = True  # 必须设为 True，否则会报错
            
            try:
                # 转换为绝对路径
                abs_path = os.path.abspath(self.file_path)
                presentation = ppt_app.Presentations.Open(abs_path, ReadOnly=True, WithWindow=True)
                
                full_text = []
                for slide in presentation.Slides:
                    for shape in slide.Shapes:
                        if shape.HasTextFrame:
                            text = shape.TextFrame.TextRange.Text
                            if text.strip():
                                full_text.append(text.strip())
                
                presentation.Close()
                return '\n'.join(full_text)
                
            finally:
                ppt_app.Quit()
                
        except Exception as e:
            print(f"Error reading PPT file {self.file_path} with pywin32: {e}")
            # 回退到文件名描述
            return ""

        return ""
