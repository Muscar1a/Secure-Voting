# backend/app/crud.py
from typing import List, Optional
from models import Voter, Vote, VoteStatus, EncryptedVoteRecord # Thêm EncryptedVoteRecord, cập nhật VoteStatus
from datetime import datetime, timezone
# import uuid # Vẫn có thể dùng nếu Voter cần

# --- populate_initial_voters_if_empty, find_or_create_voter, get_voter_by_personal_id, get_voter_by_vote_token, issue_token_to_voter, mark_voter_as_voted giữ nguyên ---
async def populate_initial_voters_if_empty() -> int:
    print("CRUD: populate_initial_voters_if_empty - No initial voter list defined. Skipping population.")
    return 0

async def find_or_create_voter(personal_id: str) -> Voter:
    voter = await Voter.find_one(Voter.personal_id == personal_id)
    if voter:
        print(f"CRUD: Found existing voter: {personal_id}")
        return voter
    else:
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

async def issue_token_to_voter(voter: Voter, token_value: str) -> Voter:
    voter.vote_token = token_value
    voter.has_received_token = True
    voter.token_issued_at = datetime.now(timezone.utc)
    await voter.save()
    print(f"CRUD: Issued token {token_value} to voter {voter.personal_id}")
    return voter

async def mark_voter_as_voted(voter: Voter) -> bool:
    voter.has_voted = True
    voter.voted_at = datetime.now(timezone.utc)
    await voter.save()
    print(f"CRUD: Marked voter {voter.personal_id} (token: {voter.vote_token}) as voted.")
    return True
# --- Hết phần giữ nguyên ---


async def store_vote(encrypted_data: str, token_used: str) -> Vote: # election_id: Optional[str] = "default_election"
    """
    Creates and inserts a new Vote document with RECEIVED_PENDING_PROCESSING status.
    """
    new_vote = Vote(
        encrypted_vote_data=encrypted_data,
        vote_token_used=token_used,
        status=VoteStatus.RECEIVED_PENDING_PROCESSING,
        # election_id=election_id # Nếu dùng
        # sequence_number có thể được gán bằng một counter hoặc dựa trên thời gian/id
    )
    await new_vote.insert()
    print(f"CRUD: Stored encrypted vote (ID: {new_vote.id}) with token {token_used}, status: {new_vote.status}")
    return new_vote

async def get_votes_for_processing(limit: int = 1000, skip: int = 0) -> List[Vote]: # election_id: Optional[str] = "default_election"
    """
    Lấy danh sách các phiếu bầu (chỉ ciphertext) đang ở trạng thái RECEIVED_PENDING_PROCESSING.
    Hữu ích cho Tally Authorities hoặc hệ thống Homomorphic Tally truy xuất.
    """
    query = Vote.find(Vote.status == VoteStatus.RECEIVED_PENDING_PROCESSING)
    # if election_id:
    #     query = query.find(Vote.election_id == election_id)
    
    return await query.skip(skip).limit(limit).to_list()

"""
async def update_vote_status_batch(vote_ids: List[str], new_status: VoteStatus):
    (Tùy chọn) Cập nhật trạng thái của một loạt phiếu bầu.
    Ví dụ: sau khi các Tally Authority đã nhận được phiếu, đánh dấu chúng là PROCESSING_BY_AUTHORITIES.
    # Beanie không hỗ trợ trực tiếp update_many với list các ID theo cách đơn giản như Pymongo.
    # Bạn có thể lặp qua hoặc sử dụng truy vấn $in nếu Beanie hỗ trợ.
    # Cách tiếp cận đơn giản hơn cho Beanie là từng phiếu một hoặc tìm cách dùng raw Pymongo.
    # Ví dụ với $in (kiểm tra docs của Beanie cho cách tốt nhất):
    updated_result = await Vote.find(Vote.id.is_in([object_id_from_str(vid) for vid in vote_ids])).update(
        {"$set": {"status": new_status.value}} # Cần .value khi set trực tiếp giá trị Enum
    )
    # Chú ý: object_id_from_str là một hàm tiện ích bạn cần tự tạo hoặc import (từ bson.objectid import ObjectId)
    # Và đảm bảo vote_ids là list các ObjectId hoặc string ID hợp lệ.
    # Đây là ví dụ, cần kiểm tra cú pháp chính xác của Beanie cho update với $in.
    # Cách an toàn hơn là lặp:
    count = 0
    for vote_id_str in vote_ids:
        try:
            from bson import ObjectId # Đặt import ở đây để tránh lỗi nếu không dùng
            vote_obj_id = ObjectId(vote_id_str)
            vote = await Vote.get(vote_obj_id)
            if vote:
                vote.status = new_status
                await vote.save()
                count += 1
        except Exception as e:
            print(f"CRUD: Error updating status for vote_id {vote_id_str}: {e}")

    print(f"CRUD: Attempted to update status for {len(vote_ids)} votes to {new_status}. Successfully updated {count}.")
    return count
"""

async def get_all_votes() -> List[Vote]: # Giữ nguyên
    return await Vote.find_all().to_list()

async def get_all_voters() -> List[Voter]: # Giữ nguyên
    return await Voter.find_all().to_list()

# Hàm populate_initial_voters_if_empty() giữ nguyên