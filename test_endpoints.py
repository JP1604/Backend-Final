#!/usr/bin/env python3
"""
Script para probar endpoints específicos
"""

import requests
import json

BASE_URL = "http://localhost:8008"

def test_specific_endpoints():
    print("=== PROBANDO ENDPOINTS ESPECIFICOS ===\n")
    
    # 1. Health Check
    print("1. GET / (Health Check)")
    response = requests.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")
    
    # 2. Login Admin
    print("2. POST /auth/login (Admin)")
    login_data = {"email": "admin@example.com", "password": "password"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        admin_token = response.json()["access_token"]
        print(f"   Token: {admin_token[:30]}...\n")
    else:
        print(f"   Error: {response.json()}\n")
        return
    
    # 3. Create Challenge
    print("3. POST /challenges/ (Create Challenge)")
    headers = {"Authorization": f"Bearer {admin_token}"}
    challenge_data = {
        "title": "Fibonacci",
        "description": "Calculate nth Fibonacci number",
        "difficulty": "Medium",
        "tags": ["math", "recursion"],
        "time_limit": 3000,
        "memory_limit": 512
    }
    response = requests.post(f"{BASE_URL}/challenges/", json=challenge_data, headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        challenge = response.json()
        challenge_id = challenge["id"]
        print(f"   Challenge ID: {challenge_id}")
        print(f"   Title: {challenge['title']}\n")
    else:
        print(f"   Error: {response.json()}\n")
        return
    
    # 4. Login Student
    print("4. POST /auth/login (Student)")
    login_data = {"email": "student@example.com", "password": "password"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        student_token = response.json()["access_token"]
        print(f"   Token: {student_token[:30]}...\n")
    else:
        print(f"   Error: {response.json()}\n")
        return
    
    # 5. Submit Solution
    print("5. POST /submissions/ (Submit Solution)")
    headers = {"Authorization": f"Bearer {student_token}"}
    submission_data = {
        "challenge_id": challenge_id,
        "language": "python",
        "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
    }
    response = requests.post(f"{BASE_URL}/submissions/", json=submission_data, headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        submission = response.json()
        print(f"   Submission ID: {submission['id']}")
        print(f"   Status: {submission['status']}")
        print(f"   Language: {submission['language']}\n")
    else:
        print(f"   Error: {response.json()}\n")
    
    # 6. Test unauthorized access
    print("6. POST /challenges/ (Unauthorized)")
    response = requests.post(f"{BASE_URL}/challenges/", json=challenge_data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")
    
    print("=== TODOS LOS ENDPOINTS PROBADOS ===")

if __name__ == "__main__":
    test_specific_endpoints()

