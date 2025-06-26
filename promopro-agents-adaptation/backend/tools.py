"""
Search tools for promotional products and kits using code interpreter.
"""

from agents import function_tool
from typing import List, Dict

@function_tool(
    name_override="promo_search",
    description_override="Search the promotional products table (promo.csv) by product attributes. Use this to find individual promotional products based on user requirements."
)
def promo_search(query: str, max_rows: int = 10) -> List[Dict]:
    """
    Search promotional products using pandas in the Code Interpreter sandbox.
    
    The promo.csv file contains columns: sku, precio, categorias, nombre, descripcion, medidas, imagenes_url
    
    Args:
        query: Search criteria (e.g., "category electronics", "price under 50", "name contains mug")
        max_rows: Maximum number of results to return
        
    Returns:
        List of product dictionaries matching the search criteria
    """
    # This function body will be executed in the Code Interpreter sandbox
    # The actual CSV file will be accessible there via the file_id
    return []

@function_tool(
    name_override="suitup_search", 
    description_override="Search the promotional kits table (suitup.csv) by kit attributes. Use this to find promotional kit products based on user requirements."
)
def suitup_search(query: str, max_rows: int = 10) -> List[Dict]:
    """
    Search promotional kits using pandas in the Code Interpreter sandbox.
    
    The suitup.csv file contains columns: precio, nombre, descripcion, productos, imagen
    
    Args:
        query: Search criteria (e.g., "coffee kit", "price under 100", "name contains golf")
        max_rows: Maximum number of results to return
        
    Returns:
        List of kit dictionaries matching the search criteria
    """
    # This function body will be executed in the Code Interpreter sandbox
    # The actual CSV file will be accessible there via the file_id
    return [] 