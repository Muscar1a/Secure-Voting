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
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAy8Dbv0n3+5O7mI5S
L0yBenciq2APr5sPE1XshjlsudrUB3ks9y7vGvcbxKajvxQTmREVw71K2VAh
lS2cwsO7X+jP7v7K+y5t6V+v3N9V6f0e9a8a1nZ0iE9X0wYk8sL7O0iV4U0N
p0p7N0xX5A1mZ5o7v7y0u8l9F3o1b7h0D5W9W5T8s0h8c7y6Z7z6V3n4c9m8
H0i7g5J4f2k1t0s9S8h6G3g2j8d7e6S5L4u3i0b9o8s7Y5q4w3c2v1b0a8k7
X4j6s9f3d2n1m0c8b7a6d5e4f3g2h1j0k9l8m7n6p5o4i3z2x1y0w9v8c7b6
a5s4wQIDAQAB
-----END PUBLIC KEY-----`; // THAY THẾ BẰNG PUBLIC KEY THỰC CỦA BẠN


const API_BASE_URL = 'http://localhost:8000'; // Địa chỉ backend FastAPI

function VotingForm() {
  const [personalId, setPersonalId] = useState('');
  const [voteToken, setVoteToken] = useState(localStorage.getItem('voteToken') || '');
  const [selectedOption, setSelectedOption] = useState('');
  const [encryptedVote, setEncryptedVote] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const VOTE_OPTIONS = ['Candidate A', 'Candidate B', 'Candidate C', 'Abstain']; // Các lựa chọn

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


  const handleSubmitVote = async () => {
    setError('');
    setMessage('');
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

    try {
      await axios.post(
        `${API_BASE_URL}/submit-vote`,
        { encrypted_vote: encryptedVote },
        { headers: { Authorization: `Bearer ${voteToken}` } }
      );
      setMessage('Vote submitted successfully!');
      setSelectedOption('');
      setEncryptedVote('');
      // Xóa token sau khi vote thành công để tránh dùng lại?
      // localStorage.removeItem('voteToken');
      // setVoteToken('');
      // Hoặc backend sẽ tự ngăn chặn việc dùng lại token
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
              <textarea value={encryptedVote} readOnly rows={5} style={{width: '80%'}}/>
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