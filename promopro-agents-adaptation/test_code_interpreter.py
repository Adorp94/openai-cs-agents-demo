#!/usr/bin/env python3
"""
Test Code Interpreter tool directly to verify it works correctly
"""
import os
import sys
import asyncio
import signal
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Now import from agents package
from agents import (
    CodeInterpreterTool, 
    Runner, 
    Agent,
    ItemHelpers,
    MessageOutputItem,
    ToolCallItem,
    ToolCallOutputItem
)
from dotenv import load_dotenv

# Load environment variables from backend directory  
load_dotenv(backend_dir / '.env')

# File IDs from the uploaded CSV files
PROMO_FILE_ID = "file-HqKRR7doZMWYoPf79cQ9V6"

# Create Code Interpreter tool with the promo file
promo_code_interpreter = CodeInterpreterTool(
    tool_config={
        "type": "code_interpreter", 
        "container": {
            "type": "auto",
            "file_ids": [PROMO_FILE_ID]
        }
    }
)

# Test prompt exactly as you specified
test_prompt = """Search for termos that are below 300 pesos. Give me the best 3 options in the following structure:
For product 1:
    **Message 1:** {{nombre}} — {{descripcion}} | ${{precio}} MXN
    **Message 2:** {{imagenes_url}}
    
    For product 2:
    **Message 1:** {{nombre}} — {{descripcion}} | ${{precio}} MXN
    **Message 2:** {{imagenes_url}}
    
    For product 3:
    **Message 1:** {{nombre}} — {{descripcion}} | ${{precio}} MXN
    **Message 2:** {{imagenes_url}}"""

# Create a simple agent just for testing the Code Interpreter
test_agent = Agent(
    name="Code Interpreter Test Agent",
    model="gpt-4o",
    instructions="You are a helpful assistant that uses Code Interpreter to analyze CSV files. Follow the user's instructions exactly.",
    tools=[promo_code_interpreter]
)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Test timed out after 3 minutes")

async def test_code_interpreter():
    """Test the Code Interpreter with the exact prompt"""
    print("🧪 Testing Code Interpreter with prompt:")
    print("-" * 60)
    print(test_prompt)
    print("-" * 60)
    print("\n⏳ Running Code Interpreter (this may take 1-2 minutes)...")
    
    # Set a 3-minute timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(180)  # 3 minutes
    
    try:
        # Run the agent with the test prompt
        result = await Runner.run(test_agent, test_prompt)
        
        # Cancel the timeout
        signal.alarm(0)
        
        print("\n✅ Code Interpreter Result:")
        print("=" * 60)
        
        # Print all items from the result
        messages = []
        tool_calls = []
        tool_outputs = []
        
        for item in result.new_items:
            if isinstance(item, MessageOutputItem):
                text = ItemHelpers.text_message_output(item)
                messages.append(f"Assistant ({item.agent.name}): {text}")
                print(f"Assistant ({item.agent.name}): {text}")
            elif isinstance(item, ToolCallItem):
                tool_name = getattr(item.raw_item, "name", "Unknown")
                tool_calls.append(tool_name)
                print(f"🔧 Tool Call: {tool_name}")
            elif isinstance(item, ToolCallOutputItem):
                tool_outputs.append(str(item.output))
                print(f"📊 Tool Output: {str(item.output)[:200]}...")
        
        print("=" * 60)
        
        print(f"\n📊 Tool calls made: {len(tool_calls)}")
        print(f"📋 Tool outputs: {len(tool_outputs)}")
        print(f"💬 Messages: {len(messages)}")
        
        # Get the final response
        final_responses = [msg for msg in messages if "Assistant" in msg]
        final_response = final_responses[-1] if final_responses else "No response"
        print(f"\n🎯 Final Response Length: {len(final_response)} characters")
        
        # Check if response contains actual product data
        if "CILINDRO VATTEN" in final_response or "Kalaus" in final_response or "$" in final_response:
            print("✅ Response contains actual product data!")
        else:
            print("❌ Response does not contain expected product data")
            print("\n🔍 Debug - First tool output:")
            if tool_outputs:
                print(tool_outputs[0][:500] + "..." if len(tool_outputs[0]) > 500 else tool_outputs[0])
        
        return final_response
            
    except TimeoutError:
        print("\n❌ Test timed out after 3 minutes")
        signal.alarm(0)
        return None
    except Exception as e:
        print(f"❌ Error testing Code Interpreter: {e}")
        import traceback
        traceback.print_exc()
        signal.alarm(0)
        raise

if __name__ == "__main__":
    asyncio.run(test_code_interpreter()) 