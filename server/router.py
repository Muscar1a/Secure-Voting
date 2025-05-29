from fastapi import APIRouter
from crud import get_all_votes, delete_all_votes
from models import Vote
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
    1) Mixnet: re-encrypt & shuffle all decrypted votes
    2) Tally: decrypt shuffled ciphertexts and count
    """
    public_key = load_public_key()
    private_key = load_private_key()

    # 1) Mixnet: re-encrypt & shuffle
    votes = await get_all_votes()
    # Re-encrypt using PKCS#1 v1.5
    for vote in votes:
        if vote.decrypted_candidate is None:
            # Nếu chưa có plaintext, decrypt tạm để mixnet (nếu cần)
            encrypted_bytes = base64.b64decode(vote.encrypted_vote_data)
            decrypted = private_key.decrypt(encrypted_bytes, padding.PKCS1v15())
            pt = decrypted  # giữ plaintext
        else:
            pt = vote.decrypted_candidate.encode("utf-8")

        # Tái mã hóa
        ct = public_key.encrypt(pt, padding.PKCS1v15())
        vote.encrypted_vote_data = base64.b64encode(ct).decode()

    # Shuffle order (có thể gán vào shuffled_index nếu muốn)
    random.shuffle(votes)
    # Lưu lại mọi thay đổi (encrypted_vote_data)
    for vote in votes:
        await vote.save()

    # 2) Tally: decrypt & count
    tally = {}
    for vote in votes:
        encrypted_bytes = base64.b64decode(vote.encrypted_vote_data)
        decrypted_bytes = private_key.decrypt(encrypted_bytes, padding.PKCS1v15())
        candidate = decrypted_bytes.decode("utf-8")
        tally[candidate] = tally.get(candidate, 0) + 1

    return {"tally": tally}

@router.delete("/admin/reset_votes")
async def reset_votes():
    deleted = await delete_all_votes()
    return {"deleted_votes": deleted}

@router.get("/debug/votes_count")
async def votes_count():
    votes = await get_all_votes()
    return {"total_votes": len(votes)}

# MIXNET ROUTER
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