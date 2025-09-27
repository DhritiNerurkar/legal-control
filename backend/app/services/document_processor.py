import os
import hashlib
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
import uuid
from app.core.config import settings
from app.models.database import SessionLocal, DocumentStore
from app.services.anthropic_client import AnthropicClient

class DocumentProcessor:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=Settings(anonymized_telemetry=False)
        )

        try:
            self.collection = self.chroma_client.get_collection(
                name=settings.CHROMA_COLLECTION_NAME
            )
        except Exception:
            self.collection = self.chroma_client.create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )

        self.anthropic_client = AnthropicClient()

    async def process_documents_directory(self, directory_path: str = None) -> Dict[str, Any]:
        """Process all documents in the specified directory"""

        if directory_path is None:
            directory_path = settings.DOCUMENTS_PATH

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        processed_count = 0
        errors = []

        for filename in os.listdir(directory_path):
            if filename.endswith(('.txt', '.pdf', '.docx')):
                try:
                    file_path = os.path.join(directory_path, filename)
                    await self._process_single_document(file_path, filename)
                    processed_count += 1
                except Exception as e:
                    errors.append(f"Error processing {filename}: {str(e)}")

        return {
            "processed_count": processed_count,
            "errors": errors,
            "total_documents_in_vector_store": self.collection.count()
        }

    async def _process_single_document(self, file_path: str, filename: str):
        """Process a single document and add to vector store"""

        # Read document content
        content = self._read_document(file_path)
        if not content:
            return

        # Generate content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check if document already processed
        db = SessionLocal()
        try:
            existing_doc = db.query(DocumentStore).filter(
                DocumentStore.content_hash == content_hash
            ).first()

            if existing_doc:
                return  # Document already processed

            # Extract entity LEI from filename if possible
            entity_lei = self._extract_lei_from_filename(filename)

            # Determine document type
            doc_type = self._determine_document_type(filename, content)

            # Generate embeddings and store in ChromaDB
            vector_id = str(uuid.uuid4())

            # Split content into chunks for better retrieval
            chunks = self._chunk_document(content)

            # Create embeddings for each chunk
            documents = []
            metadatas = []
            ids = []

            for i, chunk in enumerate(chunks):
                chunk_id = f"{vector_id}_chunk_{i}"
                documents.append(chunk)
                metadatas.append({
                    "filename": filename,
                    "entity_lei": entity_lei,
                    "document_type": doc_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
                ids.append(chunk_id)

            # Add to ChromaDB
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            # Store metadata in SQL database
            doc_store = DocumentStore(
                id=vector_id,
                document_name=filename,
                document_path=file_path,
                entity_lei=entity_lei,
                document_type=doc_type,
                content_hash=content_hash,
                vector_id=vector_id
            )

            db.add(doc_store)
            db.commit()

        finally:
            db.close()

    def _read_document(self, file_path: str) -> str:
        """Read document content based on file type"""

        try:
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()

            # For now, only handle .txt files
            # In production, would add PDF and DOCX parsing
            return ""

        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            return ""

    def _extract_lei_from_filename(self, filename: str) -> str:
        """Extract LEI number from filename if present"""

        # Simple heuristic: look for 20-character alphanumeric strings
        import re
        lei_pattern = r'[A-Z0-9]{20}'
        matches = re.findall(lei_pattern, filename.upper())

        if matches:
            return matches[0]

        # Map common entity names to LEIs
        lei_mapping = {
            'goldman': 'LMPQFR1LHAW71HGQGA77',
            'bridgewater': '5493006MHB84DD0ZWV18',
            'jpmorgan': '7H6GLXDRUGQFU57RNE97',
            'man_group': 'MLKBWG1CBLZLWR7DYP07',
            'two_sigma': '549300DHLU1APW6NMU86'
        }

        filename_lower = filename.lower()
        for entity, lei in lei_mapping.items():
            if entity in filename_lower:
                return lei

        return ""

    def _determine_document_type(self, filename: str, content: str) -> str:
        """Determine document type based on filename and content"""

        filename_lower = filename.lower()
        content_lower = content.lower()

        if any(term in filename_lower for term in ['charter', 'certificate', 'incorporation']):
            return 'charter'
        elif any(term in filename_lower for term in ['bylaws', 'agreement']):
            return 'bylaws'
        elif any(term in filename_lower for term in ['opinion', 'legal']):
            return 'legal_opinion'
        elif any(term in content_lower for term in ['certificate of formation', 'articles of incorporation']):
            return 'charter'
        elif any(term in content_lower for term in ['partnership agreement', 'limited partnership']):
            return 'partnership_agreement'
        else:
            return 'organizational_document'

    def _chunk_document(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split document into overlapping chunks"""

        if len(content) <= chunk_size:
            return [content]

        chunks = []
        start = 0

        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]

            # Try to break at sentence boundary
            if end < len(content):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')

                break_point = max(last_period, last_newline)
                if break_point > start + chunk_size // 2:
                    chunk = content[start:break_point + 1]
                    end = break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap if end < len(content) else end

        return chunks

    async def get_entity_documents(self, lei_number: str) -> List[Dict[str, Any]]:
        """Retrieve documents for a specific entity"""

        # Query vector store for documents
        try:
            results = self.collection.query(
                where={"entity_lei": lei_number},
                n_results=50
            )

            documents = []
            for i, doc in enumerate(results['documents']):
                documents.append({
                    "content": doc,
                    "metadata": results['metadatas'][i],
                    "id": results['ids'][i]
                })

            return documents

        except Exception as e:
            print(f"Error querying documents for LEI {lei_number}: {str(e)}")
            return []

    async def search_documents(self, query: str, entity_lei: str = None, document_type: str = None, n_results: int = 10) -> List[Dict[str, Any]]:
        """Search documents using vector similarity"""

        where_clause = {}
        if entity_lei:
            where_clause["entity_lei"] = entity_lei
        if document_type:
            where_clause["document_type"] = document_type

        try:
            results = self.collection.query(
                query_texts=[query],
                where=where_clause if where_clause else None,
                n_results=n_results
            )

            documents = []
            for i in range(len(results['documents'][0])):
                documents.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None,
                    "id": results['ids'][0][i]
                })

            return documents

        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            return []

    async def analyze_authority(self, lei_number: str, products: List[str]) -> Dict[str, Any]:
        """Analyze authority provisions in organizational documents"""

        # Get relevant documents
        documents = await self.get_entity_documents(lei_number)

        if not documents:
            return {"error": "No organizational documents found"}

        # Search for authority-related content
        authority_queries = [
            "authority to enter into derivative transactions",
            "power to execute swap agreements",
            "ISDA master agreement authority",
            "derivative trading authorization",
            "investment powers and authority"
        ]

        relevant_content = []
        for query in authority_queries:
            results = await self.search_documents(query, lei_number, n_results=3)
            relevant_content.extend(results)

        # Use Claude to analyze the content
        content_text = "\n\n".join([doc["content"] for doc in relevant_content[:5]])  # Limit content

        try:
            analysis = await self.anthropic_client.analyze_document(content_text, "authority_analysis")

            return {
                "authority_provisions_found": len(relevant_content) > 0,
                "relevant_documents": [doc["metadata"]["filename"] for doc in relevant_content],
                "analysis": analysis,
                "products_requested": products
            }

        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}",
                "documents_found": len(documents),
                "relevant_content_found": len(relevant_content)
            }

    async def analyze_capacity(self, lei_number: str, jurisdiction: str, products: List[str]) -> Dict[str, Any]:
        """Analyze capacity limitations in organizational documents"""

        # Search for capacity-related content
        capacity_queries = [
            "investment restrictions",
            "capacity limitations",
            "ultra vires",
            "prohibited investments",
            "investment policy restrictions"
        ]

        relevant_content = []
        for query in capacity_queries:
            results = await self.search_documents(query, lei_number, n_results=3)
            relevant_content.extend(results)

        if not relevant_content:
            return {"analysis": "No capacity restrictions found in available documents"}

        # Analyze content for capacity issues
        content_text = "\n\n".join([doc["content"] for doc in relevant_content[:5]])

        try:
            analysis = await self.anthropic_client.analyze_document(content_text, "capacity_analysis")

            return {
                "capacity_restrictions_found": True,
                "relevant_documents": [doc["metadata"]["filename"] for doc in relevant_content],
                "analysis": analysis,
                "jurisdiction": jurisdiction,
                "products_requested": products
            }

        except Exception as e:
            return {
                "error": f"Capacity analysis failed: {str(e)}",
                "relevant_content_found": len(relevant_content)
            }