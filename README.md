# transform_app
1. Install deps: pip install -r requirements.txt
2. Run: uvicorn app:app --reload --port 8000
3. Call POST http://localhost:8000/transform with JSON {"text": "Hello world"}
