import fitz
import re
from .TextChunkProcessor import TextChunkProcessor
from .TablePreprocessor import TablePreprocessor


class PDFParser(TextChunkProcessor):
    """
    PDF 文件解析器
    支持页码标记输出，便于分块策略解析
    """
    type = 'pdf'

    def __init__(self, file_path: str, **kwargs):
        super().__init__(file_path, **kwargs)
        self._page_count = 0

    def _extract_content(self) -> str:
        try:
            pdf_doc: fitz.Document = fitz.open(self.file_path)
            if pdf_doc.needs_pass:
                pdf_doc.close()
                return ""

            raw_text_parts = []
            total_text_len = 0
            total_images = 0
            self._page_count = pdf_doc.page_count

            for page_num, page in enumerate(pdf_doc, 1):
                text = page.get_text("text").strip()
                total_text_len += len(text)
                total_images += len(page.get_images(full=True))

                if text:
                    # 添加页码标记，便于分块策略解析
                    raw_text_parts.append(f"[PAGE:{page_num}]\n{text}")

            # 简单检测扫描件
            if self._page_count > 0:
                avg_text_per_page = total_text_len / self._page_count
                if avg_text_per_page < 100 and total_images >= self._page_count:
                    pdf_doc.close()
                    print(f"检测到扫描件 PDF: {self.file_path} (文本: {total_text_len} 字符, 图片: {total_images} 张)")
                    self._is_scanned_pdf = True
                    return ""

            pdf_doc.close()

            # 返回带页码标记的文本
            return '\n\n'.join(raw_text_parts)
        except Exception as e:
            print(f"Error reading PDF file {self.file_path}: {e}")
            return ""

    def get_text(self):
        """重写以处理扫描件"""
        self._parsed_content = self._extract_content()

        if not self._parsed_content and getattr(self, '_is_scanned_pdf', False):
            # 扫描件，调用 LLM 生成描述
            description = self._generate_scanned_description()
            self._chunks = [description]
            return self._chunks

        if not self._parsed_content:
            return []

        # 表格预处理标准化后，进入常规分块流程
        self._parsed_content = TablePreprocessor.preprocess(self._parsed_content)

        if self.chunking_strategy:
            self._chunks = self.chunking_strategy.chunk(self._parsed_content)
        else:
            self._chunks = [self._parsed_content] if self._parsed_content.strip() else []

        return self._chunks

    def _generate_scanned_description(self) -> str:
        """为扫描件 PDF 生成 LLM 描述"""
        from backend.process.binary.BinaryProcessor import BinaryProcessor
        import os

        file_name = os.path.splitext(os.path.basename(self.file_path))[0]
        file_ext = os.path.splitext(self.file_path)[1]

        binary_proc = BinaryProcessor(
            self.file_path,
            vector_store=self.vector_store,
            embedding_model=self.embedding_model,
            llm_client=self.llm_client
        )

        structure = binary_proc._analyze_structure()

        sibling_info = ""
        if structure.get("sibling_files"):
            sibling_info = f"\n同目录文件: {', '.join(structure['sibling_files'][:5])}"

        prompt = f"""你是一个专业的文件分析助手。请根据文件信息，为该扫描件 PDF 文件生成一段简洁、信息丰富、便于后续向量检索的文本说明。

【任务要求】
1. 这是一个扫描件 PDF（图片合成的 PDF，无可提取的文本）
2. 根据文件名推测文档内容、来源或用途
3. 结合同级文件信息，判断该文件在目录结构中的角色
4. 描述长度控制在 80~150 字之间
5. 输出只包含描述文本，不要有多余的解释或格式

【文件信息】
文件名：{file_name}
文件类型：{file_ext}（扫描件 PDF）
绝对路径：{self.file_path}
所在目录：{structure.get('locate_dir', '未知')}{sibling_info}"""

        try:
            from backend.RAG.SystemManager import SystemManager
            sm = SystemManager.get_instance()
            response = sm.generate_with_llm(prompt)
            print(f"* 扫描件 LLM 描述: {response}")
            return response if response else f"扫描件 PDF 文件: {file_name}"
        except Exception as e:
            print(f"LLM 描述生成失败: {e}")
            return f"扫描件 PDF 文件: {file_name}"
