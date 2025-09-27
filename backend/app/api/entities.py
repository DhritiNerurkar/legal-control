from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db, Entity
from app.models.schemas import EntityInfo
from typing import List, Optional

router = APIRouter()

@router.get("/{lei_number}", response_model=EntityInfo)
async def get_entity(lei_number: str, db: Session = Depends(get_db)):
    """Get entity information by LEI number"""

    db_entity = db.query(Entity).filter(Entity.lei_number == lei_number).first()
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    return EntityInfo(
        lei_number=db_entity.lei_number,
        legal_name=db_entity.legal_name,
        entity_type=db_entity.entity_type,
        jurisdiction=db_entity.jurisdiction,
        incorporation_date=db_entity.incorporation_date,
        regulatory_status=db_entity.regulatory_status,
        website=db_entity.website,
        business_description=db_entity.business_description,
        authorized_products=db_entity.authorized_products or [],
        capacity_limitations=db_entity.capacity_limitations or [],
        regulatory_body=db_entity.regulatory_body
    )

@router.get("/", response_model=List[EntityInfo])
async def search_entities(
    name: Optional[str] = None,
    entity_type: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search entities with optional filters"""

    query = db.query(Entity)

    if name:
        query = query.filter(Entity.legal_name.contains(name))
    if entity_type:
        query = query.filter(Entity.entity_type == entity_type)
    if jurisdiction:
        query = query.filter(Entity.jurisdiction.contains(jurisdiction))

    entities = query.offset(skip).limit(limit).all()

    return [
        EntityInfo(
            lei_number=entity.lei_number,
            legal_name=entity.legal_name,
            entity_type=entity.entity_type,
            jurisdiction=entity.jurisdiction,
            incorporation_date=entity.incorporation_date,
            regulatory_status=entity.regulatory_status,
            website=entity.website,
            business_description=entity.business_description,
            authorized_products=entity.authorized_products or [],
            capacity_limitations=entity.capacity_limitations or [],
            regulatory_body=entity.regulatory_body
        )
        for entity in entities
    ]