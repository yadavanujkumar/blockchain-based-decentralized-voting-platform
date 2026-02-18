# src/api/endpoints.py

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, ValidationError
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import logging
import asyncio

# Initialize FastAPI app
app = FastAPI(
    title="Blockchain-Based Decentralized Voting Platform API",
    version="1.0.0",
    description="Enterprise-grade API for a blockchain-based decentralized voting platform."
)

# CORS Configuration
origins = ["https://your-frontend-domain.com", "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Logger setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Models
class UserRegistrationRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class ElectionCreationRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    start_time: datetime
    end_time: datetime

class VoteRequest(BaseModel):
    election_id: UUID
    candidate_id: UUID

class ResultResponse(BaseModel):
    election_id: UUID
    results: dict

# In-memory storage for demonstration purposes
users_db = {}
elections_db = {}
votes_db = {}

# Dependency for authentication (stub for demonstration)
async def get_current_user(request: Request):
    # Simulate JWT token validation
    token = request.headers.get("Authorization")
    if not token or token != "Bearer valid_token":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")
    return {"user_id": "12345", "username": "test_user"}

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP Exception: {exc.detail} | Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.status_code, "message": exc.detail}},
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"Validation Error: {exc.errors()} | Path: {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": 422, "message": "Validation error", "details": exc.errors()}},
    )

# Endpoints
@app.post("/v1/users/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserRegistrationRequest):
    if user.email in users_db:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user_id = str(uuid4())
    users_db[user.email] = {"id": user_id, "username": user.username, "password": user.password}
    logger.info(f"User registered: {user.email}")
    return {"id": user_id, "username": user.username, "email": user.email}

@app.post("/v1/elections", status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def create_election(election: ElectionCreationRequest):
    if election.start_time >= election.end_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid election time range")
    election_id = str(uuid4())
    elections_db[election_id] = {
        "id": election_id,
        "title": election.title,
        "description": election.description,
        "start_time": election.start_time,
        "end_time": election.end_time,
        "votes": {}
    }
    logger.info(f"Election created: {election.title}")
    return {"id": election_id, "title": election.title, "description": election.description}

@app.post("/v1/votes", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
async def cast_vote(vote: VoteRequest):
    if vote.election_id not in elections_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Election not found")
    if vote.candidate_id not in elections_db[vote.election_id]["votes"]:
        elections_db[vote.election_id]["votes"][vote.candidate_id] = 0
    elections_db[vote.election_id]["votes"][vote.candidate_id] += 1
    logger.info(f"Vote cast for candidate {vote.candidate_id} in election {vote.election_id}")
    return {"message": "Vote successfully cast"}

@app.get("/v1/elections/{election_id}/results", response_model=ResultResponse, dependencies=[Depends(get_current_user)])
async def get_results(election_id: UUID):
    if str(election_id) not in elections_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Election not found")
    results = elections_db[str(election_id)]["votes"]
    logger.info(f"Results retrieved for election {election_id}")
    return {"election_id": election_id, "results": results}

# Health Check Endpoints
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy"}

@app.get("/readiness", status_code=status.HTTP_200_OK)
async def readiness_check():
    return {"status": "ready"}

# Graceful Shutdown
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application gracefully...")
    await asyncio.sleep(1)  # Simulate cleanup tasks