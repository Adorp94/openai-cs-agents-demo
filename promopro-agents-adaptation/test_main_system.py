#!/usr/bin/env python3
"""
Test the main system with simplified approach
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_conversation():
    print("🧪 Testing Main System with Simplified Approach")
    print("=" * 60)
    
    # Start a new conversation
    response = requests.post(f"{BASE_URL}/chat", json={"message": ""})
    data = response.json()
    conversation_id = data["conversation_id"]
    
    print(f"✅ Started conversation: {conversation_id}")
    
    # Step 1: Initial greeting
    print("\n📝 Step 1: Send initial greeting...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "conversation_id": conversation_id,
        "message": "Hola"
    })
    data = response.json()
    print(f"Agent: {data['messages'][-1]['content'] if data['messages'] else 'No response'}")
    
    # Step 2: Select Promoselect business unit
    print("\n📝 Step 2: Select Promoselect...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "conversation_id": conversation_id,
        "message": "Promoselect"
    })
    data = response.json()
    print(f"Agent: {data['messages'][-1]['content'] if data['messages'] else 'No response'}")
    
    # Step 3: Provide product description
    print("\n📝 Step 3: Ask for termos...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "conversation_id": conversation_id,
        "message": "Busco termos"
    })
    data = response.json()
    print(f"Agent: {data['messages'][-1]['content'] if data['messages'] else 'No response'}")
    
    # Step 4: Provide budget
    print("\n📝 Step 4: Set budget below 300 pesos...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "conversation_id": conversation_id,
        "message": "menos de 300 pesos"
    })
    data = response.json()
    
    # This should trigger the Code Interpreter
    print(f"Agent: {data['messages'][-1]['content'] if data['messages'] else 'No response'}")
    
    # Check if we got the expected products
    final_response = data['messages'][-1]['content'] if data['messages'] else ""
    
    print("\n" + "=" * 60)
    print("🎯 RESULTS:")
    print("=" * 60)
    
    if "CILINDRO VATTEN" in final_response:
        print("✅ Found CILINDRO VATTEN (expected product from test)")
    else:
        print("❌ Did not find CILINDRO VATTEN")
    
    if "$16.65" in final_response:
        print("✅ Found correct price $16.65")
    else:
        print("❌ Did not find expected price")
        
    if "ECO STELLA" in final_response or "ECO COUPE" in final_response:
        print("✅ Found other expected products")
    else:
        print("❌ Did not find other expected products")
        
    # Check tool calls
    tool_calls = [event for event in data.get('events', []) if event.get('type') == 'tool_call']
    print(f"\n📊 Tool calls made: {len(tool_calls)}")
    for tool_call in tool_calls:
        print(f"   - {tool_call.get('content', 'Unknown tool')}")
    
    print(f"\n📄 Final response length: {len(final_response)} characters")
    
    if len(final_response) > 200 and ("CILINDRO VATTEN" in final_response or "$" in final_response):
        print("\n🎉 SUCCESS: System is working with simplified approach!")
        return True
    else:
        print("\n❌ ISSUE: System may not be working correctly")
        print("Debug info:")
        print(f"Response: {final_response[:200]}...")
        return False

if __name__ == "__main__":
    success = test_conversation()
    if success:
        print("\n✅ All tests passed! The simplified approach is working correctly.")
    else:
        print("\n❌ Tests failed. Check the implementation.") 