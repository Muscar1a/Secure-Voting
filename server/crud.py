# backend/app/crud.py
from typing import List, Optional
# Đảm bảo rằng import này trỏ đúng đến file models.py của bạn
# Nếu crud.py và models.py cùng cấp trong thư mục app, thì import như sau:
from models import Voter, Vote
# Nếu chúng ở các vị trí khác, bạn cần điều chỉnh đường dẫn import.
from datetime import datetime, timezone
import uuid

# --- Không còn INITIAL_ELIGIBLE_VOTER_IDS và get_initial_voter_ids() ---

async def populate_initial_voters_if_empty() -> int:
    """
    Hàm này không còn ý nghĩa nhiều nếu không có danh sách cử tri ban đầu.
    Bạn có thể xóa nó hoặc giữ lại nếu có mục đích khác (ví dụ: tạo một vài voter mẫu).
    Hiện tại, sẽ trả về 0 vì không có logic populate.
    """
    print("CRUD: populate_initial_voters_if_empty - No initial voter list defined. Skipping population.")
    return 0

async def find_or_create_voter(personal_id: str) -> Voter: # Luôn trả về Voter
    """
    Finds a voter by personal_id. If not found, creates a new voter document.
    Returns the Voter object (either existing or newly created).
    """
    voter = await Voter.find_one(Voter.personal_id == personal_id)
    if voter:
        print(f"CRUD: Found existing voter: {personal_id}")
        return voter
    else:
        # Nếu cử tri không tồn tại, tạo mới mà không cần kiểm tra danh sách hợp lệ
        new_voter = Voter(personal_id=personal_id)
        await new_voter.insert()
        print(f"CRUD: Created new voter: {personal_id}")
        return new_voter

async def get_voter_by_personal_id(personal_id: str) -> Optional[Voter]:
    return await Voter.find_one(Voter.personal_id == personal_id)

async def get_voter_by_vote_token(token: str) -> Optional[Voter]:
    if not token:
        return None
    return await Voter.find_one(Voter.vote_token == token)

async def issue_token_to_voter(voter: Voter, token_value: str) -> Voter: # Luôn trả về Voter nếu thành công
    """
    Updates the voter document with the new token and issuance timestamp.
    """
    voter.vote_token = token_value
    voter.has_received_token = True
    voter.token_issued_at = datetime.now(timezone.utc)
    await voter.save() # Beanie's save handles updates if document already exists
    print(f"CRUD: Issued token {token_value} to voter {voter.personal_id}")
    return voter

async def mark_voter_as_voted(voter: Voter) -> bool:
    """
    Marks a Voter object as having voted and sets the voted_at timestamp.
    """
    # Không cần kiểm tra if voter nữa vì logic gọi hàm này thường đã đảm bảo voter tồn tại
    voter.has_voted = True
    voter.voted_at = datetime.now(timezone.utc)
    await voter.save()
    print(f"CRUD: Marked voter {voter.personal_id} (token: {voter.vote_token}) as voted.")
    return True


async def store_vote(encrypted_data: str, token_used: str) -> Vote:
    """
    Creates and inserts a new Vote document.
    """
    new_vote = Vote(
        encrypted_vote_data=encrypted_data,
        vote_token_used=token_used
        # submitted_at is handled by default_factory
    )
    await new_vote.insert()
    print(f"CRUD: Stored vote submitted with token {token_used}, vote_id: {new_vote.id}")
    return new_vote

async def get_all_votes() -> List[Vote]:
    return await Vote.find_all().to_list()

async def get_all_voters() -> List[Voter]:
    return await Voter.find_all().to_list()