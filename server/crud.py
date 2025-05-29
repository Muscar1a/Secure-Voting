from typing import List, Optional
from models import Voter, Vote, VoteStatus, EncryptedVoteRecord
from datetime import datetime, timezone

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


async def store_vote(encrypted_data: str, token_used: str) -> Vote:
    new_vote = Vote(
        encrypted_vote_data=encrypted_data,
        vote_token_used=token_used,
        status=VoteStatus.RECEIVED_PENDING_PROCESSING,
    )
    await new_vote.insert()
    print(f"CRUD: Stored encrypted vote (ID: {new_vote.id}) with token {token_used}, status: {new_vote.status}")
    return new_vote

async def get_votes_for_processing(limit: int = 1000, skip: int = 0) -> List[Vote]:
    query = Vote.find(Vote.status == VoteStatus.RECEIVED_PENDING_PROCESSING)
    
    return await query.skip(skip).limit(limit).to_list()


async def get_all_votes() -> List[Vote]:
    return await Vote.find_all().to_list()

async def get_all_voters() -> List[Voter]:
    return await Voter.find_all().to_list()

async def get_pending_votes() -> List[Vote]:
    return await Vote.find(Vote.status == VoteStatus.RECEIVED_PENDING_PROCESSING).to_list()

async def delete_all_votes() -> int:
    result = await Vote.get_motor_collection().delete_many({})
    print(f"CRUD: Deleted {result.deleted_count} votes")
    return result.deleted_count