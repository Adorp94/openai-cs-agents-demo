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
from dotenv import load_dotenv
from vector_search import vector_manager

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# ============================
# CLEAN OUTPUT FORMATTING & PRODUCT STORAGE
# ============================

# Global storage for last search results (for user follow-up questions)
_last_search_results = []

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
        # Get vector store IDs from environment or set them up
        _promo_vector_store_id = os.getenv("PROMO_VECTOR_STORE_ID")
        _suitup_vector_store_id = os.getenv("SUITUP_VECTOR_STORE_ID")
        
        if not _promo_vector_store_id or not _suitup_vector_store_id:
            logger.info("Setting up vector stores from scratch...")
            _promo_vector_store_id, _suitup_vector_store_id = vector_manager.setup_vector_stores()
        else:
            logger.info(f"Using existing vector stores - Promo: {_promo_vector_store_id}, SuitUp: {_suitup_vector_store_id}")
        
        # Create FileSearchTool instances
        _promo_file_search_tool = FileSearchTool(
            vector_store_ids=[_promo_vector_store_id],
            max_num_results=10  # Get more results for better filtering
        )
        
        _suitup_file_search_tool = FileSearchTool(
            vector_store_ids=[_suitup_vector_store_id],
            max_num_results=10
        )
        
        logger.info(f"Vector search initialized successfully")
        
    except Exception as e:
        logger.warning(f"Could not set up vector search: {e}")
        _promo_file_search_tool = None
        _suitup_file_search_tool = None

# Create FileSearchTool instances as actual tools for the agents
_setup_vector_search()

# Export the FileSearchTool instances for use by agents
promo_file_search = _promo_file_search_tool if _promo_file_search_tool else None
suitup_file_search = _suitup_file_search_tool if _suitup_file_search_tool else None

def _parse_vector_response_and_filter(vector_response: str, max_price: float | None, limit: int) -> List[Dict]:
    """
    Parse vector search response and extract matching products from catalog.
    
    Args:
        vector_response: Response from FileSearchTool
        max_price: Maximum price filter
        limit: Maximum number of results
        
    Returns:
        List of product dictionaries
    """
    if not vector_response or not isinstance(vector_response, str):
        return []
    
    logger.info(f"Parsing vector response: {vector_response[:200]}...")
    
    # Extract product names/SKUs mentioned in the vector response
    # This is a simple approach - the vector response should contain relevant product info
    found_products = []
    
    if PROMO_CATALOG.empty:
        return []
    
    df = PROMO_CATALOG.copy()
    
    # Apply price filter first if specified
    if max_price is not None:
        df = df[df["price_numeric"] <= max_price]
    
    # Look for products mentioned in the vector response
    # The vector response should contain product names, descriptions, or SKUs
    lines = vector_response.split('\n')
    for line in lines:
        if not line.strip():
            continue
            
        # Try to match product names mentioned in the response
        for _, product in df.iterrows():
            product_name = str(product.get('nombre', '')).lower()
            product_sku = str(product.get('sku', '')).lower()
            
            if (product_name and product_name in line.lower()) or (product_sku and product_sku in line.lower()):
                cols = ["sku", "nombre", "categorias", "precio", "descripcion", "imagenes_url"]
                available_cols = [col for col in cols if col in product.index]
                product_dict = product[available_cols].to_dict()
                
                if product_dict not in found_products:
                    found_products.append(product_dict)
                    if len(found_products) >= limit:
                        break
        
        if len(found_products) >= limit:
            break
    
    logger.info(f"Extracted {len(found_products)} products from vector response")
    return found_products

@function_tool(
    name_override="get_product_info",
    description_override="Get detailed information about a specific product from the last search results."
)
def get_product_info(product_name: str) -> str:
    """
    Get detailed information about a specific product from stored search results.
    
    Args:
        product_name: Name of the product to get info about
        
    Returns:
        Detailed product information or not found message
    """
    global _last_search_results
    
    if not _last_search_results:
        return "No hay productos almacenados de búsquedas anteriores."
    
    # Search for the product by name (case-insensitive)
    for product in _last_search_results:
        if product_name.lower() in product.get('nombre', '').lower():
            return _format_single_product_detailed(product)
    
    return f"No se encontró información sobre '{product_name}' en los resultados anteriores."

def _format_single_product_detailed(product: Dict) -> str:
    """Format a single product with all available details."""
    nombre = product.get('nombre', 'N/A')
    descripcion = product.get('descripcion', 'N/A')
    precio = product.get('precio', 'N/A')
    sku = product.get('sku', 'N/A')
    categorias = product.get('categorias', 'N/A')
    imagenes = product.get('imagenes_url', '')
    
    result = f"**{nombre}**\n"
    result += f"Precio: ${precio} MXN\n"
    result += f"SKU: {sku}\n"
    result += f"Categorías: {categorias}\n"
    result += f"Descripción: {descripcion}\n"
    
    if imagenes and imagenes.strip():
        image_links = []
        urls = [url.strip() for url in imagenes.split(',') if url.strip()]
        for j, url in enumerate(urls[:3], 1):
            image_links.append(f"[Imagen {j}]({url})")
        if image_links:
            result += f"Imágenes: {' | '.join(image_links)}"
    
    return result

@function_tool(
    name_override="search_and_format_products",
    description_override="Comprehensive search for promotional products using semantic + precise filtering strategy. Returns JSON with products that you must present individually."
)
def search_and_format_products(keyword: str, max_price: float | None = None, limit: int = 3) -> str:
    """
    IMPROVED STRATEGY: Semantic search first for relevance, then precise filtering.
    
    1. Vector/semantic search → Find semantically relevant products 
    2. Precise filtering → Apply price/budget constraints
    3. Fallback to keyword search if vector search fails
    
    Args:
        keyword: Product description/query from user
        max_price: Maximum price in MXN (optional)
        limit: Maximum number of results
        
    Returns:
        Formatted string with product results or no results message
    """
    logger.info(f"IMPROVED search strategy for: '{keyword}', max_price: {max_price}")
    
    # STEP 1: Try semantic/vector search FIRST for relevance
    logger.info("Step 1: Trying semantic/vector search for relevance...")
    _setup_vector_search()
    
    semantic_results = []
    if _promo_file_search_tool is not None:
        try:
            # Try to use actual vector search via FileSearchTool
            # This would return semantically relevant products
            logger.info(f"Using FileSearchTool vector search for: {keyword}")
            
            # Note: FileSearchTool integration would happen here
            # For now, let's implement a smarter keyword approach that focuses on semantic matching
            
            # Get a broader set of potentially relevant products first
            df = PROMO_CATALOG.copy()
            
            # Create semantic-focused search terms
            semantic_terms = _extract_semantic_terms(keyword)
            logger.info(f"Semantic terms extracted: {semantic_terms}")
            
            semantic_matches = []
            for term in semantic_terms:
                # Look for semantic matches in product fields
                mask = (
                    df["nombre"].str.contains(term, case=False, na=False) |
                    df["descripcion"].str.contains(term, case=False, na=False) |
                    df["categorias"].str.contains(term, case=False, na=False)
                )
                matches = df[mask]
                if not matches.empty:
                    semantic_matches.append(matches)
            
            # Combine and deduplicate semantic matches
            if semantic_matches:
                all_matches = pd.concat(semantic_matches).drop_duplicates()
                
                # STEP 2: Apply precise filtering (price, etc.) to semantic results
                if max_price is not None:
                    all_matches = all_matches[all_matches["price_numeric"] <= max_price]
                
                # Get the best results
                cols = ["sku", "nombre", "categorias", "precio", "descripcion", "imagenes_url"]
                available_cols = [col for col in cols if col in all_matches.columns]
                semantic_results = all_matches[available_cols].head(limit).to_dict(orient="records")
                
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
    
    logger.info(f"Semantic search returned {len(semantic_results)} results")
    
    # STEP 3: If semantic search found good results, return them
    if semantic_results:
        return _format_product_results(semantic_results)
    
    # STEP 4: Fallback to traditional precise search
    logger.info("Semantic search found no results, trying traditional precise search...")
    
    precise_results = []
    if not PROMO_CATALOG.empty:
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
    
    # STEP 5: Return results or no-results message
    if precise_results:
        return _format_product_results(precise_results)
    else:
        return "No se encontraron productos que coincidan con los criterios de búsqueda."

def _format_product_results_clean(results: List[Dict]) -> str:
    """Format product search results for clean agent presentation."""
    if not results:
        return "No se encontraron productos."
    
    formatted_products = []
    for i, product in enumerate(results, 1):
        nombre = product.get('nombre', 'N/A')
        descripcion = product.get('descripcion', 'N/A')
        precio = product.get('precio', 'N/A')
        imagenes = product.get('imagenes_url', '')
        
        # Format product info
        product_info = f"**Producto {i}:** {nombre} — {descripcion} | ${precio} MXN"
        formatted_products.append(product_info)
        
        # Add images if available
        if imagenes and imagenes.strip():
            image_links = []
            # Split multiple image URLs and create clean links
            urls = [url.strip() for url in imagenes.split(',') if url.strip()]
            for j, url in enumerate(urls[:3], 1):  # Limit to 3 images
                image_links.append(f"[Imagen {j}]({url})")
            if image_links:
                formatted_products.append(f"Imágenes: {' | '.join(image_links)}")
    
    return "\n\n".join(formatted_products)

@function_tool(
    name_override="search_products_structured", 
    description_override="Save search criteria for vector search. The agent will use FileSearchTool automatically for vector search."
)
def search_products_structured(keyword: str, max_price: float | None = None, limit: int = 3) -> str:
    """
    VECTOR-ONLY APPROACH: This function saves search criteria.
    The agent has FileSearchTool in its tools list and will use it automatically for vector search.
    
    Args:
        keyword: Product description/query from user
        max_price: Maximum price in MXN (optional)  
        limit: Maximum number of results
        
    Returns:
        Instructions for the agent to use FileSearchTool
    """
    logger.info(f"Search criteria saved - keyword: '{keyword}', max_price: {max_price}")
    
    search_instruction = f"Busca productos promocionales usando la descripción: '{keyword}'"
    if max_price:
        search_instruction += f" con precio máximo de ${max_price} MXN"
    
    search_instruction += f". Busca hasta {limit} productos relevantes usando las herramientas de búsqueda vectorial disponibles."
    
    return search_instruction

def _extract_semantic_terms(keyword: str) -> List[str]:
    """Extract semantic search terms from user query."""
    # Map common user terms to product categories/terms (PRECISE MAPPING)
    semantic_mapping = {
        "termos": ["termo", "thermal", "insulado", "acero inoxidable", "doble pared", "vacío"],
        "termo": ["termo", "thermal", "insulado", "acero inoxidable", "doble pared", "vacío"],
        "botellas": ["botella", "deportiva", "hidratación", "agua"],
        "tazas": ["taza", "mug", "café", "ceramica", "porcelana"],
        "plumas": ["pluma", "bolígrafo", "escritura", "lapiz"],
        "libretas": ["libreta", "cuaderno", "agenda", "bloc", "papel"],
        "mochilas": ["mochila", "backpack", "bolsa", "equipaje"],
        "llaveros": ["llavero", "key", "chain", "accesorio"],
        "mouse": ["mouse", "ratón", "computadora", "oficina"],
        "usb": ["usb", "memoria", "flash", "almacenamiento"],
    }
    
    # Start with the original keyword
    terms = [keyword.lower()]
    
    # Add semantic alternatives
    for key, alternatives in semantic_mapping.items():
        if key in keyword.lower():
            terms.extend(alternatives)
    
    # Add individual words from the query
    words = keyword.split()
    for word in words:
        if len(word) > 2:  # Skip very short words
            terms.append(word.lower())
    
    # Remove duplicates and return
    return list(set(terms))

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

def _format_product_results_json(results: List[Dict]) -> List[Dict]:
    """Format product search results as structured JSON for easy agent processing."""
    if not results:
        return []
    
    formatted_products = []
    for product in results:
        nombre = product.get('nombre', 'N/A')
        descripcion = product.get('descripcion', 'N/A')
        precio = product.get('precio', 'N/A')
        imagenes = product.get('imagenes_url', '')
        
        formatted_products.append({
            "name": nombre,
            "description": descripcion,
            "price": precio,
            "images": imagenes
        })
    
    return formatted_products

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