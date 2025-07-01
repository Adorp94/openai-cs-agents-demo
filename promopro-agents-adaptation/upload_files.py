#!/usr/bin/env python3
"""
Upload CSV files to OpenAI and update file IDs
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def upload_file(file_path, purpose="assistants"):
    """Upload a file to OpenAI and return the file ID"""
    print(f"Uploading {file_path}...")
    
    with open(file_path, "rb") as file:
        response = client.files.create(
            file=file,
            purpose=purpose
        )
    
    file_id = response.id
    print(f"✅ Uploaded {file_path} -> File ID: {file_id}")
    return file_id

def main():
    """Upload both CSV files and save their IDs"""
    
    # Upload promo.csv
    promo_file_id = upload_file("data/promo.csv")
    
    # Upload suitup.csv  
    suitup_file_id = upload_file("data/suitup.csv")
    
    # Save the file IDs to meta files
    with open("data/promo.csv.meta.json", "w") as f:
        json.dump({"file_id": promo_file_id}, f)
    
    with open("data/suitup.csv.meta.json", "w") as f:
        json.dump({"file_id": suitup_file_id}, f)
    
    print("\n📁 File IDs saved to meta files:")
    print(f"PROMO_FILE_ID = {promo_file_id}")
    print(f"SUITUP_FILE_ID = {suitup_file_id}")
    
    print(f"\n🔧 Update these in main.py:")
    print(f'PROMO_FILE_ID = "{promo_file_id}"')
    print(f'SUITUP_FILE_ID = "{suitup_file_id}"')

if __name__ == "__main__":
    main() 