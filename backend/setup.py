#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path

def setup_backend():
    """Setup the backend environment"""

    print("🚀 Setting up Legal Entity Due Diligence Backend...")

    # Create directories
    directories = [
        "data/documents",
        "data/synthetic",
        "chroma_db",
        "logs"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

    # Copy .env file if it doesn't exist
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ Created .env file from .env.example")
            print("⚠️  Please edit .env file and add your ANTHROPIC_API_KEY")
        else:
            print("❌ .env.example not found")

    # Load synthetic data
    try:
        from app.services.data_loader import load_synthetic_data
        load_synthetic_data()
        print("✅ Loaded synthetic data")
    except Exception as e:
        print(f"❌ Failed to load synthetic data: {e}")

    # Process documents
    try:
        from app.services.document_processor import DocumentProcessor
        import asyncio

        async def process_docs():
            processor = DocumentProcessor()
            result = await processor.process_documents_directory()
            print(f"✅ Processed {result['processed_count']} documents")
            if result['errors']:
                for error in result['errors']:
                    print(f"⚠️  Document processing error: {error}")

        asyncio.run(process_docs())
    except Exception as e:
        print(f"⚠️  Document processing setup will be done at runtime: {e}")

    print("\n🎉 Backend setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file and add your ANTHROPIC_API_KEY")
    print("2. Install requirements: pip install -r requirements.txt")
    print("3. Run the server: uvicorn app.main:app --reload")

if __name__ == "__main__":
    setup_backend()