# Leaderboard System Design

## 🎯 Core Principle

**Leaderboards are DERIVED DATA, not source data.**

They should be calculated from actual submissions and exam attempts, never manually entered.

---

## 📊 How Leaderboards Work

### 1. **Challenge Leaderboard**

**Source:** `submissions` table

**Calculation Logic:**
```sql
-- For each student, find their BEST submission for a specific challenge
-- Rank by: score DESC, time ASC

SELECT 
    user_id,
    challenge_id,
    MAX(score) as best_score,
    MIN(time_ms_total) FILTER (WHERE score = MAX(score)) as best_time,
    COUNT(*) as submission_count,
    (SELECT id FROM submissions s2 
     WHERE s2.user_id = s1.user_id 
     AND s2.challenge_id = s1.challenge_id 
     ORDER BY score DESC, time_ms_total ASC 
     LIMIT 1) as best_submission_id
FROM submissions s1
WHERE challenge_id = 'CHALLENGE_ID'
  AND status = 'ACCEPTED' OR status = 'WRONG_ANSWER' -- completed submissions
GROUP BY user_id, challenge_id
ORDER BY best_score DESC, best_time ASC;
```

**Updates:** Recalculate whenever a submission completes

---

### 2. **Course Leaderboard**

**Source:** `submissions` + `course_challenges` tables

**Calculation Logic:**
```sql
-- For each student in a course:
-- 1. Find their best submission for EACH challenge in the course
-- 2. Sum all those best scores
-- 3. Sum all those best times

WITH course_challenge_ids AS (
    SELECT challenge_id 
    FROM course_challenges 
    WHERE course_id = 'COURSE_ID'
),
best_submissions AS (
    SELECT 
        s.user_id,
        s.challenge_id,
        MAX(s.score) as best_score,
        MIN(s.time_ms_total) FILTER (WHERE s.score = MAX(s.score)) as best_time
    FROM submissions s
    JOIN course_challenge_ids cc ON s.challenge_id = cc.challenge_id
    WHERE s.status IN ('ACCEPTED', 'WRONG_ANSWER')
    GROUP BY s.user_id, s.challenge_id
)
SELECT 
    user_id,
    SUM(best_score) as total_score,
    SUM(best_time) as total_time,
    COUNT(DISTINCT challenge_id) as challenges_completed
FROM best_submissions
GROUP BY user_id
ORDER BY total_score DESC, total_time ASC;
```

**Updates:** Recalculate when any submission completes for a course challenge

---

### 3. **Exam Leaderboard**

**Source:** `exam_attempts` + `submissions` tables

**Calculation Logic:**
```sql
-- For each student's exam attempt:
-- 1. Use the score from exam_attempts (already calculated)
-- 2. Rank by score DESC, submission time ASC

SELECT 
    ea.user_id,
    ea.exam_id,
    ea.score,
    (ea.submitted_at - ea.started_at) as time_taken,
    ea.passed,
    ea.submitted_at
FROM exam_attempts ea
WHERE ea.exam_id = 'EXAM_ID'
  AND ea.submitted_at IS NOT NULL  -- only completed attempts
ORDER BY ea.score DESC, time_taken ASC;
```

**Updates:** Recalculate when an exam attempt is submitted

---

## 🔄 Recalculation Strategy

### Option 1: On-Demand (Current Implementation)
- Calculate leaderboard when requested via API
- **Pros:** Always accurate, no stale data
- **Cons:** Slower API response for large datasets

### Option 2: Cached in Database (Recommended)
- Store calculated results in `leaderboard_entries` table
- Recalculate on submission completion
- **Pros:** Fast API responses
- **Cons:** Requires trigger/queue to update

### Option 3: Hybrid
- Cache in `leaderboard_entries`
- Recalculate async after submission
- Serve cached data with "last_updated" timestamp
- **Pros:** Best of both worlds
- **Cons:** Slightly stale data (seconds)

---

## 🚀 Implementation Plan

### Phase 1: Calculation Use Cases ✅ (TODO)
```
RecalculateChallengeLeaderboardUseCase
RecalculateCourseLeaderboardUseCase  
RecalculateExamLeaderboardUseCase
```

### Phase 2: API Endpoints ✅ (TODO)
```
GET /leaderboards/challenge/{id}
GET /leaderboards/course/{id}
GET /leaderboards/exam/{id}
```

### Phase 3: Auto-Recalculation 🚧 (TODO)
**Option A: Trigger-based**
```sql
CREATE TRIGGER recalculate_leaderboard_on_submission
AFTER UPDATE ON submissions
FOR EACH ROW
WHEN (NEW.status IN ('ACCEPTED', 'WRONG_ANSWER', 'TIME_LIMIT_EXCEEDED'))
EXECUTE FUNCTION queue_leaderboard_recalculation();
```

**Option B: Application-level** (Recommended)
```python
# In SubmitSolutionUseCase, after submission completes:
async def execute(...):
    # ... submit code ...
    # ... wait for results ...
    
    # Trigger leaderboard update
    await recalculate_challenge_leaderboard(challenge_id)
    await recalculate_course_leaderboard(course_id)
```

---

## 📋 Leaderboard Entry Schema

```python
@dataclass
class LeaderboardEntry:
    id: str
    user_id: str
    type: LeaderboardType  # 'challenge', 'course', 'exam'
    
    # Context (only one set based on type)
    challenge_id: Optional[str]
    course_id: Optional[str]
    exam_id: Optional[str]
    
    # Performance metrics (CALCULATED, not entered)
    score: int
    total_time_ms: int
    submissions_count: int
    best_submission_id: Optional[str]
    
    # Ranking (CALCULATED)
    rank: int
    
    # Metadata
    last_submission_at: datetime
    updated_at: datetime  # when this entry was last recalculated
```

---

## 🧪 Testing Leaderboards

### With Mock Data:

**Current State:**
- ✅ 8 Users created
- ✅ 5 Challenges with test cases
- ✅ 4 Sample submissions
- ✅ 3 Courses with enrollments
- ✅ 3 Exams with attempts

**To Test Leaderboards:**

1. **Create more submissions** via API:
```bash
POST /submissions/
{
  "challenge_id": "20000000-0000-0000-0000-000000000001",
  "language": "python",
  "code": "def twoSum(nums, target):\n    return [0, 1]"
}
```

2. **Wait for processing** (workers will update status and score)

3. **Query leaderboard** (once implemented):
```bash
GET /leaderboards/challenge/20000000-0000-0000-0000-000000000001
```

4. **Verify calculations** match submission data:
```sql
-- Manual verification query
SELECT 
    u.first_name,
    u.last_name,
    s.score,
    s.time_ms_total,
    s.status
FROM submissions s
JOIN users u ON s.user_id = u.id
WHERE s.challenge_id = '20000000-0000-0000-0000-000000000001'
ORDER BY s.score DESC, s.time_ms_total ASC;
```

---

## ✅ Benefits of Calculated Leaderboards

1. **Always Accurate** - Reflects actual performance
2. **Self-Healing** - Recalculation fixes any inconsistencies
3. **Auditable** - Can trace back to source submissions
4. **No Data Duplication** - Single source of truth
5. **Testing Friendly** - Just create submissions, leaderboard auto-updates

---

## 🎯 Next Steps

1. ✅ Remove mock leaderboard data (DONE)
2. 🚧 Implement calculation use cases (TODO)
3. 🚧 Create leaderboard API endpoints (TODO)
4. 🚧 Add auto-recalculation on submission (TODO)
5. 🚧 Add caching for performance (TODO)

---

**Key Takeaway:** Leaderboards are like a "view" of your data - they show derived information calculated from the real source data (submissions and exam attempts).

