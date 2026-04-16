"""
PPT/PPTX 文件解析器
支持 .ppt (旧版 PowerPoint 97-2003) 和 .pptx (新版)
"""
import os
import pptx
from .TextChunkProcessor import TextChunkProcessor


class PPTParser(TextChunkProcessor):
    """
    PPT/PPTX 文件解析器
    
    输出格式：
    [SLIDE:1:标题]
    内容1-1
    内容1-2
    [备注:]
    备注内容
    
    [SLIDE:2:标题]
    内容2-1
    """
    type = 'ppt'

    def __init__(self, file_path: str, **kwargs):
        super().__init__(file_path, **kwargs)
        self._slide_data = []  # 存储幻灯片数据供后续使用

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
            self._slide_data = []
            marked_parts = []

            for slide_num, slide in enumerate(prs.slides, 1):
                # 提取标题
                title = ""
                for shape in slide.shapes:
                    if hasattr(shape, "is_placeholder") and shape.is_placeholder:
                        if shape.placeholder_format.type in (1, 2, 3):  # TITLE, CENTER_TITLE, SUBTITLE
                            if shape.text.strip():
                                title = shape.text.strip()
                                break

                # 提取正文内容
                slide_texts = []
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        # 跳过标题和占位符
                        if shape.text.strip() == title:
                            continue
                        if hasattr(shape, "is_placeholder") and shape.is_placeholder:
                            continue
                        slide_texts.append(shape.text.strip())

                # 提取备注
                notes = ""
                if slide.has_notes_slide:
                    notes_frame = slide.notes_slide.notes_text_frame
                    if notes_frame and notes_frame.text.strip():
                        notes = notes_frame.text.strip()

                # 存储幻灯片数据
                self._slide_data.append({
                    'num': slide_num,
                    'title': title,
                    'content': '\n'.join(slide_texts),
                    'notes': notes
                })

                # 构建带标记的幻灯片文本
                slide_lines = [f"[SLIDE:{slide_num}:{title}]"]
                if slide_texts:
                    slide_lines.append('\n'.join(slide_texts))
                if notes:
                    slide_lines.append(f"[备注:]\n{notes}")
                
                marked_parts.append('\n'.join(slide_lines))

            return '\n\n'.join(marked_parts)

        except Exception as e:
            print(f"Error reading PPTX file {self.file_path}: {e}")
            return ""

    def _extract_ppt(self) -> str:
        """使用 pywin32 + PowerPoint COM 提取 .ppt 文本"""
        try:
            import win32com.client

            ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            ppt_app.Visible = True

            try:
                abs_path = os.path.abspath(self.file_path)
                presentation = ppt_app.Presentations.Open(abs_path, ReadOnly=True, WithWindow=True)

                self._slide_data = []
                marked_parts = []

                for slide_num, slide in enumerate(presentation.Slides, 1):
                    # 提取标题和内容
                    slide_texts = []
                    title = ""

                    for shape in slide.Shapes:
                        try:
                            if not shape.HasTextFrame:
                                continue
                                
                            # 检查是否为标题占位符
                            if hasattr(shape, "PlaceholderFormat") and shape.PlaceholderFormat:
                                if shape.PlaceholderFormat.Type in (1, 2, 3):
                                    text = shape.TextFrame.TextRange.Text
                                    if text.strip():
                                        title = text.strip()
                                        continue

                            # 提取正文
                            text = shape.TextFrame.TextRange.Text
                            if text.strip():
                                slide_texts.append(text.strip())
                        except Exception:
                            continue

                    # 提取备注
                    notes = ""
                    if slide.NotesPage.Shapes.Count > 0:
                        notes_shape = slide.NotesPage.Shapes.Placeholders(2)
                        if notes_shape:
                            notes = notes_shape.TextFrame.TextRange.Text.strip()

                    # 存储幻灯片数据
                    self._slide_data.append({
                        'num': slide_num,
                        'title': title,
                        'content': '\n'.join(slide_texts),
                        'notes': notes
                    })

                    # 构建带标记的幻灯片文本
                    slide_lines = [f"[SLIDE:{slide_num}:{title}]"]
                    if slide_texts:
                        slide_lines.append('\n'.join(slide_texts))
                    if notes:
                        slide_lines.append(f"[备注:]\n{notes}")
                    
                    marked_parts.append('\n'.join(slide_lines))

                presentation.Close()
                return '\n\n'.join(marked_parts)

            finally:
                ppt_app.Quit()

        except Exception as e:
            print(f"Error reading PPT file {self.file_path} with pywin32: {e}")
            return ""

    def get_slide_data(self):
        """获取所有幻灯片的结构化数据"""
        return self._slide_data
