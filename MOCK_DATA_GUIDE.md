# Mock Data Testing Guide

## 🎯 What's Included in init.sql

All tables are properly initialized with realistic test data - **except leaderboards** (which are calculated, not seeded).

---

## 👥 Users (8 total)

### Credentials
**All users have password:** `password`

| ID | Email | Role | Name |
|----|-------|------|------|
| `...001` | admin@example.com | ADMIN | Admin User |
| `...002` | prof1@example.com | PROFESSOR | Professor Smith |
| `...003` | prof2@example.com | PROFESSOR | Professor Johnson |
| `...011` | alice@student.com | STUDENT | Alice Williams |
| `...012` | bob@student.com | STUDENT | Bob Brown |
| `...013` | charlie@student.com | STUDENT | Charlie Davis |
| `...014` | diana@student.com | STUDENT | Diana Miller |
| `...015` | eve@student.com | STUDENT | Eve Wilson |

---

## 📚 Courses (3 total)

| ID | Name | Teacher | Status | Students Enrolled |
|----|------|---------|--------|-------------------|
| `10...001` | Data Structures & Algorithms | Prof Smith | active | Alice, Bob, Charlie, Diana |
| `10...002` | Advanced Programming | Prof Smith | active | Alice, Bob, Eve |
| `10...003` | Algorithm Design | Prof Johnson | active | Charlie, Diana, Eve |

---

## 🎯 Challenges (5 total)

| ID | Title | Difficulty | Tags | Test Cases | Created By |
|----|-------|------------|------|------------|------------|
| `20...001` | Two Sum | Easy | arrays, hashmap | 3 | Prof Smith |
| `20...002` | Reverse String | Easy | strings, two-pointers | 3 | Prof Smith |
| `20...003` | Valid Parentheses | Easy | stack, strings | 4 | Prof Smith |
| `20...004` | Binary Search | Easy | binary-search, arrays | 0 | Prof Johnson |
| `20...005` | Merge Sort | Medium | sorting, divide-conquer | 0 | Prof Johnson |

### Course Assignments:
- **Data Structures course:** Two Sum, Reverse String, Valid Parentheses
- **Advanced Programming course:** Valid Parentheses, Merge Sort
- **Algorithm Design course:** Binary Search, Merge Sort

---

## 📝 Submissions (4 total)

| ID | Student | Challenge | Language | Status | Score | Time (ms) |
|----|---------|-----------|----------|--------|-------|-----------|
| `30...001` | Alice | Two Sum | python | ACCEPTED | 100 | 50 |
| `30...002` | Bob | Two Sum | python | ACCEPTED | 100 | 75 |
| `30...003` | Charlie | Two Sum | python | WRONG_ANSWER | 66 | 100 |
| `30...004` | Alice | Reverse String | python | ACCEPTED | 100 | 30 |

---

## 📋 Exams (3 total)

| ID | Title | Course | Status | Duration | Max Attempts | Passing Score |
|----|-------|--------|--------|----------|--------------|---------------|
| `40...001` | Midterm Exam | Data Structures | active | 90 min | 2 | 70% |
| `40...002` | Final Exam | Advanced Programming | scheduled | 120 min | 1 | 75% |
| `40...003` | Quiz 1 | Algorithm Design | completed | 60 min | 1 | 60% |

### Exam Challenges:
- **Midterm:** Two Sum (50pts), Valid Parentheses (50pts)
- **Final:** Valid Parentheses (40pts), Merge Sort (60pts)
- **Quiz 1:** Binary Search (100pts)

---

## 🏃 Exam Attempts (4 total)

| ID | Exam | Student | Score | Passed | Status |
|----|------|---------|-------|--------|--------|
| `50...001` | Midterm | Alice | 85 | ✅ Yes | Completed |
| `50...002` | Midterm | Bob | 72 | ✅ Yes | Completed |
| `50...003` | Midterm | Charlie | 65 | ❌ No | Completed |
| `50...004` | Quiz 1 | Diana | 80 | ✅ Yes | Completed |

---

## 🧪 Testing Scenarios

### Scenario 1: Login & View Courses

```bash
# Login as a professor
POST /auth/login
{
  "email": "prof1@example.com",
  "password": "password"
}

# List courses (should see 2 courses they teach)
GET /courses/
```

### Scenario 2: Login as Student & Submit Solution

```bash
# Login as Alice
POST /auth/login
{
  "email": "alice@student.com",
  "password": "password"
}

# View enrolled courses (should see 2)
GET /courses/

# View challenges in a course
GET /courses/10000000-0000-0000-0000-000000000001/challenges

# Submit solution to Two Sum
POST /submissions/
{
  "challenge_id": "20000000-0000-0000-0000-000000000001",
  "language": "python",
  "code": "def twoSum(nums, target):\n    hash_map = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in hash_map:\n            return [hash_map[complement], i]\n        hash_map[num] = i"
}

# Check submission status
GET /submissions/{submission_id}

# Check queue (should process quickly)
GET /submissions/queue/status
```

### Scenario 3: Enroll a New Student

```bash
# Login as professor
POST /auth/login
{
  "email": "prof1@example.com",
  "password": "password"
}

# Enroll Eve in Data Structures course
POST /courses/10000000-0000-0000-0000-000000000001/students
{
  "student_id": "00000000-0000-0000-0000-000000000015"
}

# Verify enrollment
GET /courses/10000000-0000-0000-0000-000000000001/students
```

### Scenario 4: Assign New Challenge to Course

```bash
# As professor, assign Binary Search to Data Structures
POST /courses/10000000-0000-0000-0000-000000000001/challenges
{
  "challenge_id": "20000000-0000-0000-0000-000000000004",
  "order_index": 4
}
```

### Scenario 5: View Exam Details

```bash
# Login as student
POST /auth/login
{
  "email": "alice@student.com",
  "password": "password"
}

# View course exams
GET /exams/?course_id=10000000-0000-0000-0000-000000000001

# View specific exam
GET /exams/40000000-0000-0000-0000-000000000001
```

---

## 📊 Expected Leaderboard Data (Once Calculated)

### Challenge Leaderboard - Two Sum

| Rank | Student | Score | Time (ms) | Submissions |
|------|---------|-------|-----------|-------------|
| 1 | Alice | 100 | 50 | 1 |
| 2 | Bob | 100 | 75 | 1 |
| 3 | Charlie | 66 | 100 | 1 |

### Course Leaderboard - Data Structures

| Rank | Student | Total Score | Total Time | Challenges |
|------|---------|-------------|------------|------------|
| 1 | Alice | 200 | 80 | 2 |
| 2 | Bob | 100 | 75 | 1 |
| 3 | Charlie | 66 | 100 | 1 |

### Exam Leaderboard - Midterm

| Rank | Student | Score | Time Taken |
|------|---------|-------|------------|
| 1 | Alice | 85 | 1h 0m |
| 2 | Bob | 72 | 1h 30m |
| 3 | Charlie | 65 | 2h 0m |

---

## 🔄 Resetting Mock Data

To reset the database with fresh mock data:

```bash
# Stop services
docker-compose stop api worker

# Reinitialize database
Get-Content init.sql | docker exec -i online-judge-postgres psql -U postgres

# Restart services
docker-compose up -d api worker
```

---

## 🎯 Quick Test Commands

### Health Check
```bash
curl http://localhost:8008/health
```

### Login (get token)
```bash
curl -X POST http://localhost:8008/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@student.com","password":"password"}'
```

### List Courses
```bash
curl http://localhost:8008/courses/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Submit Solution
```bash
curl -X POST http://localhost:8008/submissions/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "challenge_id":"20000000-0000-0000-0000-000000000001",
    "language":"python",
    "code":"def twoSum(nums, target):\n    return [0,1]"
  }'
```

---

## ✅ What to Expect

- **Users:** 8 users (1 admin, 2 professors, 5 students)
- **Courses:** 3 active courses with enrollments
- **Challenges:** 5 challenges (3 with test cases ready)
- **Submissions:** 4 historical submissions
- **Exams:** 3 exams (1 active, 1 scheduled, 1 completed)
- **Exam Attempts:** 4 completed attempts
- **Leaderboards:** 0 entries (calculated on-demand from submissions)

---

**Note:** The mock data is designed to be realistic and interconnected. Students are enrolled in multiple courses, challenges are assigned to courses, and there are historical submissions to seed leaderboard calculations.

