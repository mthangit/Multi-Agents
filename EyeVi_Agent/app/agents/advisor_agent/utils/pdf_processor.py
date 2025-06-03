import PyPDF2
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
from langchain.docstore.document import Document
from config import Config
import re

class PDFProcessor:
    def __init__(self):
        """
        Khởi tạo PDF processor với chunking strategy tối ưu cho tiếng Việt
        """
        print(f"🔧 Khởi tạo PDF Processor...")
        print(f"   Chunk size: {Config.CHUNK_SIZE}")
        print(f"   Chunk overlap: {Config.CHUNK_OVERLAP}")
        print(f"   Strategy: {Config.CHUNK_STRATEGY}")
        
        self._init_text_splitter()
    
    def _init_text_splitter(self):
        """
        Khởi tạo text splitter tối ưu cho tiếng Việt
        """
        if Config.CHUNK_STRATEGY == "recursive":
            # Tối ưu cho tiếng Việt - separators tùy chỉnh
            vietnamese_separators = [
                "\n\n",  # Paragraph breaks
                "\n",    # Line breaks  
                ". ",    # Sentence ends
                "! ",    # Exclamation
                "? ",    # Question
                "; ",    # Semicolon
                ", ",    # Comma
                " ",     # Space
                ""       # Character level
            ]
            
            self.text_splitter = RecursiveCharacterTextSplitter(
                separators=vietnamese_separators,
                chunk_size=Config.CHUNK_SIZE,
                chunk_overlap=Config.CHUNK_OVERLAP,
                length_function=len,
                is_separator_regex=False,
            )
        elif Config.CHUNK_STRATEGY == "semantic":
            # Semantic chunking - group by meaning
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=Config.CHUNK_SIZE,
                chunk_overlap=Config.CHUNK_OVERLAP,
                separators=["\n\n", "\n", ". ", "! ", "? "],
                length_function=len,
            )
        elif Config.CHUNK_STRATEGY == "token":
            # Token-based chunking
            self.text_splitter = TokenTextSplitter(
                chunk_size=Config.CHUNK_SIZE // 4,  # ~4 chars per token
                chunk_overlap=Config.CHUNK_OVERLAP // 4,
            )
        else:  # fixed
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=Config.CHUNK_SIZE,
                chunk_overlap=Config.CHUNK_OVERLAP,
            )
    
    def clean_vietnamese_text(self, text: str) -> str:
        """
        Làm sạch text tiếng Việt
        """
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove weird characters but keep Vietnamese
        text = re.sub(r'[^\w\sàáâãèéêìíîïòóôõöùúûüỳýđĐ.,!?;:\-\(\)\[\]\"\']+', ' ', text)
        
        # Remove multiple punctuation
        text = re.sub(r'([.!?]){2,}', r'\1', text)
        
        # Clean up spaces around punctuation
        text = re.sub(r'\s*([.!?;,:])\s*', r'\1 ', text)
        
        return text.strip()
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text từ PDF với error handling
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            # Clean Vietnamese text
                            cleaned_text = self.clean_vietnamese_text(page_text)
                            text += f"\n--- Trang {page_num + 1} ---\n{cleaned_text}\n"
                    except Exception as e:
                        print(f"   ⚠️  Lỗi đọc trang {page_num + 1}: {e}")
                        continue
                
                return text
                
        except Exception as e:
            raise Exception(f"Không thể đọc PDF {pdf_path}: {e}")
    
    def create_overlapping_chunks(self, texts: List[str], metadata: Dict) -> List[Dict]:
        """
        Tạo chunks với overlap thông minh cho context tốt hơn
        """
        chunks = []
        
        if Config.OVERLAP_METHOD == "sliding":
            # Sliding window overlap
            for i, text in enumerate(texts):
                chunk = {
                    "content": text,
                    "source": metadata["source"],
                    "chunk_id": i,
                    "total_chunks": len(texts),
                    "metadata": {
                        **metadata,
                        "chunk_method": "sliding_overlap",
                        "overlap_size": Config.CHUNK_OVERLAP
                    }
                }
                chunks.append(chunk)
                
        elif Config.OVERLAP_METHOD == "sentence":
            # Sentence-aware overlap
            for i, text in enumerate(texts):
                # Thêm context từ chunk trước và sau
                enhanced_text = text
                
                if i > 0 and len(texts[i-1]) > 0:
                    # Lấy 1-2 câu cuối từ chunk trước
                    prev_sentences = texts[i-1].split('. ')[-2:]
                    enhanced_text = '. '.join(prev_sentences) + '. ' + enhanced_text
                
                if i < len(texts) - 1 and len(texts[i+1]) > 0:
                    # Lấy 1-2 câu đầu từ chunk sau
                    next_sentences = texts[i+1].split('. ')[:2]
                    enhanced_text = enhanced_text + '. ' + '. '.join(next_sentences)
                
                chunk = {
                    "content": enhanced_text,
                    "source": metadata["source"],
                    "chunk_id": i,
                    "total_chunks": len(texts),
                    "metadata": {
                        **metadata,
                        "chunk_method": "sentence_overlap",
                        "enhanced": True
                    }
                }
                chunks.append(chunk)
                
        else:  # paragraph
            # Paragraph-aware overlap
            for i, text in enumerate(texts):
                chunk = {
                    "content": text,
                    "source": metadata["source"], 
                    "chunk_id": i,
                    "total_chunks": len(texts),
                    "metadata": {
                        **metadata,
                        "chunk_method": "paragraph_overlap"
                    }
                }
                chunks.append(chunk)
        
        return chunks
    
    def process_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Xử lý PDF thành chunks với metadata chi tiết
        """
        try:
            print(f"   📖 Extracting text từ PDF...")
            
            # Extract text
            full_text = self.extract_text_from_pdf(pdf_path)
            
            if not full_text.strip():
                print(f"   ❌ PDF rỗng hoặc không đọc được text")
                return []
            
            print(f"   📝 Text length: {len(full_text)} chars")
            
            # Split into chunks
            print(f"   ✂️  Chunking với strategy: {Config.CHUNK_STRATEGY}")
            texts = self.text_splitter.split_text(full_text)
            
            # Create metadata
            import os
            metadata = {
                "source": os.path.basename(pdf_path),
                "file_path": pdf_path,
                "file_size": os.path.getsize(pdf_path),
                "chunk_size": Config.CHUNK_SIZE,
                "chunk_overlap": Config.CHUNK_OVERLAP,
                "chunk_strategy": Config.CHUNK_STRATEGY,
                "overlap_method": Config.OVERLAP_METHOD,
                "total_chars": len(full_text)
            }
            
            # Create chunks with overlap
            chunks = self.create_overlapping_chunks(texts, metadata)
            
            print(f"   ✅ Tạo được {len(chunks)} chunks")
            
            # Quality check
            avg_chunk_size = sum(len(chunk["content"]) for chunk in chunks) / len(chunks)
            print(f"   📊 Average chunk size: {avg_chunk_size:.0f} chars")
            
            return chunks
            
        except Exception as e:
            print(f"   ❌ Lỗi xử lý PDF: {e}")
            return []
    
    def get_chunk_statistics(self, chunks: List[Dict]) -> Dict:
        """
        Thống kê về chunks để tune parameters
        """
        if not chunks:
            return {}
        
        chunk_sizes = [len(chunk["content"]) for chunk in chunks]
        
        stats = {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "chunk_size_std": (sum((x - sum(chunk_sizes)/len(chunk_sizes))**2 for x in chunk_sizes) / len(chunk_sizes))**0.5,
            "strategy_used": Config.CHUNK_STRATEGY,
            "overlap_used": Config.CHUNK_OVERLAP
        }
        
        return stats 