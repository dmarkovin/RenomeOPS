from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, or_
from app.database import AsyncSessionLocal
from app.database.models import Document

async def create_document(
    doc_type: str,
    number: str,
    title: str,
    recipient: str = None,
    sender: str = None,
    storage_location: str = None,
    issued_to: str = None,
    comment: str = "",
    created_by: int = None,
) -> Document:
    async with AsyncSessionLocal() as db:
        doc = Document(
            doc_type=doc_type,
            number=number,
            title=title,
            recipient=recipient,
            sender=sender,
            storage_location=storage_location,
            issued_to=issued_to,
            comment=comment,
            created_by=created_by,
            status="active"
        )
        if doc_type == "issued" and issued_to:
            doc.issued_at = datetime.utcnow()
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

async def get_document(doc_id: int) -> Optional[Document]:
    async with AsyncSessionLocal() as db:
        return await db.get(Document, doc_id)

async def get_documents(
    doc_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
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

async def return_document(doc_id: int) -> Optional[Document]:
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if not doc or doc.doc_type != "issued" or doc.status != "active":
            return None
        doc.status = "returned"
        doc.returned_at = datetime.utcnow()
        doc.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(doc)
        return doc

async def archive_document(doc_id: int) -> Optional[Document]:
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if not doc:
            return None
        doc.status = "archived"
        doc.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(doc)
        return doc
