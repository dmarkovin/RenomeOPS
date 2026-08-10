from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.database.models import Document

async def create_document(
    name: str,
    doc_type: str,
    number: str = "",
    sender: str = "",
    recipient: str = "",
    comment: str = "",
    photo_ids: List[str] = None,
    created_by: int = None
) -> Document:
    async with AsyncSessionLocal() as db:
        doc = Document(
            name=name,
            doc_type=doc_type,
            number=number or None,
            sender=sender or None,
            recipient=recipient or None,
            comment=comment or "",
            photo_ids=photo_ids or [],
            created_by=created_by,
            status="active"
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

async def get_document(doc_id: int) -> Optional[Document]:
    async with AsyncSessionLocal() as db:
        return await db.get(Document, doc_id)

async def get_documents(
    doc_type: str = None,
    status: str = None,
    limit: int = 20,
    offset: int = 0
) -> List[Document]:
    async with AsyncSessionLocal() as db:
        query = select(Document).order_by(Document.created_at.desc())
        if doc_type:
            query = query.where(Document.doc_type == doc_type)
        if status:
            query = query.where(Document.status == status)
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()

async def update_document_status(doc_id: int, status: str) -> Optional[Document]:
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if not doc:
            return None
        doc.status = status
        doc.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(doc)
        return doc

async def delete_document(doc_id: int) -> bool:
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if not doc:
            return False
        await db.delete(doc)
        await db.commit()
        return True
