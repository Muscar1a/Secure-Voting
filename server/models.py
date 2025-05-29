# backend/app/models.py
from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, List # Đảm bảo có List
from datetime import datetime, timezone
from enum import Enum

# --- PersonalIdRequest, VoteTokenResponse, EncryptedVotePayload giữ nguyên ---
class PersonalIdRequest(BaseModel):
    personal_id: str

class VoteTokenResponse(BaseModel):
    vote_token: str

class EncryptedVotePayload(BaseModel):
    encrypted_vote: str
# --- Hết phần giữ nguyên ---

class Voter(Document): # Model Voter giữ nguyên
    personal_id: str = Field(..., unique=True)
    has_received_token: bool = Field(default=False)
    vote_token: Optional[str] = Field(default=None, unique=True, sparse=True)
    has_voted: bool = Field(default=False)
    token_issued_at: Optional[datetime] = Field(default=None)
    voted_at: Optional[datetime] = Field(default=None)

    class Settings:
        name = "voters"

# Cập nhật Enum cho trạng thái của phiếu bầu
class VoteStatus(str, Enum):
    RECEIVED_PENDING_PROCESSING = "received_pending_processing" # Phiếu đã nhận, chờ được lấy để xử lý (bởi Tally Authorities / Homomorphic system)
    PROCESSING_BY_AUTHORITIES = "processing_by_authorities" # (Tùy chọn) Đã được gửi/truy xuất bởi các Tally Authority
    TALLIED_EXTERNALLY = "tallied_externally" # (Tùy chọn) Được đánh dấu là đã kiểm bởi hệ thống bên ngoài

class Vote(Document):
    encrypted_vote_data: str = Field(...)
    vote_token_used: str = Field(..., index=True) # Giữ lại để liên kết (dù có thể không cần cho ẩn danh sau này)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decrypted_candidate: Optional[str] = None # decrypt
    shuffled_index: Optional[int] = None #mixnet    
    
    # --- Các trường cập nhật/mới cho kịch bản này ---
    status: VoteStatus = Field(default=VoteStatus.RECEIVED_PENDING_PROCESSING)
    # election_id: Optional[str] = Field(default="default_election", index=True) # Nên có để quản lý nhiều cuộc bỏ phiếu
    # sequence_number: Optional[int] = Field(default=None, index=True) # (Tùy chọn) Để đảm bảo thứ tự hoặc làm bulletin board

    class Settings:
        name = "votes"
        indexes = [
            "vote_token_used",
            "status",
            # "election_id",
            # "sequence_number",
        ]

# Model cho response khi tạo vote thành công
class VoteSubmissionResponse(BaseModel): # Giữ nguyên
    message: str
    vote_id: str
    submitted_at: datetime

# --- Model TallyResult và TallyResultItem không còn cần thiết ở server này ---
# Vì việc kiểm phiếu (tallying) sẽ diễn ra ở nơi khác.
# Bạn có thể giữ lại nếu server này cũng cần lưu kết quả cuối cùng sau khi nhận từ các authority.
# Nhưng theo yêu cầu "không cần giải mã", thì tạm thời có thể bỏ qua.

# --- Model mới để trả về danh sách các phiếu mã hóa cho Tally Authorities ---
class EncryptedVoteRecord(BaseModel):
    vote_id: str
    encrypted_vote_data: str
    submitted_at: datetime
    # election_id: Optional[str] # Nếu dùng
    # sequence_number: Optional[int] # Nếu dùng