"""
INTEGRATION GUIDE - How to enable search routes safely
"""

# STEP 1: Add this import to app/main.py (line ~11, after existing imports):
# 
#    from search_engine.routes import router as search_router

# STEP 2: Add this line to app/main.py (line ~37, after existing routers):
#
#    app.include_router(search_router)

# That's it! No other modifications needed.

# NOW AVAILABLE ENDPOINTS:
# 
# GET  /search                    - Search candidates
# GET  /search/status             - Get index status  
# POST /search/index              - Rebuild index
# GET  /search/{candidate_id}/details - Get candidate details

# EXAMPLE USAGE:

"""
1. First time setup (build index):
   POST http://localhost:8000/search/index
   
   Response:
   {
     "status": "success",
     "candidates": 150,
     "tokens": 2340
   }

2. Check status:
   GET http://localhost:8000/search/status
   
   Response:
   {
     "indexed": true,
     "candidates": 150,
     "tokens": 2340
   }

3. Search for candidates:
   GET http://localhost:8000/search?q=react+node
   
   Response:
   {
     "query": "react node",
     "total_results": 5,
     "results": [
       {
         "candidate_id": 1,
         "name": "Amit Kumar",
         "email": "amit@example.com",
         "branch": "CSE",
         "cgpa": 8.7,
         "match_score": 92.5,
         "overall_score": 75.3,
         "matched_terms": ["react", "node"],
         "match_quality": "exact"
       },
       ...
     ]
   }

4. Search with filters:
   GET http://localhost:8000/search?q=python&min_score=70&branch=CSE&limit=10

5. Get candidate details:
   GET http://localhost:8000/search/1/details
   
   Response:
   {
     "id": 1,
     "name": "Amit Kumar",
     "email": "amit@example.com",
     "skills": ["python", "react", "node.js"],
     "overall_score": 75.3,
     ...
   }
"""
