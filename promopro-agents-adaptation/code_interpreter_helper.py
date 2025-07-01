"""
Helper functions for Code Interpreter prompts
"""

def create_product_search_prompt(descripcion: str, precio: str) -> str:
    """
    Create a Code Interpreter prompt for searching products
    
    Args:
        descripcion: Product type/description (e.g., "termos", "bolígrafos")
        precio: Price limit (e.g., "300 pesos", "50 dólares")
    
    Returns:
        Formatted prompt for Code Interpreter
    """
    prompt = f"""Search for {descripcion} that are below {precio}. Give me the best 3 options in the following structure:
For product 1:
    **Message 1:** {{{{nombre}}}} — {{{{descripcion}}}} | ${{{{precio}}}} MXN
    **Message 2:** {{{{imagenes_url}}}}
    
    For product 2:
    **Message 1:** {{{{nombre}}}} — {{{{descripcion}}}} | ${{{{precio}}}} MXN
    **Message 2:** {{{{imagenes_url}}}}
    
    For product 3:
    **Message 1:** {{{{nombre}}}} — {{{{descripcion}}}} | ${{{{precio}}}} MXN
    **Message 2:** {{{{imagenes_url}}}}"""
    
    return prompt

def create_kit_search_prompt(descripcion: str, precio: str) -> str:
    """
    Create a Code Interpreter prompt for searching kits
    
    Args:
        descripcion: Kit type/description (e.g., "kit ejecutivo", "kit promocional")
        precio: Price limit (e.g., "500 pesos", "100 dólares")
    
    Returns:
        Formatted prompt for Code Interpreter
    """
    prompt = f"""Search for {descripcion} that are below {precio}. Give me the best 3 options in the following structure:
For kit 1:
    **Message 1:** {{{{nombre}}}} — {{{{descripcion}}}} — ({{{{productos}}}}) | ${{{{precio}}}} MXN
    **Message 2:** {{{{imagen}}}}
    
    For kit 2:
    **Message 1:** {{{{nombre}}}} — {{{{descripcion}}}} — ({{{{productos}}}}) | ${{{{precio}}}} MXN
    **Message 2:** {{{{imagen}}}}
    
    For kit 3:
    **Message 1:** {{{{nombre}}}} — {{{{descripcion}}}} — ({{{{productos}}}}) | ${{{{precio}}}} MXN
    **Message 2:** {{{{imagen}}}}"""
    
    return prompt

# Test the functions
if __name__ == "__main__":
    # Test product search prompt
    product_prompt = create_product_search_prompt("termos", "300 pesos")
    print("Product Search Prompt:")
    print("=" * 60)
    print(product_prompt)
    print("=" * 60)
    
    # Test kit search prompt  
    kit_prompt = create_kit_search_prompt("kit ejecutivo", "500 pesos")
    print("\nKit Search Prompt:")
    print("=" * 60)
    print(kit_prompt)
    print("=" * 60) 