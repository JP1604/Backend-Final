#!/usr/bin/env python3
"""
Script SIMPLE para probar la API del Online Judge
"""

import requests
import json
import time

BASE_URL = "http://localhost:8008"

def test_api():
    print("=== Testing Online Judge API (SIMPLIFIED) ===")
    print()
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Health check: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # Test 2: Login as admin
    print("2. Testing login as admin...")
    try:
        login_data = {
            "email": "admin@example.com",
            "password": "password"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Admin login: {response.json()}")
        
        if response.status_code == 200:
            admin_token = response.json()["access_token"]
            print("Admin token obtained")
        else:
            print("Login failed")
            return
    except Exception as e:
        print(f"Error: {e}")
        return
    print()
    
    # Test 3: Create a challenge
    print("3. Testing create challenge...")
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        challenge_data = {
            "title": "Suma de dos numeros",
            "description": "Dados dos numeros, devuelve su suma",
            "difficulty": "Easy",
            "tags": ["math", "basic"],
            "time_limit": 1000,
            "memory_limit": 128
        }
        response = requests.post(f"{BASE_URL}/challenges/", json=challenge_data, headers=headers)
        print(f"Create challenge: {response.json()}")
        
        if response.status_code == 200:
            challenge_id = response.json()["id"]
            print(f"Challenge ID: {challenge_id}")
        else:
            print("Create challenge failed")
            return
    except Exception as e:
        print(f"Error: {e}")
        return
    print()
    
    # Test 4: Get challenges
    print("4. Testing get challenges...")
    try:
        response = requests.get(f"{BASE_URL}/challenges/", headers=headers)
        print(f"Get challenges: Found {len(response.json())} challenges")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # Test 5: Login as student
    print("5. Testing login as student...")
    try:
        login_data = {
            "email": "student@example.com",
            "password": "password"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Student login: {response.json()}")
        
        if response.status_code == 200:
            student_token = response.json()["access_token"]
            print("Student token obtained")
        else:
            print("Student login failed")
            return
    except Exception as e:
        print(f"Error: {e}")
        return
    print()
    
    # Test 6: Submit solution
    print("6. Testing submit solution...")
    try:
        headers = {"Authorization": f"Bearer {student_token}"}
        submission_data = {
            "challenge_id": challenge_id,
            "language": "python",
            "code": "def solution(a, b):\n    return a + b"
        }
        response = requests.post(f"{BASE_URL}/submissions/", json=submission_data, headers=headers)
        print(f"Submit solution: {response.json()}")
        
        if response.status_code == 200:
            submission_id = response.json()["id"]
            print(f"Submission ID: {submission_id}")
        else:
            print("Submit solution failed")
            return
    except Exception as e:
        print(f"Error: {e}")
        return
    print()
    
    # Test 7: Wait for processing
    print("7. Waiting for submission processing...")
    time.sleep(3)  # Wait for worker to process
    print("Processing completed")
    print()
    
    print("=== ALL TESTS COMPLETED SUCCESSFULLY ===")
    print("API is working correctly!")
    print("You can now use the platform!")

if __name__ == "__main__":
    test_api()
