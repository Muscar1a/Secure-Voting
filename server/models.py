from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


class PersonalIdRequest(BaseModel):
    personal_id: str

class VoteTokenResponse(BaseModel):
    vote_token: str

class EncryptedVotePayload(BaseModel):
    encrypted_vote: str


class Voter(Document):
    personal_id: str = Field(..., unique=True)
    has_received_token: bool = Field(default=False, description="Has this voter received a vote token?")
    vote_token: Optional[str] = Field(default=None, unique=True, sparse=True)
    has_voted: bool = Field(default=False)
    
    token_issued_at: Optional[datetime] = Field(default=None, description="Timestamp when the token was issued")
    voted_at: Optional[datetime] = Field(default=None, description="Timestamp when the vote was cast")

    class Settings:
        name = "voters" # Tên collection trong MongoDB
        # indexes = [ # Bạn có thể định nghĩa index ở đây hoặc trong init script của MongoDB
        #     "personal_id",
        #     [("vote_token", 1), {"unique": True, "sparse": True}],
        # ]


class Vote(Document):
    # Beanie tự động quản lý trường _id (ObjectId)
    # Nếu bạn muốn id tùy chỉnh, bạn có thể thêm:
    # vote_custom_id: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)

    encrypted_vote_data: str = Field(...)
    vote_token_used: str = Field(..., index=True)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of vote submission")


    class Settings:
        name = "votes"
        
# Model cho response khi tạo vote thành công (nếu bạn muốn trả về nhiều hơn là message)
class VoteSubmissionResponse(BaseModel):
    message: str
    vote_id: str # Sẽ là _id của document Vote sau khi lưu
    submitted_at: datetime