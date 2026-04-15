import fitz
from .TextChunkProcessor import TextChunkProcessor


class PDFParser(TextChunkProcessor):
    """
    PDF 文件解析器
    """
    type = 'pdf'

    def _extract_content(self) -> str:
        try:
            pdf_doc: fitz.Document = fitz.open(self.file_path)
            if pdf_doc.needs_pass:
                pdf_doc.close()
                return ""

            raw_text = ""
            total_text_len = 0
            total_images = 0
            
            for page in pdf_doc:
                text = page.get_text("text").strip()
                raw_text += text + "\n"
                total_text_len += len(text)
                total_images += len(page.get_images(full=True))
            
            # 简单检测扫描件：文本很少但图片较多（需要在 close 之前）
            page_count = pdf_doc.page_count
            if page_count > 0:
                avg_text_per_page = total_text_len / page_count
                if avg_text_per_page < 100 and total_images >= page_count:
                    pdf_doc.close()
                    print(f"检测到扫描件 PDF: {self.file_path} (文本: {total_text_len} 字符, 图片: {total_images} 张)")
                    self._is_scanned_pdf = True
                    return ""
            
            pdf_doc.close()
            return raw_text
        except Exception as e:
            print(f"Error reading PDF file {self.file_path}: {e}")
            return ""
    
    def get_text(self):
        """重写以处理扫描件"""
        self._parsed_content = self._extract_content()
        
        if not self._parsed_content and getattr(self, '_is_scanned_pdf', False):
            # 扫描件，调用 LLM 生成描述（复用 BinaryProcessor 逻辑）
            description = self._generate_scanned_description()
            self._chunks = [description]
            return self._chunks
        
        if not self._parsed_content:
            return []
        
        if self.chunking_strategy:
            self._chunks = self.chunking_strategy.chunk(self._parsed_content)
        else:
            self._chunks = [self._parsed_content]
        
        return self._chunks
    
    def _generate_scanned_description(self) -> str:
        """为扫描件 PDF 生成 LLM 描述"""
        from backend.process.binary.BinaryProcessor import BinaryProcessor
        import os
        
        file_name = os.path.splitext(os.path.basename(self.file_path))[0]
        file_ext = os.path.splitext(self.file_path)[1]
        
        # 复用 BinaryProcessor 的目录结构分析
        binary_proc = BinaryProcessor(
            self.file_path,
            vector_store=self.vector_store,
            embedding_model=self.embedding_model,
            llm_client=self.llm_client
        )
        
        # 分析目录结构
        structure = binary_proc._analyze_structure()
        
        # 生成描述
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
