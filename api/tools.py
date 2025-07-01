"""
Advanced search tools for promotional products using precise + fuzzy search strategy.
"""

import pandas as pd
import pathlib
import os
import logging
from typing import List, Dict
from agents import function_tool, FileSearchTool
from openai import OpenAI
from vector_search import vector_manager

logger = logging.getLogger(__name__)

# Load CSV files into memory on module import (fast access)
current_dir = pathlib.Path(__file__).parent
PROMO_CSV_PATH = os.getenv("PROMO_CSV_PATH", str(current_dir / "../data/promo.csv"))
SUITUP_CSV_PATH = os.getenv("SUITUP_CSV_PATH", str(current_dir / "../data/suitup.csv"))

# Load DataFrames with error handling
try:
    PROMO_CATALOG = pd.read_csv(PROMO_CSV_PATH)
    # Clean and convert price column
    PROMO_CATALOG["price_numeric"] = (
        PROMO_CATALOG["precio"].astype(str).str.replace(r"[^\d.]", "", regex=True).astype(float)
    )
    logger.info(f"Loaded {len(PROMO_CATALOG)} promotional products")
except Exception as e:
    logger.error(f"Failed to load promo catalog: {e}")
    PROMO_CATALOG = pd.DataFrame()

try:
    SUITUP_CATALOG = pd.read_csv(SUITUP_CSV_PATH)
    # Clean and convert price column  
    SUITUP_CATALOG["price_numeric"] = (
        SUITUP_CATALOG["precio"].astype(str).str.replace(r"[^\d.]", "", regex=True).astype(float)
    )
    logger.info(f"Loaded {len(SUITUP_CATALOG)} promotional kits")
except Exception as e:
    logger.error(f"Failed to load suitup catalog: {e}")
    SUITUP_CATALOG = pd.DataFrame()

# ============================
# PRECISE SEARCH TOOLS (Primary)
# ============================

@function_tool(
    name_override="find_promo_products",
    description_override="Search promotional products precisely by keyword, category, and price range. Use this FIRST for specific product searches."
)
def find_promo_products(
    keyword: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    limit: int = 6,
) -> List[Dict]:
    """
    Search the promotional products catalog with precise filters.
    
    Args:
        keyword: Search in product name and description
        category: Filter by category (case-insensitive)
        min_price: Minimum price in MXN
        max_price: Maximum price in MXN
        limit: Maximum number of results
        
    Returns:
        List of matching products
    """
    if PROMO_CATALOG.empty:
        return []
        
    df = PROMO_CATALOG.copy()

    # Apply filters
    if keyword:
        mask = (
            df["nombre"].str.contains(keyword, case=False, na=False) |
            df["descripcion"].str.contains(keyword, case=False, na=False)
        )
        df = df[mask]

    if category:
        df = df[df["categorias"].str.contains(category, case=False, na=False)]

    if min_price is not None:
        df = df[df["price_numeric"] >= min_price]
        
    if max_price is not None:
        df = df[df["price_numeric"] <= max_price]

    # Return results
    cols = ["sku", "nombre", "categorias", "precio", "descripcion", "imagenes_url"]
    available_cols = [col for col in cols if col in df.columns]
    
    results = df[available_cols].head(limit).to_dict(orient="records")
    logger.info(f"Precise search returned {len(results)} products for query: {keyword}, category: {category}, price: {min_price}-{max_price}")
    
    return results

@function_tool(
    name_override="find_suitup_kits",
    description_override="Search promotional kits precisely by keyword, and price range. Use this FIRST for specific kit searches."
)
def find_suitup_kits(
    keyword: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    limit: int = 6,
) -> List[Dict]:
    """
    Search the promotional kits catalog with precise filters.
    
    Args:
        keyword: Search in kit name, description, and included products
        min_price: Minimum price in MXN
        max_price: Maximum price in MXN
        limit: Maximum number of results
        
    Returns:
        List of matching kits
    """
    if SUITUP_CATALOG.empty:
        return []
        
    df = SUITUP_CATALOG.copy()

    # Apply filters
    if keyword:
        mask = (
            df["nombre"].str.contains(keyword, case=False, na=False) |
            df["descripcion"].str.contains(keyword, case=False, na=False) |
            df["productos"].str.contains(keyword, case=False, na=False)
        )
        df = df[mask]

    if min_price is not None:
        df = df[df["price_numeric"] >= min_price]
        
    if max_price is not None:
        df = df[df["price_numeric"] <= max_price]

    # Return results
    cols = ["nombre", "descripcion", "productos", "precio", "imagen"]
    available_cols = [col for col in cols if col in df.columns]
    
    results = df[available_cols].head(limit).to_dict(orient="records")
    logger.info(f"Precise search returned {len(results)} kits for query: {keyword}, price: {min_price}-{max_price}")
    
    return results

# ============================
# FUZZY SEARCH TOOLS (Fallback)
# ============================

# Vector store setup
_promo_vector_store_id = None
_suitup_vector_store_id = None
_promo_file_search_tool = None
_suitup_file_search_tool = None

def _setup_vector_search():
    """Initialize vector search tools if not already set up."""
    global _promo_vector_store_id, _suitup_vector_store_id, _promo_file_search_tool, _suitup_file_search_tool
    
    if _promo_file_search_tool is not None:
        return
        
    try:
        # Set up vector stores
        logger.info("Setting up vector stores...")
        _promo_vector_store_id, _suitup_vector_store_id = vector_manager.setup_vector_stores()
        
        # Create FileSearchTool instances
        _promo_file_search_tool = FileSearchTool(
            vector_store_ids=[_promo_vector_store_id],
            max_num_results=5
        )
        
        _suitup_file_search_tool = FileSearchTool(
            vector_store_ids=[_suitup_vector_store_id],
            max_num_results=5
        )
        
        logger.info(f"Vector search initialized - Promo: {_promo_vector_store_id}, SuitUp: {_suitup_vector_store_id}")
        
    except Exception as e:
        logger.warning(f"Could not set up vector search: {e}")
        _promo_file_search_tool = None
        _suitup_file_search_tool = None

@function_tool(
    name_override="search_and_format_products",
    description_override="Comprehensive search for promotional products using precise + semantic strategy. Use this after gathering description and budget."
)
def search_and_format_products(keyword: str, max_price: float | None = None, limit: int = 3) -> str:
    """
    Comprehensive search that tries precise search first, then semantic search.
    
    Args:
        keyword: Product description/query from user
        max_price: Maximum price in MXN (optional)
        limit: Maximum number of results
        
    Returns:
        Formatted string with product results or no results message
    """
    logger.info(f"Comprehensive search for: '{keyword}', max_price: {max_price}")
    
    # STEP 1: Try precise search first
    precise_results = []
    if PROMO_CATALOG.empty:
        logger.warning("PROMO_CATALOG is empty")
    else:
        df = PROMO_CATALOG.copy()
        
        # Apply keyword filter
        if keyword:
            mask = (
                df["nombre"].str.contains(keyword, case=False, na=False) |
                df["descripcion"].str.contains(keyword, case=False, na=False)
            )
            df = df[mask]
        
        # Apply price filter
        if max_price is not None:
            df = df[df["price_numeric"] <= max_price]
        
        # Get results
        cols = ["sku", "nombre", "categorias", "precio", "descripcion", "imagenes_url"]
        available_cols = [col for col in cols if col in df.columns]
        precise_results = df[available_cols].head(limit).to_dict(orient="records")
    
    logger.info(f"Precise search returned {len(precise_results)} results")
    
    # STEP 2: If precise search found results, format and return them
    if precise_results:
        return _format_product_results(precise_results)
    
    # STEP 3: Try semantic/vector search as fallback
    logger.info("Precise search found no results, trying semantic search...")
    
    semantic_results = []
    try:
        # Skip vector search setup for now, use improved keyword fallback
        # Extract meaningful words from the query
        words = keyword.split()
        meaningful_words = [word for word in words if len(word) > 3]
        
        logger.info(f"Trying semantic search with words: {meaningful_words}")
        
        for word in meaningful_words:
            df = PROMO_CATALOG.copy()
            mask = (
                df["nombre"].str.contains(word, case=False, na=False) |
                df["descripcion"].str.contains(word, case=False, na=False) |
                df["categorias"].str.contains(word, case=False, na=False)
            )
            df = df[mask]
            
            if max_price is not None:
                df = df[df["price_numeric"] <= max_price]
            
            if not df.empty:
                cols = ["sku", "nombre", "categorias", "precio", "descripcion", "imagenes_url"]
                available_cols = [col for col in cols if col in df.columns]
                semantic_results = df[available_cols].head(limit).to_dict(orient="records")
                logger.info(f"Found {len(semantic_results)} results with word: {word}")
                break
        
        # If still no results, try with very broad search terms
        if not semantic_results and max_price is not None:
            logger.info("Trying broader search within price range...")
            df = PROMO_CATALOG.copy()
            df = df[df["price_numeric"] <= max_price]
            if not df.empty:
                # Get popular/featured products within budget
                cols = ["sku", "nombre", "categorias", "precio", "descripcion", "imagenes_url"]
                available_cols = [col for col in cols if col in df.columns]
                semantic_results = df[available_cols].head(limit).to_dict(orient="records")
                logger.info(f"Found {len(semantic_results)} results with broad price search")
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
    
    logger.info(f"Semantic search returned {len(semantic_results)} results")
    
    # STEP 4: Return results or no-results message
    if semantic_results:
        return _format_product_results(semantic_results)
    else:
        return "No se encontraron productos que coincidan con los criterios de búsqueda."

@function_tool(
    name_override="search_and_format_kits",
    description_override="Comprehensive search for promotional kits using precise + semantic strategy. Use this after gathering description and budget."
)
def search_and_format_kits(keyword: str, max_price: float | None = None, limit: int = 3) -> str:
    """
    Comprehensive search that tries precise search first, then semantic search for kits.
    
    Args:
        keyword: Kit description/query from user
        max_price: Maximum price in MXN (optional)
        limit: Maximum number of results
        
    Returns:
        Formatted string with kit results or no results message
    """
    logger.info(f"Comprehensive kit search for: '{keyword}', max_price: {max_price}")
    
    # STEP 1: Try precise search first
    precise_results = []
    if SUITUP_CATALOG.empty:
        logger.warning("SUITUP_CATALOG is empty")
    else:
        df = SUITUP_CATALOG.copy()
        
        # Apply keyword filter
        if keyword:
            mask = (
                df["nombre"].str.contains(keyword, case=False, na=False) |
                df["descripcion"].str.contains(keyword, case=False, na=False) |
                df["productos"].str.contains(keyword, case=False, na=False)
            )
            df = df[mask]
        
        # Apply price filter
        if max_price is not None:
            df = df[df["price_numeric"] <= max_price]
        
        # Get results
        cols = ["nombre", "descripcion", "productos", "precio", "imagen"]
        available_cols = [col for col in cols if col in df.columns]
        precise_results = df[available_cols].head(limit).to_dict(orient="records")
    
    logger.info(f"Precise kit search returned {len(precise_results)} results")
    
    # STEP 2: If precise search found results, format and return them
    if precise_results:
        return _format_kit_results(precise_results)
    
    # STEP 3: Try semantic/vector search as fallback
    logger.info("Precise kit search found no results, trying semantic search...")
    _setup_vector_search()
    
    semantic_results = []
    if _suitup_file_search_tool is not None:
        try:
            # Use vector search (this would be implemented with proper FileSearchTool integration)
            # For now, implement keyword fallback with individual words
            words = keyword.split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    df = SUITUP_CATALOG.copy()
                    mask = (
                        df["nombre"].str.contains(word, case=False, na=False) |
                        df["descripcion"].str.contains(word, case=False, na=False) |
                        df["productos"].str.contains(word, case=False, na=False)
                    )
                    df = df[mask]
                    
                    if max_price is not None:
                        df = df[df["price_numeric"] <= max_price]
                    
                    if not df.empty:
                        cols = ["nombre", "descripcion", "productos", "precio", "imagen"]
                        available_cols = [col for col in cols if col in df.columns]
                        semantic_results = df[available_cols].head(limit).to_dict(orient="records")
                        break
        except Exception as e:
            logger.error(f"Semantic kit search failed: {e}")
    
    logger.info(f"Semantic kit search returned {len(semantic_results)} results")
    
    # STEP 4: Return results or no-results message
    if semantic_results:
        return _format_kit_results(semantic_results)
    else:
        return "No se encontraron kits que coincidan con los criterios de búsqueda."

def _format_product_results(results: List[Dict]) -> str:
    """Format product search results for agent presentation with separate messages."""
    if not results:
        return "No se encontraron productos."
    
    # Return explicit instructions for separate messages
    instructions = ["IMPORTANTE: Envía cada mensaje por separado. NO envíes todo como un solo mensaje."]
    
    for i, product in enumerate(results, 1):
        nombre = product.get('nombre', 'N/A')
        descripcion = product.get('descripcion', 'N/A')
        precio = product.get('precio', 'N/A')
        imagen = product.get('imagenes_url', '')
        
        instructions.append(f"\nPRODUCTO {i} - Envía 2 mensajes separados:")
        instructions.append(f"MENSAJE {i}A: {nombre} — {descripcion} | ${precio} MXN")
        instructions.append(f"MENSAJE {i}B: {imagen}")
    
    instructions.append("\nRecuerda: Envía cada mensaje individualmente, no como un bloque de texto.")
    
    return "\n".join(instructions)

def _format_kit_results(results: List[Dict]) -> str:
    """Format kit search results for agent presentation with separate messages."""
    if not results:
        return "No se encontraron kits."
    
    # Return explicit instructions for separate messages
    instructions = ["IMPORTANTE: Envía cada mensaje por separado. NO envíes todo como un solo mensaje."]
    
    for i, kit in enumerate(results, 1):
        nombre = kit.get('nombre', 'N/A')
        descripcion = kit.get('descripcion', 'N/A')
        productos = kit.get('productos', 'N/A')
        precio = kit.get('precio', 'N/A')
        imagen = kit.get('imagen', '')
        
        instructions.append(f"\nKIT {i} - Envía 2 mensajes separados:")
        instructions.append(f"MENSAJE {i}A: {nombre} — {descripcion} — ({productos}) | ${precio} MXN")
        instructions.append(f"MENSAJE {i}B: {imagen}")
    
    instructions.append("\nRecuerda: Envía cada mensaje individualmente, no como un bloque de texto.")
    
    return "\n".join(instructions)

# ============================
# RAW SEARCH FUNCTIONS (for direct use and testing)
# ============================

def search_and_format_products_raw(keyword: str, max_price: float = None, limit: int = 3) -> str:
    """Direct access to comprehensive product search for testing."""
    logger.info(f"Comprehensive search for: '{keyword}', max_price: {max_price}")
    
    # STEP 1: Try precise search first
    precise_results = []
    if PROMO_CATALOG.empty:
        logger.warning("PROMO_CATALOG is empty")
    else:
        df = PROMO_CATALOG.copy()
        
        # Apply keyword filter
        if keyword:
            mask = (
                df["nombre"].str.contains(keyword, case=False, na=False) |
                df["descripcion"].str.contains(keyword, case=False, na=False)
            )
            df = df[mask]
        
        # Apply price filter
        if max_price is not None:
            df = df[df["price_numeric"] <= max_price]
        
        # Get results
        cols = ["sku", "nombre", "categorias", "precio", "descripcion", "imagenes_url"]
        available_cols = [col for col in cols if col in df.columns]
        precise_results = df[available_cols].head(limit).to_dict(orient="records")
    
    logger.info(f"Precise search returned {len(precise_results)} results")
    
    # STEP 2: If precise search found results, format and return them
    if precise_results:
        return _format_product_results(precise_results)
    
    # STEP 3: Try semantic/vector search as fallback
    logger.info("Precise search found no results, trying semantic search...")
    
    semantic_results = []
    # Extract meaningful words from the query
    words = keyword.split()
    meaningful_words = [word for word in words if len(word) > 3]
    
    logger.info(f"Trying semantic search with words: {meaningful_words}")
    
    for word in meaningful_words:
        df = PROMO_CATALOG.copy()
        mask = (
            df["nombre"].str.contains(word, case=False, na=False) |
            df["descripcion"].str.contains(word, case=False, na=False) |
            df["categorias"].str.contains(word, case=False, na=False)
        )
        df = df[mask]
        
        if max_price is not None:
            df = df[df["price_numeric"] <= max_price]
        
        if not df.empty:
            cols = ["sku", "nombre", "categorias", "precio", "descripcion", "imagenes_url"]
            available_cols = [col for col in cols if col in df.columns]
            semantic_results = df[available_cols].head(limit).to_dict(orient="records")
            logger.info(f"Found {len(semantic_results)} results with word: {word}")
            break
    
    # If still no results, try with very broad search terms
    if not semantic_results and max_price is not None:
        logger.info("Trying broader search within price range...")
        df = PROMO_CATALOG.copy()
        df = df[df["price_numeric"] <= max_price]
        if not df.empty:
            # Get popular/featured products within budget
            cols = ["sku", "nombre", "categorias", "precio", "descripcion", "imagenes_url"]
            available_cols = [col for col in cols if col in df.columns]
            semantic_results = df[available_cols].head(limit).to_dict(orient="records")
            logger.info(f"Found {len(semantic_results)} results with broad price search")
    
    logger.info(f"Semantic search returned {len(semantic_results)} results")
    
    # STEP 4: Return results or no-results message
    if semantic_results:
        return _format_product_results(semantic_results)
    else:
        return "No se encontraron productos que coincidan con los criterios de búsqueda."

def find_promo_products_raw(keyword: str = None, max_price: float = None, limit: int = 3) -> List[Dict]:
    """Direct access to promo search without agents decoration."""
    if PROMO_CATALOG.empty:
        return []
        
    df = PROMO_CATALOG.copy()

    # Apply filters
    if keyword:
        mask = (
            df["nombre"].str.contains(keyword, case=False, na=False) |
            df["descripcion"].str.contains(keyword, case=False, na=False)
        )
        df = df[mask]

    if max_price is not None:
        df = df[df["price_numeric"] <= max_price]

    # Return results
    cols = ["sku", "nombre", "categorias", "precio", "descripcion", "imagenes_url"]
    available_cols = [col for col in cols if col in df.columns]
    
    return df[available_cols].head(limit).to_dict(orient="records")

def find_suitup_kits_raw(keyword: str = None, max_price: float = None, limit: int = 3) -> List[Dict]:
    """Direct access to suitup search without agents decoration."""
    if SUITUP_CATALOG.empty:
        return []
        
    df = SUITUP_CATALOG.copy()

    # Apply filters
    if keyword:
        mask = (
            df["nombre"].str.contains(keyword, case=False, na=False) |
            df["descripcion"].str.contains(keyword, case=False, na=False) |
            df["productos"].str.contains(keyword, case=False, na=False)
        )
        df = df[mask]

    if max_price is not None:
        df = df[df["price_numeric"] <= max_price]

    # Return results
    cols = ["nombre", "descripcion", "productos", "precio", "imagen"]
    available_cols = [col for col in cols if col in df.columns]
    
    return df[available_cols].head(limit).to_dict(orient="records") 