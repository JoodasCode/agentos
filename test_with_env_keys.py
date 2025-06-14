#!/usr/bin/env python3
"""
Test AgentOS with existing .env API keys
This script automatically uses your configured API keys
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Backend URL
BASE_URL = "http://localhost:8000"

def test_backend():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            result = response.json()
            print("✅ Backend is running")
            print(f"   Version: {result.get('version')}")
            print(f"   Agents: {', '.join(result.get('agents', []))}")
            return True
        else:
            print("❌ Backend not responding")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on port 8000")
        return False

def auto_store_api_keys():
    """Automatically store API keys from environment"""
    keys_to_store = [
        ("slack", "Slack Integration", os.getenv("SLACK_CLIENT_SECRET")),
        ("notion", "Notion Integration", os.getenv("NOTION_CLIENT_SECRET")),
        ("monday", "Monday.com Integration", os.getenv("MONDAY_CLIENT_SECRET")),
    ]
    
    stored_count = 0
    for service, name, api_key in keys_to_store:
        if api_key:
            try:
                data = {
                    "service": service,
                    "service_name": name,
                    "api_key": api_key
                }
                response = requests.post(f"{BASE_URL}/api/keys/store", json=data)
                if response.status_code == 200:
                    print(f"✅ {name} API key stored")
                    stored_count += 1
                else:
                    print(f"❌ Failed to store {name} key: {response.text}")
            except Exception as e:
                print(f"❌ Error storing {name} key: {e}")
        else:
            print(f"⚠️  {name} key not found in environment")
    
    return stored_count

def test_integrations():
    """Test service integrations"""
    services = ["slack", "notion"]
    
    for service in services:
        try:
            response = requests.get(f"{BASE_URL}/api/v1/integrations/{service}/test")
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ {service.title()} integration working")
                else:
                    print(f"❌ {service.title()} integration failed: {result.get('error')}")
            else:
                print(f"❌ {service.title()} test failed: {response.text}")
        except Exception as e:
            print(f"❌ Error testing {service}: {e}")

def test_automation():
    """Test Trigger.dev automation"""
    try:
        # Test automation health
        response = requests.get(f"{BASE_URL}/api/automation/health")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Automation service available: {result.get('trigger_dev_available')}")
            
            # Test a simple automation trigger
            automation_data = {
                "event_type": "test_event",
                "user_id": "test_user",
                "properties": {
                    "source": "test_script",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            }
            
            response = requests.post(f"{BASE_URL}/api/automation/analytics-tracking", json=automation_data)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Automation triggered successfully: {result.get('run_id')}")
            else:
                print(f"❌ Automation trigger failed: {response.text}")
        else:
            print(f"❌ Automation service not available")
    except Exception as e:
        print(f"❌ Error testing automation: {e}")

def main():
    print("🚀 AgentOS Test Suite (Using .env Keys)")
    print("=" * 45)
    
    # Test backend
    if not test_backend():
        print("\n❌ Backend not running. Start it with:")
        print("   cd backend && python3 -m uvicorn app.main:app --reload")
        return
    
    print("\n🔐 Auto-storing API Keys")
    print("-" * 25)
    stored = auto_store_api_keys()
    print(f"Stored {stored} API keys")
    
    print("\n🔍 Testing Integrations")
    print("-" * 25)
    test_integrations()
    
    print("\n🤖 Testing Automation")
    print("-" * 25)
    test_automation()
    
    print("\n✨ Test Complete!")
    print("\n🎯 What you can do now:")
    print("  • Visit frontend: http://localhost:3002")
    print("  • Chat with agents: Alex, Dana, Riley, Jamie")
    print("  • Use @ mentions to target specific agents")
    print("  • Trigger automations through the chat interface")
    print("  • View API docs: http://localhost:8000/docs")

if __name__ == "__main__":
    main() 