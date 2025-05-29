// frontend/src/components/VotingForm.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import JSEncrypt from 'jsencrypt'; // For RSA Encryption

// !!! QUAN TRỌNG: Đây là PUBLIC KEY của hệ thống bỏ phiếu.
// Trong thực tế, bạn sẽ lấy nó từ một nguồn đáng tin cậy, không hardcode trực tiếp
// nếu nó thay đổi thường xuyên. Có thể fetch từ backend 1 lần.
// Đây là một ví dụ public key RSA (bạn cần tạo cặp khóa riêng của mình)
// Bạn có thể tạo cặp khóa RSA online hoặc dùng OpenSSL:
// openssl genrsa -out private_key.pem 2048
// openssl rsa -pubout -in private_key.pem -out public_key.pem
const VOTING_SYSTEM_PUBLIC_KEY = `-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzXVFODm2NX+NTwGpB4Hc
cndgl6I2EYBnbugqqeAlEcR70mgB5xO0Er/jW/mwkmx+xs4LsgV8x+kyGj4ZLjS+
dWCUswytbYAXYL5+YdvtQS32W5T99Q9AWM1NTdjIVm8aPI6cL6xeVQUpjIrlUPqp
megF7gXCQtM3IV9PsQT2AUyZr49X+hmHocVySkbtaB0D7S8XkYbVgRzfJS0Rb0Ad
utTGH5HG+5GFDrsUxRHj30xU1ZAjvPj15hptUEzPPmFBfNHvxcyYNbqjkBDYT9zI
zCiyie9QRWrbhaQi2NgOXLZSRpE9sRN2o3ahbpvmvCILVTAo/5iliK8khMdinFfp
qwIDAQAB
-----END PUBLIC KEY-----`;

const API_BASE_URL = 'http://localhost:8000'; // Địa chỉ backend FastAPI

function VotingForm() {
  const [personalId, setPersonalId] = useState('');
  const [voteToken, setVoteToken] = useState(localStorage.getItem('voteToken') || '');
  const [selectedOption, setSelectedOption] = useState('');
  const [encryptedVote, setEncryptedVote] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const VOTE_OPTIONS = ['Candidate A', 'Candidate B', 'Candidate C', 'Candidate D'];

  localStorage.removeItem('voteToken');

  const clearMessages = () => {
    setMessage('');
    setError('');
  }


  const handleGetToken = async () => {
    setError('');
    setMessage('');
    if (!personalId) {
      setError('Please enter your Personal ID.');
      return;
    }
    try {
      console.log("[DEBUG]", `${API_BASE_URL}/get-vote-token`);
      const response = await axios.post(`${API_BASE_URL}/get-vote-token`, { personal_id: personalId });
      setVoteToken(response.data.vote_token);
      localStorage.setItem('voteToken', response.data.vote_token); // Lưu token
      setMessage('Vote token received successfully!');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to get vote token. Ensure your ID is valid and not used.';
      setError(errorMsg);
      console.error("Error getting token:", err);
    }
  };

  const encryptVote = (voteOption) => {
    if (!voteOption) return '';
    try {
      const encrypt = new JSEncrypt();
      encrypt.setPublicKey(VOTING_SYSTEM_PUBLIC_KEY);

      const ciphertext = encrypt.encrypt(voteOption);
      console.log("[DEBUG] Encrypted vote:", ciphertext);
      if (!ciphertext) {
        setError("Encryption failed. The public key might be invalid or the data too large for RSA.");
        return '';
      }
      return ciphertext;
    } catch (e) {
      console.error("Encryption error:", e);
      setError("An error occurred during encryption.");
      return '';
    }
  };

  useEffect(() => {
    if (selectedOption) {
      const ciphertext = encryptVote(selectedOption);
      setEncryptedVote(ciphertext);
    } else {
      setEncryptedVote('');
    }
  }, [selectedOption]);


  const handleSubmitVote = async (event) => {
    event.preventDefault();
    clearMessages();
    if (!voteToken) {
      setError('Please get a vote token first.');
      return;
    }
    if (!selectedOption) {
      setError('Please select an option to vote for.');
      return;
    }
    if (!encryptedVote) {
      setError('Could not encrypt your vote. Please try again or select an option.');
      return;
    }
    setIsLoading(true);
    try {
      await axios.post(
        `${API_BASE_URL}/submit-vote`,
        { encrypted_vote: encryptedVote },
        { headers: { Authorization: `Bearer ${voteToken}` } }
      );
      setVoteToken('');
      localStorage.removeItem('voteToken');
      setSelectedOption('');
      setEncryptedVote('');
      setPersonalId('');
      console.log("[DEBUG] Vote submitted successfully");
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to submit vote. Your token might be invalid or already used.';
      setError(errorMsg);
      console.error("Error submitting vote:", err);
    }
  };

  return (
    <div>
      {message && <p style={{ color: 'green' }}>{message}</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}

      {!voteToken ? (
        <section>
          <h2>Step 1: Get Your Vote Token</h2>
          <input
            type="text"
            placeholder="Enter Personal ID (e.g., MSV123)"
            value={personalId}
            onChange={(e) => setPersonalId(e.target.value)}
          />
          <button onClick={handleGetToken}>Get Token</button>
        </section>
      ) : (
        <section>
          <h2>Step 2: Cast Your Vote</h2>
          <p>Your Vote Token: <code>{voteToken}</code> (Keep this safe if you need to resume later)</p>
          <div>
            {VOTE_OPTIONS.map(option => (
              <button
                key={option}
                onClick={() => setSelectedOption(option)}
                style={{
                  margin: '5px',
                  backgroundColor: selectedOption === option ? 'lightblue' : 'white'
                }}
              >
                {option}
              </button>
            ))}
          </div>
          {selectedOption && <p>You selected: {selectedOption}</p>}
          {encryptedVote && (
            <div>
              <p>Encrypted Vote (for submission):</p>
              <textarea value={encryptedVote} readOnly rows={5} style={{ width: '80%' }} />
            </div>
          )}
          <button onClick={handleSubmitVote} disabled={!selectedOption || !encryptedVote}>
            Submit Encrypted Vote
          </button>
        </section>
      )}
    </div>
  );
}

export default VotingForm;