#!/usr/bin/env python3
"""
Quick test of the fixed system
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def quick_test():
    print("🚀 Quick Test - Fixed Prompt Substitution")
    print("=" * 60)
    
    # Start conversation and go through the flow quickly
    response = requests.post(f"{BASE_URL}/chat", json={"message": ""})
    conversation_id = response.json()["conversation_id"]
    
    # Say hello
    requests.post(f"{BASE_URL}/chat", json={
        "conversation_id": conversation_id,
        "message": "Hola"
    })
    
    # Select Promoselect
    requests.post(f"{BASE_URL}/chat", json={
        "conversation_id": conversation_id,
        "message": "Promoselect"
    })
    
    # Ask for termos
    response = requests.post(f"{BASE_URL}/chat", json={
        "conversation_id": conversation_id,
        "message": "Busco termos"
    })
    
    print(f"✅ Product description saved: {response.json()['context']['descripcion']}")
    
    # Provide budget - this should trigger Code Interpreter
    print("\n⏳ Sending budget (should trigger Code Interpreter)...")
    start_time = time.time()
    
    response = requests.post(f"{BASE_URL}/chat", json={
        "conversation_id": conversation_id,
        "message": "menos de 300 pesos"
    })
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"⏱️  Response time: {duration:.1f} seconds")
    
    # Check results
    data = response.json()
    final_response = data['messages'][-1]['content'] if data['messages'] else ""
    
    print("\n" + "=" * 60)
    print("🎯 RESULTS:")
    print("=" * 60)
    
    # Check for expected products
    success_indicators = [
        "CILINDRO VATTEN" in final_response,
        "$16.65" in final_response,
        "ECO STELLA" in final_response or "ECO COUPE" in final_response,
        len(final_response) > 200
    ]
    
    if any(success_indicators):
        print("✅ SUCCESS: Found expected product data!")
        print(f"   - Found CILINDRO VATTEN: {'Yes' if 'CILINDRO VATTEN' in final_response else 'No'}")
        print(f"   - Found $16.65 price: {'Yes' if '$16.65' in final_response else 'No'}")
        print(f"   - Response length: {len(final_response)} characters")
        
        if duration < 60:  # Less than 1 minute is good
            print(f"✅ Good response time: {duration:.1f} seconds")
        else:
            print(f"⚠️  Slow response time: {duration:.1f} seconds")
            
        return True
    else:
        print("❌ FAILED: No expected product data found")
        print(f"Response: {final_response[:200]}...")
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n🎉 System is working correctly!")
    else:
        print("\n❌ System still has issues.") 