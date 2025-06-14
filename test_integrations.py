#!/usr/bin/env python3
"""
Test script for AgentOS service integrations
Run this to test your Slack and Notion connections
"""

import requests
import json
import sys

# Backend URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "running":
                print("✅ Backend is running")
                return True
            else:
                print("❌ Backend health check failed")
                return False
        else:
            print("❌ Backend health check failed")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on port 8000")
        return False

def store_api_key(service, api_key, service_name):
    """Store an API key"""
    data = {
        "service": service,
        "service_name": service_name,
        "api_key": api_key
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/keys/store", json=data)
        if response.status_code == 200:
            print(f"✅ {service_name} API key stored successfully")
            return True
        else:
            print(f"❌ Failed to store {service_name} API key: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error storing API key: {e}")
        return False

def test_service_connection(service):
    """Test service connection"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/integrations/{service}/test")
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ {service.title()} connection test passed")
                return True
            else:
                print(f"❌ {service.title()} connection test failed: {result.get('error')}")
                return False
        else:
            print(f"❌ {service.title()} test request failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing {service}: {e}")
        return False

def test_slack_message():
    """Test sending a Slack message"""
    data = {
        "channel": "#general",  # Change this to your channel
        "message": "🤖 Test message from AgentOS!",
        "user_id": "test_user"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/integrations/slack/send-message", json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Slack message sent successfully")
                return True
            else:
                print(f"❌ Failed to send Slack message: {result.get('error')}")
                return False
        else:
            print(f"❌ Slack message request failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending Slack message: {e}")
        return False

def test_notion_page():
    """Test creating a Notion page"""
    data = {
        "title": "🤖 Test Page from AgentOS",
        "content": "This is a test page created by AgentOS automation system.",
        "user_id": "test_user"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/integrations/notion/create-page", json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Notion page created successfully")
                print(f"   Page URL: {result.get('page_url', 'N/A')}")
                return True
            else:
                print(f"❌ Failed to create Notion page: {result.get('error')}")
                return False
        else:
            print(f"❌ Notion page request failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating Notion page: {e}")
        return False

def main():
    print("🚀 AgentOS Integration Test Suite")
    print("=" * 40)
    
    # Test backend health
    if not test_health():
        sys.exit(1)
    
    print("\n📝 API Key Setup")
    print("-" * 20)
    
    # Get API keys from user
    slack_token = input("Enter your Slack Bot Token (xoxb-...): ").strip()
    if slack_token:
        store_api_key("slack", slack_token, "Slack Bot")
    
    notion_token = input("Enter your Notion Integration Token (secret_...): ").strip()
    if notion_token:
        store_api_key("notion", notion_token, "Notion Integration")
    
    print("\n🔍 Connection Tests")
    print("-" * 20)
    
    # Test connections
    if slack_token:
        test_service_connection("slack")
    
    if notion_token:
        test_service_connection("notion")
    
    print("\n🧪 Functionality Tests")
    print("-" * 20)
    
    # Test actual functionality
    if slack_token:
        test_slack_message()
    
    if notion_token:
        test_notion_page()
    
    print("\n✨ Test complete!")
    print("Check your Slack channel and Notion workspace for test messages/pages.")

if __name__ == "__main__":
    main() 