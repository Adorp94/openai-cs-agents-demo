#!/usr/bin/env python3
"""
Debug what exact prompt is being sent to Code Interpreter
"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Import the helper functions
from code_interpreter_helper import generate_code_interpreter_prompt

def test_prompt_generation():
    print("🔍 Testing Code Interpreter Prompt Generation")
    print("=" * 60)
    
    # Test with sample data similar to what the agent receives
    test_descripcion = "termos"
    test_precio = "300"
    
    print(f"Input descripcion: '{test_descripcion}'")
    print(f"Input precio: '{test_precio}'")
    print()
    
    # Generate the prompt using the helper function
    prompt = generate_code_interpreter_prompt(test_descripcion, test_precio)
    
    print("Generated Prompt:")
    print("-" * 40)
    print(prompt)
    print("-" * 40)
    
    # Check for potential issues
    issues = []
    
    if "{{descripcion}}" in prompt or "{{precio}}" in prompt:
        issues.append("❌ Unresolved template variables found")
    else:
        print("✅ All template variables resolved")
        
    if "below 300 pesos" in prompt:
        print("✅ Price constraint formatted correctly")
    else:
        issues.append("❌ Price constraint not formatted correctly")
        
    if "Give me the best 3 options" in prompt:
        print("✅ Request for 3 options found")
    else:
        issues.append("❌ Request for 3 options not found")
        
    if issues:
        print("\n🚨 Issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ Prompt looks good!")
        
    return prompt

def test_manual_prompt():
    """Test with the exact prompt that worked in isolation"""
    print("\n" + "=" * 60)
    print("🧪 Testing Manual Prompt (from successful isolated test)")
    print("=" * 60)
    
    manual_prompt = """Search for termos that are below 300 pesos. Give me the best 3 options in the following structure:
For product 1:
    **Message 1:** {{nombre}} — {{descripcion}} | ${{precio}} MXN
    **Message 2:** {{imagenes_url}}
    
    For product 2:
    **Message 1:** {{nombre}} — {{descripcion}} | ${{precio}} MXN
    **Message 2:** {{imagenes_url}}
    
    For product 3:
    **Message 1:** {{nombre}} — {{descripcion}} | ${{precio}} MXN
    **Message 2:** {{imagenes_url}}"""
    
    print("Manual Prompt:")
    print("-" * 40)
    print(manual_prompt)
    print("-" * 40)
    
    return manual_prompt

if __name__ == "__main__":
    generated_prompt = test_prompt_generation()
    manual_prompt = test_manual_prompt()
    
    print("\n" + "=" * 60)
    print("🔍 COMPARISON")
    print("=" * 60)
    
    if generated_prompt.strip() == manual_prompt.strip():
        print("✅ Generated prompt matches manual prompt exactly")
    else:
        print("❌ Generated prompt differs from manual prompt")
        print("\nDifferences may explain why the main system hangs!")
        
    print(f"\nGenerated prompt length: {len(generated_prompt)} characters")
    print(f"Manual prompt length: {len(manual_prompt)} characters") 