from fastapi import APIRouter
from crud import get_all_votes, delete_all_votes, get_votes_for_processing
from models import Vote, VoteStatus
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
import base64, random


router = APIRouter()

def load_private_key():
    with open("private_key.pem", "rb") as key_file:
        return serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )

def load_public_key():
    with open("public_key.pem", "rb") as key_file:
        return serialization.load_pem_public_key(
            key_file.read()
        )

@router.post("/mixnet_and_tally")
async def mixnet_and_tally():
    """
    1) MIXNET: lấy vote pending, re-encrypt & shuffle → status PROCESSING_BY_AUTHORITIES
    2) TALLY: lấy vote đang processing, decrypt & count → status TALLIED_EXTERNALLY
    """
    public_key = load_public_key()
    private_key = load_private_key()

    # 1) MIXNET
    pending_votes = await get_votes_for_processing()  # status == RECEIVED_PENDING_PROCESSING
    # Re-encrypt + shuffle
    for vote in pending_votes:
        # Giải mã tạm nếu chưa có plaintext
        if vote.decrypted_candidate:
            pt_bytes = vote.decrypted_candidate.encode("utf-8")
        else:
            enc = base64.b64decode(vote.encrypted_vote_data)
            pt_bytes = private_key.decrypt(enc, padding.PKCS1v15())

        # Tái mã hóa
        ct_bytes = public_key.encrypt(pt_bytes, padding.PKCS1v15())
        vote.encrypted_vote_data = base64.b64encode(ct_bytes).decode()
        vote.status = VoteStatus.PROCESSING_BY_AUTHORITIES
        await vote.save()

    # Xáo trộn danh sách pending_votes
    random.shuffle(pending_votes)
    # (Tuỳ chọn) gán shuffled_index nếu bạn đã có field

    # 2) TALLY
    # Giờ lấy tất cả phiếu đã chuyển status sang PROCESSING_BY_AUTHORITIES
    processing_votes = await Vote.find(
        Vote.status == VoteStatus.PROCESSING_BY_AUTHORITIES
    ).to_list()

    tally = {}
    for vote in processing_votes:
        enc = base64.b64decode(vote.encrypted_vote_data)
        dec = private_key.decrypt(enc, padding.PKCS1v15())
        candidate = dec.decode("utf-8")

        # Đếm
        tally[candidate] = tally.get(candidate, 0) + 1

        # Cập nhật status & lưu decrypted_candidate
        vote.decrypted_candidate = candidate
        vote.status = VoteStatus.TALLIED_EXTERNALLY
        await vote.save()

    return {"tally": tally}

@router.get("/results")
async def process_and_get_results():
    """
    1) Lấy vote mới (RECEIVED_PENDING_PROCESSING), mixnet → PROCESSING_BY_AUTHORITIES
    2) Tally những vote này → TALLIED_EXTERNALLY
    3) Đếm toàn bộ vote TALLIED_EXTERNALLY và return tổng
    """
    private_key = load_private_key()
    public_key  = load_public_key()

    # 1) MIXNET & TALLY mới nhất
    pending = await get_votes_for_processing()  # RECEIVED_PENDING_PROCESSING
    # Re-encrypt + shuffle + mark processing
    for vote in pending:
        # nếu đã lưu decrypted_candidate thì dùng, còn không thì decrypt tạm
        if vote.decrypted_candidate:
            pt = vote.decrypted_candidate.encode()
        else:
            ct = base64.b64decode(vote.encrypted_vote_data)
            pt = private_key.decrypt(ct, padding.PKCS1v15())
        # re-encrypt
        new_ct = public_key.encrypt(pt, padding.PKCS1v15())
        vote.encrypted_vote_data = base64.b64encode(new_ct).decode()
        vote.status = VoteStatus.PROCESSING_BY_AUTHORITIES
        await vote.save()

    # shuffle order
    random.shuffle(pending)

    # decrypt & tally những vote vừa processing
    for vote in pending:
        ct = base64.b64decode(vote.encrypted_vote_data)
        pt = private_key.decrypt(ct, padding.PKCS1v15())
        candidate = pt.decode()
        # tallied
        vote.decrypted_candidate = candidate
        vote.status = VoteStatus.TALLIED_EXTERNALLY
        await vote.save()

    # 2) Đếm toàn bộ vote đã tally
    all_tallied = await Vote.find(Vote.status == VoteStatus.TALLIED_EXTERNALLY).to_list()
    total = {}
    for vote in all_tallied:
        cand = vote.decrypted_candidate
        total[cand] = total.get(cand, 0) + 1

    return {"tally": total}

@router.delete("/admin/reset_votes")
async def reset_votes():
    deleted = await delete_all_votes()
    return {"deleted_votes": deleted}

@router.get("/debug/votes_count")
async def votes_count():
    votes = await get_all_votes()
    return {"total_votes": len(votes)}

# MIXNET endpoint nếu cần mixnet shuffle thủ công
import random
@router.post("/mixnet/shuffle")
async def mixnet_shuffle():
    """
    Re-encrypt và shuffle tất cả phiếu đã giải mã (decrypted_candidate).
    Gán shuffled_index để ghi thứ tự mới.
    """
    public_key = load_public_key()
    votes = await get_all_votes()

    # Re-encrypt plaintext candidate thành ciphertext mới
    for vote in votes:
        if not getattr(vote, "decrypted_candidate", None):
            # Skip phiếu chưa giải mã
            continue
        pt = vote.decrypted_candidate.encode("utf-8")
        ct_bytes = public_key.encrypt(pt, padding.PKCS1v15())
        vote.encrypted_vote_data = base64.b64encode(ct_bytes).decode()

    # Shuffle order bằng shuffled_index
    indices = list(range(len(votes)))
    random.shuffle(indices)
    for idx, vote in zip(indices, votes):
        vote.shuffled_index = idx
        await vote.save()

    return {"shuffled": len(votes)}