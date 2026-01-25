# M4 - 文档处理任务规格书

## 概述
| 属性 | 值 |
|------|-----|
| 里程碑 | M4 - Document Processing |
| 周期 | Week 5-6 |
| 任务总数 | 10 |
| Opus 4.5 任务 | 2 |
| Mini-Agent 任务 | 8 |

## 目标
- 实现PDF/DOCX文档解析
- 建立向量存储和检索
- 实现文档上传和管理

---

## 任务列表

### M4-01: 文档处理架构设计 (Opus 4.5)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Opus 4.5

#### 描述
设计文档处理流水线架构。

#### 架构图
```
┌─────────────────────────────────────────────────────────────┐
│                  Document Processing Pipeline               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Upload ──▶ Validate ──▶ Store ──▶ Parse ──▶ Chunk ──▶ Embed│
│    │           │           │         │         │         │  │
│    ▼           ▼           ▼         ▼         ▼         ▼  │
│  ┌───┐     ┌───┐      ┌───┐     ┌───┐    ┌───┐     ┌───┐  │
│  │API│     │Pyd│      │S3 │     │PDF│    │Txt│     │Vec│  │
│  │   │     │tic│      │Min│     │Lib│    │Spl│     │tor│  │
│  └───┘     └───┘      └───┘     └───┘    └───┘     └───┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Async Task Queue                   │   │
│  │                      (Celery)                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                     Storage                          │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────────────────┐  │   │
│  │  │ MinIO   │  │PostgreSQL│  │  pgvector           │  │   │
│  │  │ (files) │  │(metadata)│  │  (embeddings)       │  │   │
│  │  └─────────┘  └─────────┘  └─────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### 验收标准
- [ ] 架构文档完成
- [ ] 处理流程明确
- [ ] 错误处理策略
- [ ] 性能考量

#### 输出文件
- `docs/document-processing-design.md`

#### 依赖
无

---

### M4-02: 文档数据模型 (Mini-Agent)
**优先级**: P0  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
创建文档和向量相关数据模型。

#### 输出文件
- `backend/app/models/document.py`
- `backend/app/models/embedding.py`

#### 模型代码
```python
# app/models/document.py
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import uuid

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    # 文档信息
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # tor, rfp, cv, etc.
    
    # 文件存储
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # 解析内容
    parsed_content = Column(Text)
    parse_status = Column(String(20), default="pending")
    parse_error = Column(Text)
    
    # 元数据
    metadata = Column(JSONB, default={})
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    project = relationship("Project", back_populates="documents")
    embeddings = relationship("Embedding", back_populates="document", cascade="all, delete-orphan")


# app/models/embedding.py
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.base import Base
import uuid

class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # 分块信息
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    
    # 向量 (1536维)
    vector = Column(Vector(1536))
    
    # 元数据
    metadata = Column(JSONB, default={})
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    document = relationship("Document", back_populates="embeddings")
```

#### 依赖
- M0-06

---

### M4-03: 文件存储服务 (Mini-Agent)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现MinIO文件存储服务。

#### 验收标准
- [ ] 文件上传
- [ ] 文件下载
- [ ] 预签名URL
- [ ] 文件删除

#### 代码实现
```python
# app/services/storage_service.py
from minio import Minio
from minio.error import S3Error
from datetime import timedelta
from io import BytesIO
from app.config import settings
from app.core.logging import logger

class StorageService:
    """MinIO文件存储服务"""
    
    BUCKET_NAME = "bidagent-documents"
    
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保bucket存在"""
        if not self.client.bucket_exists(self.BUCKET_NAME):
            self.client.make_bucket(self.BUCKET_NAME)
    
    async def upload(
        self,
        file_data: bytes,
        file_name: str,
        content_type: str = "application/octet-stream",
        folder: str = ""
    ) -> str:
        """上传文件"""
        import uuid
        
        # 生成唯一路径
        ext = file_name.split(".")[-1] if "." in file_name else ""
        object_name = f"{folder}/{uuid.uuid4()}.{ext}".lstrip("/")
        
        try:
            self.client.put_object(
                self.BUCKET_NAME,
                object_name,
                BytesIO(file_data),
                length=len(file_data),
                content_type=content_type,
            )
            logger.info(f"Uploaded file: {object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"Upload failed: {e}")
            raise
    
    async def download(self, object_name: str) -> bytes:
        """下载文件"""
        try:
            response = self.client.get_object(self.BUCKET_NAME, object_name)
            return response.read()
        finally:
            response.close()
            response.release_conn()
    
    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        """获取预签名下载URL"""
        return self.client.presigned_get_object(
            self.BUCKET_NAME,
            object_name,
            expires=timedelta(seconds=expires),
        )
    
    async def delete(self, object_name: str):
        """删除文件"""
        self.client.remove_object(self.BUCKET_NAME, object_name)

storage_service = StorageService()
```

#### 依赖
- M0-04 (MinIO)

---

### M4-04: PDF解析器 (Mini-Agent)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
实现PDF文档解析，提取文本内容。

#### 验收标准
- [ ] 提取PDF文本
- [ ] 保留基本格式
- [ ] 处理扫描PDF（OCR）
- [ ] 提取元数据

#### 代码实现
```python
# app/utils/pdf_parser.py
from typing import Dict, Any
import fitz  # PyMuPDF
from app.core.logging import logger

class PDFParser:
    """PDF解析器"""
    
    @staticmethod
    def parse(file_data: bytes) -> Dict[str, Any]:
        """解析PDF文件"""
        doc = fitz.open(stream=file_data, filetype="pdf")
        
        try:
            pages = []
            full_text = []
            
            for page_num, page in enumerate(doc):
                text = page.get_text("text")
                pages.append({
                    "page": page_num + 1,
                    "text": text,
                })
                full_text.append(text)
            
            metadata = {
                "page_count": len(doc),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "creator": doc.metadata.get("creator", ""),
                "creation_date": doc.metadata.get("creationDate", ""),
            }
            
            return {
                "text": "\n\n".join(full_text),
                "pages": pages,
                "metadata": metadata,
            }
        finally:
            doc.close()
    
    @staticmethod
    def parse_with_ocr(file_data: bytes) -> Dict[str, Any]:
        """使用OCR解析扫描PDF"""
        import pytesseract
        from PIL import Image
        import io
        
        doc = fitz.open(stream=file_data, filetype="pdf")
        full_text = []
        
        try:
            for page in doc:
                # 渲染为图像
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                
                # OCR
                text = pytesseract.image_to_string(img)
                full_text.append(text)
            
            return {
                "text": "\n\n".join(full_text),
                "metadata": {"page_count": len(doc), "ocr": True},
            }
        finally:
            doc.close()


# app/utils/docx_parser.py
from docx import Document as DocxDocument
from typing import Dict, Any

class DocxParser:
    """DOCX解析器"""
    
    @staticmethod
    def parse(file_data: bytes) -> Dict[str, Any]:
        """解析DOCX文件"""
        import io
        doc = DocxDocument(io.BytesIO(file_data))
        
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)
        
        # 提取表格
        tables = []
        for table in doc.tables:
            table_data = []
            for row in table.rows:
                row_data = [cell.text for cell in row.cells]
                table_data.append(row_data)
            tables.append(table_data)
        
        return {
            "text": "\n\n".join(paragraphs),
            "tables": tables,
            "metadata": {
                "paragraph_count": len(paragraphs),
                "table_count": len(tables),
            },
        }
```

#### 依赖库
```
PyMuPDF==1.24.0
python-docx==1.1.0
pytesseract==0.3.10
Pillow==10.2.0
```

#### 依赖
- M4-01

---

### M4-05: 文本分块 (Mini-Agent)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现文档文本分块策略。

#### 验收标准
- [ ] 按语义分块
- [ ] 控制块大小
- [ ] 保留上下文重叠
- [ ] 支持多种策略

#### 代码实现
```python
# app/utils/text_splitter.py
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken

class TextSplitter:
    """文本分块器"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        encoding_name: str = "cl100k_base"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self._token_length,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
    
    def _token_length(self, text: str) -> int:
        """计算token数量"""
        return len(self.encoding.encode(text))
    
    def split(self, text: str) -> List[Dict[str, Any]]:
        """分块文本"""
        chunks = self.splitter.split_text(text)
        
        return [
            {
                "index": i,
                "content": chunk,
                "token_count": self._token_length(chunk),
            }
            for i, chunk in enumerate(chunks)
        ]
    
    def split_with_metadata(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """分块并附加元数据"""
        chunks = self.split(text)
        
        for chunk in chunks:
            chunk["metadata"] = {
                **(metadata or {}),
                "chunk_index": chunk["index"],
                "token_count": chunk["token_count"],
            }
        
        return chunks

text_splitter = TextSplitter()
```

#### 依赖
- M4-04

---

### M4-06: 向量嵌入服务 (Opus 4.5)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Opus 4.5

#### 描述
实现文本向量化和存储服务。

#### 验收标准
- [ ] 文本向量化
- [ ] 批量处理
- [ ] 向量存储
- [ ] 相似度搜索

#### 代码实现
```python
# app/services/embedding_service.py
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from openai import AsyncOpenAI
from app.models.embedding import Embedding
from app.config import settings
from app.core.logging import logger

class EmbeddingService:
    """向量嵌入服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1",
        )
    
    async def embed_text(self, text: str) -> List[float]:
        """将文本转换为向量"""
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",  # 或使用其他模型
            input=text,
        )
        return response.data[0].embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量向量化"""
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        return [item.embedding for item in response.data]
    
    async def store_embeddings(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]]
    ):
        """存储文档向量"""
        # 批量生成向量
        texts = [c["content"] for c in chunks]
        vectors = await self.embed_batch(texts)
        
        # 存储
        for chunk, vector in zip(chunks, vectors):
            embedding = Embedding(
                document_id=document_id,
                chunk_index=chunk["index"],
                content=chunk["content"],
                vector=vector,
                metadata=chunk.get("metadata", {}),
            )
            self.db.add(embedding)
        
        await self.db.commit()
        logger.info(f"Stored {len(chunks)} embeddings for document {document_id}")
    
    async def similarity_search(
        self,
        query: str,
        project_id: str = None,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """相似度搜索"""
        # 生成查询向量
        query_vector = await self.embed_text(query)
        
        # 构建SQL
        sql = text("""
            SELECT 
                e.id,
                e.content,
                e.metadata,
                d.id as document_id,
                d.name as document_name,
                d.type as document_type,
                1 - (e.vector <=> :query_vector::vector) as similarity
            FROM embeddings e
            JOIN documents d ON e.document_id = d.id
            WHERE d.project_id = :project_id
            AND 1 - (e.vector <=> :query_vector::vector) > :threshold
            ORDER BY e.vector <=> :query_vector::vector
            LIMIT :limit
        """)
        
        result = await self.db.execute(sql, {
            "query_vector": str(query_vector),
            "project_id": project_id,
            "threshold": threshold,
            "limit": limit,
        })
        
        return [
            {
                "id": str(row.id),
                "content": row.content,
                "metadata": row.metadata,
                "document_id": str(row.document_id),
                "document_name": row.document_name,
                "document_type": row.document_type,
                "similarity": float(row.similarity),
            }
            for row in result.fetchall()
        ]
```

#### 依赖
- M4-02, M4-05, M0-04 (pgvector)

---

### M4-07: 文档上传API (Mini-Agent)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现文档上传接口。

#### 验收标准
- [ ] 文件上传
- [ ] 文件类型验证
- [ ] 大小限制
- [ ] 异步解析任务

#### API实现
```python
# app/api/v1/documents.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document
from app.services.storage_service import storage_service
from app.tasks.document_tasks import process_document
from app.api.deps import get_db, get_current_user

router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

@router.post("")
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    doc_type: str = Form(...),  # tor, rfp, cv, etc.
    name: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """上传文档"""
    # 验证文件类型
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "不支持的文件类型")
    
    # 读取文件
    content = await file.read()
    
    # 验证文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "文件大小超过限制")
    
    # 上传到存储
    file_path = await storage_service.upload(
        content,
        file.filename,
        file.content_type,
        folder=f"projects/{project_id}",
    )
    
    # 创建文档记录
    document = Document(
        project_id=project_id,
        name=name or file.filename,
        type=doc_type,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
        parse_status="pending",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # 触发异步解析任务
    process_document.delay(str(document.id))
    
    return document
```

#### 依赖
- M4-03, M1-02

---

### M4-08: 文档处理任务 (Mini-Agent)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
实现文档解析的Celery异步任务。

#### 验收标准
- [ ] 自动触发解析
- [ ] 更新解析状态
- [ ] 错误处理
- [ ] 向量化存储

#### 代码实现
```python
# app/tasks/document_tasks.py
from app.celery_app import celery_app
from app.db.session import async_session
from app.services.storage_service import storage_service
from app.services.embedding_service import EmbeddingService
from app.utils.pdf_parser import PDFParser
from app.utils.docx_parser import DocxParser
from app.utils.text_splitter import text_splitter
from app.models.document import Document
from app.core.logging import logger
import asyncio

@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: str):
    """处理文档任务"""
    asyncio.run(_process_document_async(document_id))

async def _process_document_async(document_id: str):
    async with async_session() as db:
        # 获取文档
        document = await db.get(Document, document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return
        
        try:
            # 更新状态
            document.parse_status = "processing"
            await db.commit()
            
            # 下载文件
            file_data = await storage_service.download(document.file_path)
            
            # 解析
            if document.mime_type == "application/pdf":
                result = PDFParser.parse(file_data)
            elif "wordprocessing" in document.mime_type:
                result = DocxParser.parse(file_data)
            else:
                result = {"text": file_data.decode("utf-8")}
            
            # 保存解析内容
            document.parsed_content = result["text"]
            document.metadata = result.get("metadata", {})
            
            # 分块
            chunks = text_splitter.split_with_metadata(
                result["text"],
                metadata={"document_id": document_id}
            )
            
            # 向量化存储
            embedding_service = EmbeddingService(db)
            await embedding_service.store_embeddings(document_id, chunks)
            
            # 更新状态
            document.parse_status = "completed"
            await db.commit()
            
            logger.info(f"Document processed: {document_id}")
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            document.parse_status = "failed"
            document.parse_error = str(e)
            await db.commit()
            raise
```

#### 依赖
- M4-04, M4-05, M4-06

---

### M4-09: 文档管理API (Mini-Agent)
**优先级**: P1  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现文档列表、详情、删除等API。

#### 验收标准
- [ ] GET /documents 列表
- [ ] GET /documents/{id} 详情
- [ ] DELETE /documents/{id} 删除
- [ ] GET /documents/{id}/download 下载

#### 依赖
- M4-07

---

### M4-10: 语义搜索API (Mini-Agent)
**优先级**: P1  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
实现基于向量的语义搜索API。

#### 验收标准
- [ ] POST /projects/{id}/search
- [ ] 返回相关文档片段
- [ ] 支持相似度阈值
- [ ] 支持结果数量限制

#### 依赖
- M4-06

---

## 里程碑检查点

### 完成标准
- [ ] 文档可上传存储
- [ ] PDF/DOCX可解析
- [ ] 向量检索可用
- [ ] 异步任务正常

### 交付物
1. 文档处理流水线
2. 向量存储服务
3. 文档管理API
4. 语义搜索功能
