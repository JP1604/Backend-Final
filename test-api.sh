#!/bin/bash

# Script para probar la API del Online Judge

BASE_URL="http://localhost:3000"

echo "=== Testing Online Judge API ==="
echo ""

# Test 1: Login como admin
echo "1. Testing login as admin..."
ADMIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password"
  }')

echo "Admin login response: $ADMIN_RESPONSE"
ADMIN_TOKEN=$(echo $ADMIN_RESPONSE | jq -r '.accessToken')
echo "Admin token: $ADMIN_TOKEN"
echo ""

# Test 2: Crear un challenge
echo "2. Testing create challenge..."
CHALLENGE_RESPONSE=$(curl -s -X POST "$BASE_URL/challenges" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "title": "Suma de dos números",
    "description": "Dados dos números enteros, devuelve su suma.",
    "difficulty": "Easy",
    "tags": ["math", "basic"],
    "timeLimit": 1000,
    "memoryLimit": 128
  }')

echo "Create challenge response: $CHALLENGE_RESPONSE"
CHALLENGE_ID=$(echo $CHALLENGE_RESPONSE | jq -r '.id')
echo "Challenge ID: $CHALLENGE_ID"
echo ""

# Test 3: Obtener challenges
echo "3. Testing get challenges..."
curl -s -X GET "$BASE_URL/challenges" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.'
echo ""

# Test 4: Login como estudiante
echo "4. Testing login as student..."
STUDENT_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "password"
  }')

echo "Student login response: $STUDENT_RESPONSE"
STUDENT_TOKEN=$(echo $STUDENT_RESPONSE | jq -r '.accessToken')
echo "Student token: $STUDENT_TOKEN"
echo ""

# Test 5: Enviar solución
echo "5. Testing submit solution..."
SUBMISSION_RESPONSE=$(curl -s -X POST "$BASE_URL/submissions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -d '{
    "challengeId": "'$CHALLENGE_ID'",
    "language": "python",
    "code": "def solution(a, b):\n    return a + b"
  }')

echo "Submit solution response: $SUBMISSION_RESPONSE"
SUBMISSION_ID=$(echo $SUBMISSION_RESPONSE | jq -r '.id')
echo "Submission ID: $SUBMISSION_ID"
echo ""

# Test 6: Obtener submissions
echo "6. Testing get submissions..."
curl -s -X GET "$BASE_URL/submissions" \
  -H "Authorization: Bearer $STUDENT_TOKEN" | jq '.'
echo ""

echo "=== API Tests Completed ==="
