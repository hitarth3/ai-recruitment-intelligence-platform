"""
Structured Question Pools Service for MongoDB Atlas.
Manages random non-repeating question retrieval for Technical Assessments,
AI Interviews, and Technical Manual Interviews.
"""

import random
from typing import List, Dict, Any, Optional
from app.database.database import get_database
from app.utils.logger import logger

DEFAULT_MCQ_QUESTIONS = [
    {
        "id": "mcq-1",
        "question": "In React, what is the primary purpose of the useEffect hook?",
        "options": [
            "To mutate DOM directly during render",
            "To manage side effects like data fetching, subscriptions, and DOM updates",
            "To replace state management completely",
            "To compile JSX code into HTML"
        ],
        "correct_answer": 1,
        "marks": 10,
        "explanation": "useEffect handles side effects such as subscriptions, API fetching, and manual DOM manipulation after rendering.",
        "role": "Frontend",
        "skill": "React",
        "difficulty": "Mid"
    },
    {
        "id": "mcq-2",
        "question": "Which HTTP status code signifies a resource was successfully created on the server?",
        "options": ["200 OK", "201 Created", "204 No Content", "302 Found"],
        "correct_answer": 1,
        "marks": 10,
        "explanation": "201 Created indicates that the request has succeeded and led to the creation of a new resource.",
        "role": "Backend",
        "skill": "REST API",
        "difficulty": "Junior"
    },
    {
        "id": "mcq-3",
        "question": "What is the time complexity of looking up a key in a Python hash dictionary on average?",
        "options": ["O(N)", "O(log N)", "O(1)", "O(N log N)"],
        "correct_answer": 2,
        "marks": 10,
        "explanation": "Python dictionary key lookups use hash tables, giving average time complexity of O(1).",
        "role": "Backend",
        "skill": "Python",
        "difficulty": "Mid"
    },
    {
        "id": "mcq-4",
        "question": "In TypeScript, what does the 'unknown' type represent compared to 'any'?",
        "options": [
            "It is identical to any",
            "It is a type-safe counterpart of any that requires type checking before operation",
            "It represents undefined values only",
            "It turns off type checking completely"
        ],
        "correct_answer": 1,
        "marks": 10,
        "explanation": "'unknown' forces type assertion or type narrowing before performing operations on the value.",
        "role": "Fullstack",
        "skill": "TypeScript",
        "difficulty": "Senior"
    },
    {
        "id": "mcq-5",
        "question": "In MongoDB, which index type supports full-text search across string fields?",
        "options": ["Compound Index", "Geospatial Index", "Text Index", "Hashed Index"],
        "correct_answer": 2,
        "marks": 10,
        "explanation": "Text indexes enable text search queries on string content in MongoDB documents.",
        "role": "Backend",
        "skill": "MongoDB",
        "difficulty": "Mid"
    },
    {
        "id": "mcq-6",
        "question": "Which SQL clause is used to filter records resulting from an aggregate function?",
        "options": ["WHERE", "HAVING", "GROUP BY", "ORDER BY"],
        "correct_answer": 1,
        "marks": 10,
        "explanation": "HAVING filters aggregated group data (e.g. SUM, COUNT), whereas WHERE filters individual rows before aggregation.",
        "role": "Backend",
        "skill": "SQL",
        "difficulty": "Mid"
    },
    {
        "id": "mcq-7",
        "question": "In FastAPI, what is used for asynchronous path operation functions?",
        "options": ["async def", "def sync", "yield from", "thread.start()"],
        "correct_answer": 0,
        "marks": 10,
        "explanation": "FastAPI uses native Python 'async def' to run non-blocking asynchronous request handlers.",
        "role": "Backend",
        "skill": "FastAPI",
        "difficulty": "Junior"
    },
    {
        "id": "mcq-8",
        "question": "What CSS property creates a flexbox container?",
        "options": ["display: grid", "display: flex", "flex-direction: row", "position: relative"],
        "correct_answer": 1,
        "marks": 10,
        "explanation": "display: flex defines a flex container for modern 1D layout alignment.",
        "role": "Frontend",
        "skill": "CSS",
        "difficulty": "Junior"
    },
    {
        "id": "mcq-9",
        "question": "What is the primary benefit of Redis in a web application stack?",
        "options": ["Persistent relational tables", "In-memory caching and sub-millisecond latency", "Generating PDF reports", "Managing CSS themes"],
        "correct_answer": 1,
        "marks": 10,
        "explanation": "Redis is an in-memory key-value data store providing ultra-fast caching and session storage.",
        "role": "Backend",
        "skill": "Redis",
        "difficulty": "Mid"
    },
    {
        "id": "mcq-10",
        "question": "In Git, which command stages changes for commit?",
        "options": ["git push", "git checkout", "git add", "git merge"],
        "correct_answer": 2,
        "marks": 10,
        "explanation": "git add moves modified or new files to the staging area before committing.",
        "role": "Fullstack",
        "skill": "Git",
        "difficulty": "Junior"
    },
    {
        "id": "mcq-11",
        "question": "What does JWT stand for in web authentication?",
        "options": ["Java Web Token", "JSON Web Token", "JavaScript Wide Transfer", "Joint Web Technology"],
        "correct_answer": 1,
        "marks": 10,
        "explanation": "JSON Web Token (JWT) is an open standard for securely transmitting JSON encoded information.",
        "role": "Security",
        "skill": "REST API",
        "difficulty": "Junior"
    },
    {
        "id": "mcq-12",
        "question": "In JavaScript, which operator checks both value and type equality?",
        "options": ["==", "=", "===", "!="],
        "correct_answer": 2,
        "marks": 10,
        "explanation": "=== performs strict equality comparison without type coercion.",
        "role": "Frontend",
        "skill": "JavaScript",
        "difficulty": "Junior"
    },
    {
        "id": "mcq-13",
        "question": "In Docker, what file defines container setup instructions?",
        "options": ["Docker.json", "Dockerfile", "Container.xml", "docker.yaml"],
        "correct_answer": 1,
        "marks": 10,
        "explanation": "A Dockerfile contains all instructions to assemble a Docker container image.",
        "role": "DevOps",
        "skill": "Docker",
        "difficulty": "Mid"
    },
    {
        "id": "mcq-14",
        "question": "Which HTTP method is idempotent and used to update a resource completely?",
        "options": ["POST", "PUT", "PATCH", "DELETE"],
        "correct_answer": 1,
        "marks": 10,
        "explanation": "PUT replaces the target resource entirely and is idempotent.",
        "role": "Backend",
        "skill": "REST API",
        "difficulty": "Mid"
    },
    {
        "id": "mcq-15",
        "question": "In Python, which built-in function returns the number of items in a list?",
        "options": ["count()", "length()", "len()", "size()"],
        "correct_answer": 2,
        "marks": 10,
        "explanation": "len() returns the total element count of sequence objects in Python.",
        "role": "Backend",
        "skill": "Python",
        "difficulty": "Junior"
    }
]

DEFAULT_CODING_QUESTIONS = [
    {
        "id": "code-1",
        "title": "Two Sum Algorithm",
        "role": "Fullstack",
        "skill": "Algorithms",
        "difficulty": "Mid",
        "problem_statement": "Write a function `findTwoSum(nums, target)` that returns indices of the two numbers such that they add up to target.",
        "starter_code": "function findTwoSum(nums, target) {\n  const map = new Map();\n  for (let i = 0; i < nums.length; i++) {\n    const diff = target - nums[i];\n    if (map.has(diff)) return [map.get(diff), i];\n    map.set(nums[i], i);\n  }\n  return [];\n}"
    },
    {
        "id": "code-2",
        "title": "Valid Anagram Checker",
        "role": "Frontend",
        "skill": "TypeScript",
        "difficulty": "Junior",
        "problem_statement": "Write a function `isAnagram(s, t)` that checks if string `t` is an anagram of string `s`.",
        "starter_code": "function isAnagram(s, t) {\n  if (s.length !== t.length) return false;\n  const count = {};\n  for (let char of s) count[char] = (count[char] || 0) + 1;\n  for (let char of t) {\n    if (!count[char]) return false;\n    count[char]--;\n  }\n  return true;\n}"
    }
]

DEFAULT_INTERVIEW_QUESTIONS = [
    {
        "id": "aiq-1",
        "category": "Resume & Projects",
        "question": "Can you summarize your core technical experience and highlight your most challenging production project?"
    },
    {
        "id": "aiq-2",
        "category": "Technical Architecture",
        "question": "How do you approach designing scalable RESTful APIs and managing database connection pools under high traffic?"
    },
    {
        "id": "aiq-3",
        "category": "State & Performance",
        "question": "In modern web applications, how do you handle asynchronous state synchronization and prevent unnecessary re-renders?"
    },
    {
        "id": "aiq-4",
        "category": "Behavioral",
        "question": "Describe a scenario where you faced a critical production bug. How did you diagnose, resolve, and prevent it from recurring?"
    }
]


async def seed_question_pools_if_empty():
    """Seeds default structured question pools into MongoDB Atlas if collections are empty."""
    db = get_database()
    try:
        if await db["mcq_questions"].count_documents({}) == 0:
            await db["mcq_questions"].insert_many(DEFAULT_MCQ_QUESTIONS)
            logger.info("[QuestionPool] Seeded MCQ questions pool into MongoDB.")

        if await db["coding_questions"].count_documents({}) == 0:
            await db["coding_questions"].insert_many(DEFAULT_CODING_QUESTIONS)
            logger.info("[QuestionPool] Seeded Coding questions pool into MongoDB.")

        if await db["ai_interview_questions"].count_documents({}) == 0:
            await db["ai_interview_questions"].insert_many(DEFAULT_INTERVIEW_QUESTIONS)
            logger.info("[QuestionPool] Seeded AI Interview questions pool into MongoDB.")
    except Exception as err:
        logger.error(f"[QuestionPool] Seeding error: {err}")


async def get_random_mcq_questions(
    role: str = "Fullstack",
    skills: Optional[List[str]] = None,
    exclude_ids: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Randomly fetches non-repeating MCQ questions matching job skills and role."""
    await seed_question_pools_if_empty()
    db = get_database()
    exclude_ids = exclude_ids or []

    query: Dict[str, Any] = {"id": {"$nin": exclude_ids}}
    if skills:
        regex_skills = [f"(?i){s}" for s in skills]
        query["$or"] = [
            {"skill": {"$in": skills}},
            {"role": {"$regex": role, "$options": "i"}}
        ]

    cursor = db["mcq_questions"].find(query)
    results = await cursor.to_list(length=50)

    if len(results) < limit:
        # Fallback to all questions if query filters are too strict
        cursor = db["mcq_questions"].find({"id": {"$nin": exclude_ids}})
        results = await cursor.to_list(length=50)

    random.shuffle(results)
    for r in results:
        r["_id"] = str(r["_id"])
    return results[:limit]


async def get_random_coding_question(
    role: str = "Fullstack",
    exclude_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Randomly fetches a coding question without repetition."""
    await seed_question_pools_if_empty()
    db = get_database()
    exclude_ids = exclude_ids or []

    cursor = db["coding_questions"].find({"id": {"$nin": exclude_ids}})
    results = await cursor.to_list(length=20)

    if not results:
        results = DEFAULT_CODING_QUESTIONS

    selected = random.choice(results)
    selected["_id"] = str(selected.get("_id", selected["id"]))
    return selected
