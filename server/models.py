# backend/app/models.py
from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum

class PersonalIdRequest(BaseModel):
    personal_id: str

class VoteTokenResponse(BaseModel):
    vote_token: str

class EncryptedVotePayload(BaseModel):
    encrypted_vote: str

class Voter(Document):
    personal_id: str = Field(..., unique=True)
    has_received_token: bool = Field(default=False)
    vote_token: Optional[str] = Field(default=None, unique=True, sparse=True)
    has_voted: bool = Field(default=False)
    token_issued_at: Optional[datetime] = Field(default=None)
    voted_at: Optional[datetime] = Field(default=None)

    class Settings:
        name = "voters"


class VoteStatus(str, Enum):
    RECEIVED_PENDING_PROCESSING = "received_pending_processing"
    PROCESSING_BY_AUTHORITIES = "processing_by_authorities"
    TALLIED_EXTERNALLY = "tallied_externally"

class Vote(Document):
    encrypted_vote_data: str = Field(...)
    vote_token_used: str = Field(..., index=True)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decrypted_candidate: Optional[str] = None
    shuffled_index: Optional[int] = None
    
    status: VoteStatus = Field(default=VoteStatus.RECEIVED_PENDING_PROCESSING)
    
    class Settings:
        name = "votes"
        indexes = [
            "vote_token_used",
            "status",
        ]

class VoteSubmissionResponse(BaseModel):
    message: str
    vote_id: str
    submitted_at: datetime


class EncryptedVoteRecord(BaseModel):
    vote_id: str
    encrypted_vote_data: str
    submitted_at: datetime