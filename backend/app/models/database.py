from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = "sqlite:///./legal_capacity.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Entity(Base):
    __tablename__ = "entities"

    lei_number = Column(String, primary_key=True, index=True)
    legal_name = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    jurisdiction = Column(String, nullable=False)
    incorporation_date = Column(DateTime)
    regulatory_status = Column(String)
    website = Column(String)
    business_description = Column(Text)
    authorized_products = Column(JSON)
    capacity_limitations = Column(JSON)
    regulatory_body = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LegalOpinion(Base):
    __tablename__ = "legal_opinions"

    id = Column(String, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)
    jurisdiction = Column(String, nullable=False)
    product = Column(String, nullable=False)
    opinion_available = Column(Boolean, default=False)
    opinion_provider = Column(String)
    opinion_date = Column(DateTime)
    netting_enforceability = Column(String)
    close_out_netting = Column(String)
    opinion_summary = Column(Text)
    limitations = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class DueDiligenceCheck(Base):
    __tablename__ = "due_diligence_checks"

    id = Column(String, primary_key=True, index=True)
    lei_number = Column(String, nullable=False)
    legal_name = Column(String, nullable=False)
    products = Column(JSON, nullable=False)
    status = Column(String, default="pending")  # pending, in_progress, completed, failed

    # 5-point check results
    entity_classification_result = Column(JSON)
    jurisdiction_result = Column(JSON)
    authority_result = Column(JSON)
    capacity_result = Column(JSON)
    legal_opinion_result = Column(JSON)

    # Additional metadata
    sources_checked = Column(JSON)
    evidence_documents = Column(JSON)
    risk_assessment = Column(String)
    recommendations = Column(Text)

    # Admin logs for debugging and inference
    admin_logs = Column(JSON)  # Store prompts and AI responses for each step

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

class DocumentStore(Base):
    __tablename__ = "document_store"

    id = Column(String, primary_key=True, index=True)
    document_name = Column(String, nullable=False)
    document_path = Column(String, nullable=False)
    entity_lei = Column(String)
    document_type = Column(String)  # charter, bylaws, opinion, regulatory_filing
    content_hash = Column(String)
    vector_id = Column(String)  # Reference to ChromaDB
    created_at = Column(DateTime, default=datetime.utcnow)

def create_tables():
    import sqlite3
    import logging
    logger = logging.getLogger(__name__)

    Base.metadata.create_all(bind=engine)

    # Handle database migration for new admin_logs column
    try:
        # Connect directly to SQLite to add the missing column
        conn = sqlite3.connect("./legal_capacity.db")
        cursor = conn.cursor()

        # Check if admin_logs column exists
        cursor.execute("PRAGMA table_info(due_diligence_checks)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'admin_logs' not in columns:
            logger.info("Adding admin_logs column to due_diligence_checks table")
            cursor.execute("ALTER TABLE due_diligence_checks ADD COLUMN admin_logs TEXT")
            conn.commit()
            logger.info("Successfully added admin_logs column")
        else:
            logger.info("admin_logs column already exists")

        conn.close()

    except Exception as e:
        logger.error(f"Error during database migration: {e}")
        # Don't raise the error, just log it

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()