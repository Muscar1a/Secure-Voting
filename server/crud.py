# backend/app/crud.py
from typing import List, Optional
from models import Voter, Vote
import datetime
import uuid # Dùng nếu bạn cần UUID tùy chỉnh, không cần cho vote_token vì đã dùng str(uuid.uuid4())

# --- Danh sách cử tri hợp lệ ban đầu (có thể đọc từ file CSV, JSON, ...) ---
INITIAL_ELIGIBLE_VOTER_IDS = ["MSV123", "MSV456", "CCCD789", "TEACHER001", "USER005"]

async def get_initial_voter_ids() -> List[str]:
    return INITIAL_ELIGIBLE_VOTER_IDS

async def populate_initial_voters_if_empty() -> int:
    """
    Populates the Voter collection with initial eligible voters if they don't exist yet.
    Returns the number of newly added voters.
    """
    count = 0
    eligible_ids = await get_initial_voter_ids()
    for pid in eligible_ids:
        existing_voter = await Voter.find_one(Voter.personal_id == pid)
        if not existing_voter:
            new_voter = Voter(personal_id=pid)
            await new_voter.insert()
            count += 1
            print(f"CRUD: Added initial voter: {pid}")
    if count > 0:
        print(f"CRUD: Successfully populated {count} initial voters.")
    return count

async def find_or_create_voter(personal_id: str) -> Optional[Voter]:
    """
    Finds a voter by personal_id. If not found AND the personal_id is in the
    eligible list, creates a new voter document.
    Returns the Voter object or None if not eligible.
    """
    voter = await Voter.find_one(Voter.personal_id == personal_id)
    if voter:
        return voter

    # If voter not found, check if they are eligible to be created
    eligible_ids = await get_initial_voter_ids()
    if personal_id in eligible_ids:
        new_voter = Voter(personal_id=personal_id)
        await new_voter.insert()
        print(f"CRUD: Created new voter: {personal_id}")
        return new_voter
    return None # Not found and not eligible to be created

async def get_voter_by_personal_id(personal_id: str) -> Optional[Voter]:
    return await Voter.find_one(Voter.personal_id == personal_id)

async def get_voter_by_vote_token(token: str) -> Optional[Voter]:
    if not token:
        return None
    return await Voter.find_one(Voter.vote_token == token)

async def issue_token_to_voter(voter: Voter, token_value: str) -> Optional[Voter]:
    """
    Updates the voter document with the new token and issuance timestamp.
    """
    voter.vote_token = token_value
    voter.has_received_token = True
    voter.token_issued_at = datetime.datetime.utcnow()
    await voter.save() # Beanie's save handles updates if document already exists
    print(f"CRUD: Issued token {token_value} to voter {voter.personal_id}")
    return voter

async def mark_voter_as_voted(voter: Voter) -> bool:
    """
    Marks a Voter object as having voted and sets the voted_at timestamp.
    """
    if voter:
        voter.has_voted = True
        voter.voted_at = datetime.datetime.utcnow()
        await voter.save()
        print(f"CRUD: Marked voter {voter.personal_id} (token: {voter.vote_token}) as voted.")
        return True
    return False

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