# backend/app/main.py
from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware # Thêm CORS
from typing import List
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

import crud  # Import your CRUD operations
from models import (
    PersonalIdRequest,
    VoteTokenResponse,
    EncryptedVotePayload,
    Vote,
    Voter,
    VoteSubmissionResponse
)
from core import settings

app = FastAPI(
    title="Secure Voting System API",
    description="API for a secure electronic voting system prototype.",
    version="0.1.0"
)

# --- CORS Middleware ---
# Cho phép frontend (chạy ở port khác) gọi API này
# Trong production, bạn nên cấu hình origins cụ thể hơn
origins = [
    "http://localhost:3000", # React default dev port
    "http://127.0.0.1:3000",
    # Thêm các origin khác nếu cần
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Cho phép tất cả các method (GET, POST, etc.)
    allow_headers=["*"], # Cho phép tất cả các header
)


@app.on_event("startup")
async def app_startup_event():
    """
    Initialize Beanie ORM with MongoDB connection on application startup.
    """
    print("MAIN: Application startup...")
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        # Access the database instance using the name from settings
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

        # Optional: Populate initial voters if the collection is empty or specific IDs are missing
        # Điều này hữu ích cho việc thiết lập môi trường dev/test
        # await crud.populate_initial_voters_if_empty() # Chạy 1 lần khi setup

    except Exception as e:
        print(f"MAIN: CRITICAL - Failed to connect to MongoDB or initialize Beanie: {e}")
        # Bạn có thể quyết định dừng ứng dụng ở đây nếu DB là bắt buộc
        # import sys
        # sys.exit("MongoDB connection failed.")


# --- Dependency for verifying vote token ---
async def verify_and_get_voter_from_token(authorization: str = Header(None)): # Cho phép token là Optional
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing."
        )
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme. Use 'Bearer <token>'.",
        )
    token = authorization.split(" ")[1]
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vote token is missing in Bearer token.",
        )

    voter = await crud.get_voter_by_vote_token(token)
    if not voter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or unknown vote token.",
        )
    if voter.has_voted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This vote token has already been used to cast a vote.",
        )
    return voter # Trả về voter object, không chỉ token string

# --- API Endpoints ---

@app.post("/get-vote-token", response_model=VoteTokenResponse, tags=["Voting Process"])
async def get_vote_token_endpoint(request: PersonalIdRequest):
    """
    Allows a user to request a vote token using their personal ID.
    Verifies eligibility and ensures a token is issued only once per eligible, non-voted user.
    """
    print(f"MAIN: Request to /get-vote-token for personal_id: {request.personal_id}")
    voter = await crud.find_or_create_voter(request.personal_id)

    if not voter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personal ID is not eligible or could not be processed."
        )

    if voter.has_voted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This Personal ID has already cast a vote."
        )

    if voter.has_received_token and voter.vote_token:
        print(f"MAIN: Voter {voter.personal_id} already has token {voter.vote_token}. Returning existing token.")
        return VoteTokenResponse(vote_token=voter.vote_token)

    new_vote_token = str(uuid.uuid4())
    updated_voter = await crud.issue_token_to_voter(voter, new_vote_token)

    if updated_voter and updated_voter.vote_token:
        print(f"MAIN: Issued new token {updated_voter.vote_token} to voter {updated_voter.personal_id}")
        return VoteTokenResponse(vote_token=updated_voter.vote_token)
    else:
        # Trường hợp này không nên xảy ra nếu logic ở trên đúng
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to issue vote token due to an internal error.")


@app.post("/submit-vote", response_model=VoteSubmissionResponse, status_code=status.HTTP_201_CREATED, tags=["Voting Process"])
async def submit_vote_endpoint(
    payload: EncryptedVotePayload,
    current_voter: Voter = Depends(verify_and_get_voter_from_token) # Dependency đã trả về Voter object
):
    """
    Submits an encrypted vote. Requires a valid, unused vote token.
    Marks the token as used and stores the encrypted vote.
    """
    print(f"MAIN: Request to /submit-vote from voter (token: {current_voter.vote_token})")
    # current_voter đã được verify_and_get_voter_from_token kiểm tra là hợp lệ và chưa vote

    # Đánh dấu cử tri này là đã bỏ phiếu
    if not await crud.mark_voter_as_voted(current_voter):
        # Lỗi này không nên xảy ra nếu current_voter hợp lệ
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to mark token/voter as used.")

    # Lưu phiếu bầu đã mã hóa
    stored_vote = await crud.store_vote(payload.encrypted_vote, current_voter.vote_token) # Truyền vote_token từ current_voter
    print(f"MAIN: Vote stored successfully, vote_id: {stored_vote.id}")

    return VoteSubmissionResponse(
        message="Vote submitted successfully.",
        vote_id=str(stored_vote.id), # _id của MongoDB là ObjectId, cần convert sang str
        submitted_at=stored_vote.submitted_at
    )


# --- Admin/Debug Endpoints ---
@app.get("/admin/voters", response_model=List[Voter], tags=["Admin"])
async def get_all_voters_admin():
    """(Admin) Retrieves all voter records."""
    print("MAIN: Request to /admin/voters")
    return await crud.get_all_voters()

@app.get("/admin/votes", response_model=List[Vote], tags=["Admin"])
async def get_all_votes_admin():
    """(Admin) Retrieves all submitted (encrypted) vote records."""
    print("MAIN: Request to /admin/votes")
    return await crud.get_all_votes()

@app.post("/admin/populate-initial-voters", status_code=status.HTTP_201_CREATED, tags=["Admin"])
async def populate_initial_voters_endpoint():
    """(Admin) Populates the database with initial eligible voters if they don't exist."""
    print("MAIN: Request to /admin/populate-initial-voters")
    count = await crud.populate_initial_voters_if_empty()
    if count > 0:
        return {"message": f"Successfully populated {count} initial voters into the database."}
    return {"message": "No new voters were added. They might already exist or the eligible list is empty."}

# --- Health Check Endpoint ---
@app.get("/health", status_code=status.HTTP_200_OK, tags=["System"])
async def health_check():
    """Performs a simple health check."""
    return {"status": "ok", "message": "Voting System API is running."}