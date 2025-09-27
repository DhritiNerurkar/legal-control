import json
import pandas as pd
from datetime import datetime
from app.models.database import SessionLocal, Entity, LegalOpinion, create_tables
import os

def load_synthetic_data():
    """Load synthetic data into the database"""

    # Create tables if they don't exist
    create_tables()

    db = SessionLocal()
    try:
        # Load entities data
        entities_file = "data/synthetic/entities_sample.json"
        if os.path.exists(entities_file):
            with open(entities_file, 'r') as f:
                entities_data = json.load(f)

            for entity_data in entities_data:
                # Check if entity already exists
                existing_entity = db.query(Entity).filter(
                    Entity.lei_number == entity_data['lei_number']
                ).first()

                if not existing_entity:
                    entity = Entity(
                        lei_number=entity_data['lei_number'],
                        legal_name=entity_data['legal_name'],
                        entity_type=entity_data['entity_type'],
                        jurisdiction=entity_data['jurisdiction'],
                        incorporation_date=datetime.fromisoformat(entity_data['incorporation_date']),
                        regulatory_status=entity_data['regulatory_status'],
                        website=entity_data['website'],
                        business_description=entity_data['business_description'],
                        authorized_products=entity_data['authorized_products'],
                        capacity_limitations=entity_data['capacity_limitations'],
                        regulatory_body=entity_data['regulatory_body']
                    )
                    db.add(entity)

        # Load legal opinions data
        opinions_file = "data/synthetic/legal_opinions.json"
        if os.path.exists(opinions_file):
            with open(opinions_file, 'r') as f:
                opinions_data = json.load(f)

            for opinion_data in opinions_data:
                # Check if opinion already exists
                existing_opinion = db.query(LegalOpinion).filter(
                    LegalOpinion.id == opinion_data['id']
                ).first()

                if not existing_opinion:
                    opinion_date = None
                    if opinion_data['opinion_date']:
                        opinion_date = datetime.fromisoformat(opinion_data['opinion_date'])

                    opinion = LegalOpinion(
                        id=opinion_data['id'],
                        entity_type=opinion_data['entity_type'],
                        jurisdiction=opinion_data['jurisdiction'],
                        product=opinion_data['product'],
                        opinion_available=opinion_data['opinion_available'],
                        opinion_provider=opinion_data['opinion_provider'],
                        opinion_date=opinion_date,
                        netting_enforceability=opinion_data['netting_enforceability'],
                        close_out_netting=opinion_data['close_out_netting'],
                        opinion_summary=opinion_data['opinion_summary'],
                        limitations=opinion_data['limitations']
                    )
                    db.add(opinion)

        db.commit()
        print("Synthetic data loaded successfully")

    except Exception as e:
        print(f"Error loading synthetic data: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    load_synthetic_data()