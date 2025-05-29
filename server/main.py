# backend/app/main.py
from fastapi import FastAPI, HTTPException, Depends, Header, status, Query , APIRouter
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from router import router
import crud
from models import (
    PersonalIdRequest,
    VoteTokenResponse,
    EncryptedVotePayload,
    Vote, Voter,
    VoteSubmissionResponse,
)
from core import settings

app = FastAPI(
    title="Secure Voting System - Vote Collection API",
)

origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def app_startup_event():
    print("MAIN: Application startup...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database_instance = client[settings.DATABASE_NAME]
    await init_beanie(
        database=database_instance,
        document_models=[
            Voter,
            Vote,
        ],
    )
    print(f"MAIN: Connected to MongoDB: '{settings.MONGODB_URL}', DB: '{settings.DATABASE_NAME}'")
    print(f"MAIN: Beanie initialized with models: {[Voter.__name__, Vote.__name__]}")


async def verify_and_get_voter_from_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header is missing.")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization scheme. Use 'Bearer <token>'.")
    token = authorization.split(" ")[1]
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vote token is missing in Bearer token.")
    voter = await crud.get_voter_by_vote_token(token)
    if not voter:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or unknown vote token.")
    if voter.has_voted:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This vote token has already been used to cast a vote.")
    return voter


@app.post("/get-vote-token", response_model=VoteTokenResponse, tags=["Voting Process"])
async def get_vote_token_endpoint(request: PersonalIdRequest):
    print(f"MAIN: Request to /get-vote-token for personal_id: {request.personal_id}")
    voter = await crud.find_or_create_voter(request.personal_id)
    if not voter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personal ID is not eligible or could not be processed.")
    if voter.has_voted:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This Personal ID has already cast a vote.")
    if voter.has_received_token and voter.vote_token:
        return VoteTokenResponse(vote_token=voter.vote_token)
    new_vote_token = str(uuid.uuid4())
    updated_voter = await crud.issue_token_to_voter(voter, new_vote_token)
    if updated_voter and updated_voter.vote_token:
        return VoteTokenResponse(vote_token=updated_voter.vote_token)
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to issue vote token.")


@app.post("/submit-vote", response_model=VoteSubmissionResponse, status_code=status.HTTP_201_CREATED, tags=["Voting Process"])
async def submit_vote_endpoint(
    payload: EncryptedVotePayload,
    current_voter: Voter = Depends(verify_and_get_voter_from_token)
):
    print(f"MAIN: Request to /submit-vote from voter (token: {current_voter.vote_token})")
    if not await crud.mark_voter_as_voted(current_voter):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to mark token/voter as used.")
    
    stored_vote = await crud.store_vote(payload.encrypted_vote, current_voter.vote_token)
    print(f"MAIN: Vote stored successfully, vote_id: {stored_vote.id}, status: {stored_vote.status}")

    return VoteSubmissionResponse(
        message="Encrypted vote submitted successfully and is pending external processing.",
        vote_id=str(stored_vote.id),
        submitted_at=stored_vote.submitted_at
    )


@app.get("/", status_code=status.HTTP_200_OK, tags=["System"])
async def health_check():
    return {"status": "ok", "message": "Voting System - Vote Collection API is running."}