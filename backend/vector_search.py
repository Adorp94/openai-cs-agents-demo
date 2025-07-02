"""
Vector search setup and management for promotional products.
Implements proper OpenAI vector stores for fuzzy/semantic search.
"""

import pandas as pd
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manages OpenAI vector stores for promotional products search."""
    
    def __init__(self):
        self.client = OpenAI()
        self.promo_vector_store_id: Optional[str] = None
        self.suitup_vector_store_id: Optional[str] = None
        
    def csv_to_jsonl(self, csv_path: str, jsonl_path: str, product_type: str) -> None:
        """Convert CSV to JSONL format for vector store ingestion."""
        df = pd.read_csv(csv_path)
        
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for _, row in df.iterrows():
                if product_type == "promo":
                    # Format promotional products
                    doc = {
                        "text": f"Producto: {row.get('nombre', '')} - {row.get('descripcion', '')} - Categoría: {row.get('categorias', '')} - Precio: {row.get('precio', '')} - SKU: {row.get('sku', '')}",
                        "metadata": {
                            "sku": str(row.get('sku', '')),
                            "nombre": str(row.get('nombre', '')),
                            "descripcion": str(row.get('descripcion', '')),
                            "categorias": str(row.get('categorias', '')),
                            "precio": str(row.get('precio', '')),
                            "imagenes_url": str(row.get('imagenes_url', '')),
                            "type": "promotional_product"
                        }
                    }
                else:
                    # Format kits
                    doc = {
                        "text": f"Kit: {row.get('nombre', '')} - {row.get('descripcion', '')} - Productos incluidos: {row.get('productos', '')} - Precio: {row.get('precio', '')}",
                        "metadata": {
                            "nombre": str(row.get('nombre', '')),
                            "descripcion": str(row.get('descripcion', '')),
                            "productos": str(row.get('productos', '')),
                            "precio": str(row.get('precio', '')),
                            "imagen": str(row.get('imagen', '')),
                            "type": "promotional_kit"
                        }
                    }
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')
        
        logger.info(f"Converted {len(df)} rows to {jsonl_path}")
    
    def create_vector_store(self, name: str, jsonl_path: str) -> str:
        """Create a vector store and upload the JSONL file."""
        try:
            # Try new API first, fall back to old API
            try:
                # New API (as of 2024)
                vector_store = self.client.vector_stores.create(name=name)
                logger.info(f"Created vector store (new API): {vector_store.id}")
                
                # Upload file
                with open(jsonl_path, 'rb') as f:
                    file_response = self.client.files.create(
                        file=f,
                        purpose='assistants'
                    )
                logger.info(f"Uploaded file: {file_response.id}")
                
                # Add file to vector store
                self.client.vector_stores.files.create(
                    vector_store_id=vector_store.id,
                    file_id=file_response.id
                )
                logger.info(f"File added to vector store: {vector_store.id}")
                
            except AttributeError:
                # Fall back to beta API
                vector_store = self.client.beta.vector_stores.create(name=name)
                logger.info(f"Created vector store (beta API): {vector_store.id}")
                
                # Upload file
                with open(jsonl_path, 'rb') as f:
                    file_response = self.client.files.create(
                        file=f,
                        purpose='assistants'
                    )
                logger.info(f"Uploaded file: {file_response.id}")
                
                # Add file to vector store
                self.client.beta.vector_stores.files.create(
                    vector_store_id=vector_store.id,
                    file_id=file_response.id
                )
                logger.info(f"File added to vector store: {vector_store.id}")
            
            # Wait for processing (in production, you'd want to poll this)
            import time
            time.sleep(5)  # Give it a moment to process
            
            return vector_store.id
            
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            raise
    
    def setup_vector_stores(self, force_recreate: bool = False) -> tuple[str, str]:
        """Set up vector stores for promo and suitup catalogs."""
        current_dir = Path(__file__).parent
        data_dir = current_dir / "../data"
        
        promo_csv = data_dir / "promo.csv"
        suitup_csv = data_dir / "suitup.csv"
        
        promo_jsonl = current_dir / "promo_products.jsonl"
        suitup_jsonl = current_dir / "suitup_kits.jsonl"
        
        # Convert CSVs to JSONL
        if force_recreate or not promo_jsonl.exists():
            self.csv_to_jsonl(str(promo_csv), str(promo_jsonl), "promo")
        
        if force_recreate or not suitup_jsonl.exists():
            self.csv_to_jsonl(str(suitup_csv), str(suitup_jsonl), "suitup")
        
        # Create vector stores
        if force_recreate or not self.promo_vector_store_id:
            self.promo_vector_store_id = self.create_vector_store(
                "Promotional Products",
                str(promo_jsonl)
            )
        
        if force_recreate or not self.suitup_vector_store_id:
            self.suitup_vector_store_id = self.create_vector_store(
                "Promotional Kits",
                str(suitup_jsonl)
            )
        
        return self.promo_vector_store_id, self.suitup_vector_store_id
    
    def search_vector_store(self, vector_store_id: str, query: str, limit: int = 5) -> List[Dict]:
        """Search a vector store and return structured results."""
        try:
            # Note: This is a simplified search. In practice, you'd use the FileSearchTool
            # or implement proper vector search via the assistants API
            response = self.client.beta.vector_stores.files.list(
                vector_store_id=vector_store_id,
                limit=limit
            )
            
            # This is a placeholder - actual vector search would be implemented
            # via the FileSearchTool or assistants API with proper semantic search
            logger.info(f"Vector store search for: {query}")
            return []
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

# Global instance
vector_manager = VectorStoreManager() 