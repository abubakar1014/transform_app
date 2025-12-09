# 📘 Complete Guide: Build FastAPI Transform App from Scratch

This guide will walk you through creating a production-ready FastAPI application that transforms and analyzes text.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Instructions](#step-by-step-instructions)
4. [Testing Your Application](#testing-your-application)
5. [API Documentation](#api-documentation)
6. [Key Concepts](#key-concepts)
7. [Common Issues](#common-issues)
8. [Bonus Challenges](#bonus-challenges)

---

## 🎯 Project Overview

**What we're building:**
- A REST API that accepts text input
- Normalizes whitespace in the text
- Tokenizes the text into words
- Returns detailed statistics about the text

**Technologies:**
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type hints
- **Uvicorn**: Lightning-fast ASGI server
- **Pytest**: Testing framework

---

## ✅ Prerequisites

Before starting, make sure you have:
- Python 3.12 or higher installed
- Basic understanding of Python
- A code editor (VS Code, PyCharm, Cursor, etc.)
- Terminal/Command Prompt access

Check your Python version:
```powershell
python --version
```

---

## 🚀 Step-by-Step Instructions

### **Step 1: Create Project Structure**

Open your terminal and run these commands:

```powershell
# Navigate to where you want to create the project
cd D:\Others

# Create project directory
mkdir transform_app
cd transform_app

# Create a virtual environment
python -m venv venv

# Activate the virtual environment (Windows)
.\venv\Scripts\activate

# You should see (venv) at the start of your prompt
```

**Why use a virtual environment?**
- Isolates project dependencies
- Prevents conflicts between different projects
- Makes the project portable and reproducible

---

### **Step 2: Create `requirements.txt`**

Create a new file named `requirements.txt` in your project folder and add:

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pytest==7.4.3
requests==2.31.0
httpx==0.25.1
```

**What each package does:**
- `fastapi`: The web framework
- `uvicorn`: ASGI server to run the app
- `pydantic`: Data validation and serialization
- `pytest`: Testing framework
- `requests`: HTTP library for making requests
- `httpx`: Async HTTP client (used by TestClient)

**Install the dependencies:**

```powershell
pip install -r requirements.txt
```

This will take a minute to download and install everything.

---

### **Step 3: Create `app.py`**

Create a new file named `app.py` with the following code:

```python
# app.py
"""
Contract (read aloud before coding):
- POST /transform
- Required: {"text": <string>}
- Optional: {"language": <string>}
- Extra fields ignored.
- Response: {"original", "normalized", "length", "word_count", "tokens", "language?"}
- Invariants:
  * length == len(original)
  * normalized has no leading/trailing whitespace and collapsed internal whitespace
  * tokens == [] if normalized == "" else normalized.split(" ")
  * word_count == len(tokens)
- Errors: missing/non-string text -> 400 with JSON error message.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import re

app = FastAPI(title="Transform API", version="1.0")

TOKEN_RE = re.compile(r'\S+')  # matches sequences of non-whitespace characters


class TransformRequest(BaseModel):
    text: str = Field(description="Text to transform (required)")
    language: Optional[str] = Field(default=None, description="Optional language hint (optional)")

class TransformResponse(BaseModel):
    original: str
    normalized: str
    length: int
    word_count: int
    tokens: List[str]
    language: Optional[str] = None


def normalize_text(s: str) -> str:
    # collapse all whitespace sequences into a single space and trim ends
    # deterministic and unicode-aware
    return re.sub(r'\s+', ' ', s).strip()


@app.post("/transform", response_model=TransformResponse, response_model_exclude_none=True)
def transform(req: TransformRequest):
    # Validate `text` is a string is already enforced by Pydantic.
    original = req.text
    if not isinstance(original, str):
        # Shouldn't happen due to Pydantic but keep defensive check.
        raise HTTPException(status_code=400, detail="Invalid request: 'text' must be a string.")

    normalized = normalize_text(original)
    # Extract tokens as sequences of non-whitespace characters from normalized.
    # Using TOKEN_RE ensures deterministic tokenization.
    tokens = TOKEN_RE.findall(normalized) if normalized else []
    word_count = len(tokens)
    length = len(original)  # character count (Python gives Unicode codepoints)

    resp = {
        "original": original,
        "normalized": normalized,
        "length": length,
        "word_count": word_count,
        "tokens": tokens,
    }

    # Only include language if provided in request to preserve old behavior.
    if req.language is not None:
        resp["language"] = req.language

    return resp
```

**Code Explanation:**

1. **Imports**: We import FastAPI, Pydantic models, and standard Python libraries
2. **App Instance**: `app = FastAPI(...)` creates our application
3. **Pydantic Models**: Define request/response structure with automatic validation
4. **normalize_text()**: Helper function that collapses whitespace
5. **@app.post()**: Decorator that creates a POST endpoint at `/transform`
6. **response_model_exclude_none=True**: Excludes fields with None values from response

---

### **Step 4: Create `test_transform.py`**

Create a new file named `test_transform.py` for your test cases:

```python
# test_transform.py
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_basic_transform():
    r = client.post("/transform", json={"text": "Hello world"})
    assert r.status_code == 200
    j = r.json()
    assert j["original"] == "Hello world"
    assert j["normalized"] == "Hello world"
    assert j["length"] == len("Hello world")
    assert j["tokens"] == ["Hello", "world"]
    assert j["word_count"] == 2
    assert "language" not in j

def test_empty_text():
    r = client.post("/transform", json={"text": ""})
    assert r.status_code == 200
    j = r.json()
    assert j["original"] == ""
    assert j["normalized"] == ""
    assert j["length"] == 0
    assert j["tokens"] == []
    assert j["word_count"] == 0

def test_language_preserved():
    r = client.post("/transform", json={"text": "Hola mundo", "language": "spanish"})
    assert r.status_code == 200
    j = r.json()
    assert j["language"] == "spanish"
    assert j["original"] == "Hola mundo"

def test_invalid_missing_text():
    r = client.post("/transform", json={})
    assert r.status_code == 422  # pydantic validation error from FastAPI

def test_non_string_text():
    r = client.post("/transform", json={"text": 123})
    # pydantic will also treat this as validation error -> 422
    assert r.status_code == 422
```

**Test Explanation:**

- **TestClient**: FastAPI's built-in test client (doesn't require running server)
- **test_basic_transform**: Tests normal text transformation
- **test_empty_text**: Tests edge case with empty string
- **test_language_preserved**: Tests optional language field
- **test_invalid_missing_text**: Tests validation error when text is missing
- **test_non_string_text**: Tests validation error when text is not a string

---

### **Step 5: Create `README.md`**

Create a file named `README.md` for project documentation:

```markdown
# Transform API

A FastAPI application that transforms and analyzes text.

## Features

- Text normalization (collapse whitespace)
- Word tokenization
- Character counting
- Optional language metadata

## Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

## Run Server

```bash
uvicorn app:app --reload --port 8000
```

## Run Tests

```bash
pytest -v
```

## API Endpoint

**POST /transform**

Request:
```json
{
  "text": "Hello   world",
  "language": "english"
}
```

Response:
```json
{
  "original": "Hello   world",
  "normalized": "Hello world",
  "length": 13,
  "word_count": 2,
  "tokens": ["Hello", "world"],
  "language": "english"
}
```

## Interactive Documentation

Once the server is running, visit:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
```

---

## 🧪 Testing Your Application

### **Run All Tests**

```powershell
pytest -v
```

Expected output:
```
============================= test session starts =============================
platform win32 -- Python 3.12.4, pytest-7.4.3, pluggy-1.6.0
collected 5 items

test_transform.py::test_basic_transform PASSED                           [ 20%]
test_transform.py::test_empty_text PASSED                                [ 40%]
test_transform.py::test_language_preserved PASSED                        [ 60%]
test_transform.py::test_invalid_missing_text PASSED                      [ 80%]
test_transform.py::test_non_string_text PASSED                           [100%]

============================== 5 passed in 1.47s ==============================
```

### **Run Specific Tests**

```powershell
# Run a single test
pytest test_transform.py::test_basic_transform -v

# Run tests matching a pattern
pytest -k "language" -v

# Show print statements
pytest -v -s

# Generate coverage report
pytest --cov=app test_transform.py
```

---

## 🚀 Running the Server

### **Start the Development Server**

```powershell
uvicorn app:app --reload --port 8000
```

**Flags explained:**
- `app:app` - First `app` is the filename, second `app` is the FastAPI instance
- `--reload` - Auto-restart when code changes (development only)
- `--port 8000` - Run on port 8000

Expected output:
```
INFO:     Will watch for changes in these directories: ['D:\\Others\\transform_app']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [27984] using WatchFiles
INFO:     Started server process [35332]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### **Production Server**

For production, remove `--reload` and add workers:

```powershell
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📡 API Documentation

### **Interactive API Docs**

FastAPI automatically generates interactive documentation:

1. **Swagger UI**: http://127.0.0.1:8000/docs
   - Try API endpoints directly in browser
   - See request/response schemas
   - Auto-generated from your code

2. **ReDoc**: http://127.0.0.1:8000/redoc
   - Alternative documentation style
   - Better for reading/printing

### **Testing with cURL**

**Windows PowerShell:**
```powershell
$body = @{
    text = "Hello   world"
    language = "english"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/transform" -Body $body -ContentType "application/json"
```

**Linux/Mac:**
```bash
curl -X POST "http://127.0.0.1:8000/transform" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello   world", "language": "english"}'
```

### **Testing with Python**

```python
import requests

# Test 1: Basic request
response = requests.post(
    "http://127.0.0.1:8000/transform",
    json={"text": "Hello   world"}
)
print(response.json())

# Test 2: With language
response = requests.post(
    "http://127.0.0.1:8000/transform",
    json={"text": "Hola mundo", "language": "spanish"}
)
print(response.json())

# Test 3: Complex whitespace
response = requests.post(
    "http://127.0.0.1:8000/transform",
    json={"text": "  Multiple   spaces\n\ntabs\t\there  "}
)
print(response.json())
```

---

## 📁 Final Project Structure

Your project should look like this:

```
transform_app/
├── venv/                    # Virtual environment (don't commit to git)
│   ├── Scripts/
│   ├── Lib/
│   └── ...
├── app.py                   # Main FastAPI application
├── test_transform.py        # Test cases
├── requirements.txt         # Project dependencies
├── README.md               # Project documentation
└── guide.md                # This guide
```

### **Files to Add to .gitignore**

If using Git, create a `.gitignore` file:

```
# Virtual environment
venv/
env/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd

# Testing
.pytest_cache/
.coverage

# IDE
.vscode/
.idea/
*.swp
```

---

## 🎓 Key Concepts Learned

### **1. FastAPI Framework**
- Modern Python web framework
- Automatic API documentation
- Built-in data validation
- Fast performance (based on Starlette and Pydantic)

### **2. Pydantic Models**
- Data validation using Python type hints
- Automatic JSON serialization/deserialization
- Clear error messages for invalid data

### **3. REST API Design**
- POST endpoint for data transformation
- JSON request/response format
- Proper HTTP status codes (200, 422, 400)

### **4. Testing with Pytest**
- Unit testing your API endpoints
- TestClient for testing without running server
- Assertion-based test validation

### **5. ASGI Server (Uvicorn)**
- Asynchronous server for FastAPI
- Hot reload during development
- Production-ready with workers

### **6. Virtual Environments**
- Isolated dependency management
- Reproducible project setup
- Prevents package conflicts

---

## 🐛 Common Issues & Solutions

### **Issue 1: "No module named 'fastapi'"**

**Problem**: Dependencies not installed or venv not activated

**Solution**:
```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```

---

### **Issue 2: "Port 8000 already in use"**

**Problem**: Another process is using port 8000

**Solution**: Use a different port
```powershell
uvicorn app:app --reload --port 8001
```

Or find and stop the process:
```powershell
# Windows
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# Linux/Mac
lsof -i :8000
kill -9 <process_id>
```

---

### **Issue 3: "Tests failing"**

**Problem**: Code doesn't match expected behavior

**Solutions**:
- Make sure `response_model_exclude_none=True` is set in decorator
- Check that you're using Pydantic 2.x syntax
- Verify all imports are correct
- Run tests with `-v` flag for more details

---

### **Issue 4: "Import errors"**

**Problem**: Python can't find your modules

**Solution**: Run from project root directory
```powershell
cd D:\Others\transform_app
pytest -v
```

---

### **Issue 5: "ForwardRef._evaluate() error"**

**Problem**: Using old FastAPI/Pydantic versions with Python 3.12

**Solution**: Update to compatible versions (already in requirements.txt)
```powershell
pip install --upgrade fastapi pydantic
```

---

## 🔥 Bonus Challenges

Try adding these features to improve your skills:

### **Challenge 1: Health Check Endpoint**

Add a GET endpoint that returns server status:

```python
@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0"}
```

---

### **Challenge 2: Uppercase Transformation**

Add an optional `uppercase` field:

```python
class TransformRequest(BaseModel):
    text: str = Field(description="Text to transform (required)")
    language: Optional[str] = Field(default=None, description="Optional language hint")
    uppercase: Optional[bool] = Field(default=False, description="Convert to uppercase")

# In transform function:
if req.uppercase:
    resp["uppercase_text"] = original.upper()
```

---

### **Challenge 3: Character Statistics**

Count vowels and consonants:

```python
def count_vowels_consonants(text: str) -> dict:
    vowels = "aeiouAEIOU"
    vowel_count = sum(1 for char in text if char in vowels)
    consonant_count = sum(1 for char in text if char.isalpha() and char not in vowels)
    return {"vowels": vowel_count, "consonants": consonant_count}

# Add to response
resp["stats"] = count_vowels_consonants(original)
```

---

### **Challenge 4: Input Validation**

Reject text longer than 1000 characters:

```python
class TransformRequest(BaseModel):
    text: str = Field(description="Text to transform (required)", max_length=1000)
```

---

### **Challenge 5: Request Logging**

Log each request to a file:

```python
import logging
from datetime import datetime

logging.basicConfig(
    filename='requests.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# In transform function:
logging.info(f"Transform request: text_length={len(original)}, language={req.language}")
```

---

### **Challenge 6: Rate Limiting**

Add basic rate limiting (requires additional package):

```powershell
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/transform", response_model=TransformResponse)
@limiter.limit("10/minute")
def transform(request: Request, req: TransformRequest):
    # ... rest of code
```

---

### **Challenge 7: Async Support**

Make the endpoint async:

```python
@app.post("/transform", response_model=TransformResponse, response_model_exclude_none=True)
async def transform(req: TransformRequest):
    # Use async/await for I/O operations
    # For this simple case, the logic stays the same
    original = req.text
    # ... rest of code
```

---

### **Challenge 8: Database Storage**

Store requests in SQLite database:

```powershell
pip install sqlalchemy
```

```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

engine = create_engine('sqlite:///./requests.db')
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class RequestLog(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    language = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# In transform function:
db = SessionLocal()
log = RequestLog(text=original, language=req.language)
db.add(log)
db.commit()
db.close()
```

---

## 📚 Further Learning

### **Next Steps:**

1. **FastAPI Documentation**: https://fastapi.tiangolo.com/
2. **Pydantic Documentation**: https://docs.pydantic.dev/
3. **Pytest Documentation**: https://docs.pytest.org/
4. **REST API Best Practices**: https://restfulapi.net/

### **Related Topics to Explore:**

- **Async/Await in Python**: For handling concurrent requests
- **SQLAlchemy**: Database ORM for Python
- **Docker**: Containerize your application
- **Authentication**: Add JWT tokens or API keys
- **CORS**: Allow cross-origin requests
- **Deployment**: Deploy to Heroku, AWS, or DigitalOcean

---

## 🎉 Congratulations!

You've built a complete FastAPI application from scratch! You now understand:

✅ FastAPI framework basics
✅ Pydantic data validation
✅ REST API design
✅ Testing with pytest
✅ Virtual environments
✅ Project structure

Keep practicing and building more complex applications! 🚀

---

## 💡 Tips for Success

1. **Type everything yourself** - Don't copy-paste, typing helps you learn
2. **Experiment** - Try changing things to see what happens
3. **Read error messages** - They usually tell you exactly what's wrong
4. **Use the interactive docs** - http://127.0.0.1:8000/docs is your friend
5. **Write tests first** - Test-Driven Development (TDD) leads to better code
6. **Keep it simple** - Start small, add features gradually
7. **Ask for help** - Use Stack Overflow, FastAPI Discord, or GitHub discussions

---

## 📞 Support

If you get stuck:
- FastAPI Discord: https://discord.gg/fastapi
- Stack Overflow: Tag your questions with `fastapi` and `python`
- FastAPI GitHub: https://github.com/tiangolo/fastapi

---

**Happy Coding! 💻✨**
