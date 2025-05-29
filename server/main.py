# backend/app/main.py
from fastapi import FastAPI, HTTPException, Depends, Header, status, Query # Thêm Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

import crud
from models import (
    PersonalIdRequest,
    VoteTokenResponse,
    EncryptedVotePayload,
    Vote, Voter,
    VoteSubmissionResponse,
    VoteStatus, # Thêm VoteStatus
    EncryptedVoteRecord # Thêm EncryptedVoteRecord cho response
)
from core import settings
# Bỏ: from crypto_services import decrypt_vote_rsa

app = FastAPI(
    title="Secure Voting System - Vote Collection API", # Tên có thể thay đổi để phản ánh vai trò
    description="API for collecting and storing encrypted votes, to be processed by external Tally Authorities or Homomorphic Tally systems.",
    version="0.3.0" # Tăng version
)

# --- CORS Middleware --- (Giữ nguyên)
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            # Bỏ TallyResult nếu không dùng ở server này
        ],
    )
    print(f"MAIN: Connected to MongoDB: '{settings.MONGODB_URL}', DB: '{settings.DATABASE_NAME}'")
    print(f"MAIN: Beanie initialized with models: {[Voter.__name__, Vote.__name__]}") # Cập nhật list model
    # await crud.populate_initial_voters_if_empty()


# --- Dependency for verifying vote token --- (Giữ nguyên)
async def verify_and_get_voter_from_token(authorization: str = Header(None)):
    # ... (code giữ nguyên)
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

# --- API Endpoints ---

# Endpoint /get-vote-token (Giữ nguyên)
@app.post("/get-vote-token", response_model=VoteTokenResponse, tags=["Voting Process"])
async def get_vote_token_endpoint(request: PersonalIdRequest):
    # ... (code giữ nguyên)
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


# Endpoint /submit-vote (Logic `store_vote` đã được cập nhật)
@app.post("/submit-vote", response_model=VoteSubmissionResponse, status_code=status.HTTP_201_CREATED, tags=["Voting Process"])
async def submit_vote_endpoint(
    payload: EncryptedVotePayload,
    current_voter: Voter = Depends(verify_and_get_voter_from_token)
):
    print(f"MAIN: Request to /submit-vote from voter (token: {current_voter.vote_token})")
    if not await crud.mark_voter_as_voted(current_voter):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to mark token/voter as used.")
    
    # election_id = "default_election" # Hoặc lấy từ request/config
    stored_vote = await crud.store_vote(payload.encrypted_vote, current_voter.vote_token) # , election_id=election_id
    print(f"MAIN: Vote stored successfully, vote_id: {stored_vote.id}, status: {stored_vote.status}")

    return VoteSubmissionResponse(
        message="Encrypted vote submitted successfully and is pending external processing.",
        vote_id=str(stored_vote.id),
        submitted_at=stored_vote.submitted_at
    )

# --- ENDPOINT MỚI CHO TALLY AUTHORITIES / HOMOMORPHIC SYSTEM ---

@app.get("/external/get-encrypted-votes", response_model=List[EncryptedVoteRecord], tags=["External Processing"])
async def get_encrypted_votes_for_external_processing(
    # election_id: Optional[str] = Query("default_election", description="ID of the election to fetch votes for."),
    limit: int = Query(100, ge=1, le=1000, description="Number of votes to retrieve."),
    skip: int = Query(0, ge=0, description="Number of votes to skip (for pagination).")
    # Có thể thêm tham số xác thực cho Tally Authority ở đây (ví dụ: API key)
):
    """
    Endpoint cho các Tally Authority hoặc hệ thống kiểm phiếu đồng cấu
    truy xuất danh sách các phiếu bầu đã mã hóa đang chờ xử lý.
    """
    print(f"MAIN: Request to /external/get-encrypted-votes (limit={limit}, skip={skip})")
    # TODO: Implement robust authentication/authorization for this endpoint.
    
    # votes_from_db = await crud.get_votes_for_processing(limit=limit, skip=skip, election_id=election_id)
    votes_from_db = await crud.get_votes_for_processing(limit=limit, skip=skip)
    
    response_votes = []
    vote_ids_retrieved = []
    for vote_doc in votes_from_db:
        response_votes.append(EncryptedVoteRecord(
            vote_id=str(vote_doc.id),
            encrypted_vote_data=vote_doc.encrypted_vote_data,
            submitted_at=vote_doc.submitted_at
            # election_id=vote_doc.election_id, # Nếu dùng
            # sequence_number=vote_doc.sequence_number # Nếu dùng
        ))
        vote_ids_retrieved.append(str(vote_doc.id))

    # (Tùy chọn) Cập nhật trạng thái các phiếu đã lấy thành PROCESSING_BY_AUTHORITIES
    # if vote_ids_retrieved:
    #    await crud.update_vote_status_batch(vote_ids_retrieved, VoteStatus.PROCESSING_BY_AUTHORITIES)
    #    print(f"MAIN: Marked {len(vote_ids_retrieved)} votes as PROCESSING_BY_AUTHORITIES.")
        
    return response_votes

# (Tùy chọn) Endpoint để Tally Authority thông báo rằng việc kiểm phiếu đã hoàn tất cho một số phiếu
# @app.post("/external/mark-votes-tallied", status_code=status.HTTP_200_OK, tags=["External Processing"])
# async def mark_votes_as_tallied_externally(vote_ids: List[str]):
#     """
#     (Tùy chọn) Endpoint cho hệ thống bên ngoài đánh dấu các phiếu đã được kiểm.
#     """
#     print(f"MAIN: Request to /external/mark-votes-tallied for {len(vote_ids)} votes.")
#     # TODO: Implement robust authentication/authorization.
#     updated_count = await crud.update_vote_status_batch(vote_ids, VoteStatus.TALLIED_EXTERNALLY)
#     return {"message": f"Successfully marked {updated_count} votes as TALLIED_EXTERNALLY."}


# --- Admin/Debug Endpoints --- (Giữ nguyên các endpoint xem dữ liệu)
@app.get("/admin/voters", response_model=List[Voter], tags=["Admin - Data"])
async def get_all_voters_admin():
    return await crud.get_all_voters()

@app.get("/admin/votes", response_model=List[Vote], tags=["Admin - Data"]) # Response model bây giờ là Vote đầy đủ
async def get_all_votes_admin():
    return await crud.get_all_votes()

@app.post("/admin/populate-initial-voters", status_code=status.HTTP_201_CREATED, tags=["Admin - Setup"])
async def populate_initial_voters_endpoint():
    count = await crud.populate_initial_voters_if_empty()
    if count > 0: return {"message": f"Successfully populated {count} initial voters."}
    return {"message": "No new voters were added."}

# Bỏ endpoint /admin/tally-votes và /admin/reset-tally vì server này không làm việc đó.
# Bỏ endpoint /results vì server này không tính toán kết quả.

# --- Health Check Endpoint --- (Giữ nguyên)
@app.get("/", status_code=status.HTTP_200_OK, tags=["System"])
async def health_check():
    return {"status": "ok", "message": "Voting System - Vote Collection API is running."}