// frontend/src/components/VotingForm.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import JSEncrypt from 'jsencrypt';

const VOTING_SYSTEM_PUBLIC_KEY = `-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsj7WxRYLzvg6PwN5VJ0p
rI3bhJq0c2T7uFzP5nOVldn2OQQtWqT4gTzSzFkHqwqkVL5WzXhfBp1LX2Ps7P36
TqA1O5v9v7rh2v3vL8cJyR7nFjz6e8ZeqkqI+YX7DZCq4Xezb9hlG2lQtW6LjRZ7
LnMzJMjZH62aCUeR2L9UUS1vGx10y6xkHJNL7Z9FjkaG0B+u2AXZl1q+zJqHcoPz
RleuKr1nxHh7pxmz8W+whkv7lDZtRMYcM1TW82LjGqUJOx1CjAvPQJkV9qPq5Q7b
m6kLacYmF9y9qJyQOHXoQJ6IzEYWbkLrDLBiqm+7fwp34vTNBOq6Yt4wOgT2+8LC
twIDAQAB
-----END PUBLIC KEY-----`;

const API_BASE_URL = 'http://localhost:8000';

function VotingForm() {
  const [personalId, setPersonalId] = useState('');
  // Lấy token từ localStorage khi component mount, nếu có
  const [voteToken, setVoteToken] = useState(localStorage.getItem('voteToken') || '');
  const [selectedOption, setSelectedOption] = useState('');
  const [encryptedVote, setEncryptedVote] = useState('');
  const [isLoading, setIsLoading] = useState(false); // Sửa lại tên biến cho nhất quán
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const VOTE_OPTIONS = ['Candidate A', 'Candidate B', 'Candidate C', 'Candidate D'];

  // localStorage.removeItem('voteToken'); // << XÓA HOẶC COMMENT DÒNG NÀY Ở ĐÂY

  const clearMessages = () => {
    setMessage('');
    setError('');
  }

  const handleGetToken = async () => {
    clearMessages(); // Gọi ở đầu để xóa thông báo cũ
    if (!personalId) {
      setError('Please enter your Personal ID.');
      return;
    }
    setIsLoading(true); // Bắt đầu loading
    try {
      // console.log("[DEBUG]", `${API_BASE_URL}/get-vote-token`);
      const response = await axios.post(`${API_BASE_URL}/get-vote-token`, { personal_id: personalId });
      const newVoteToken = response.data.vote_token;
      setVoteToken(newVoteToken);
      localStorage.setItem('voteToken', newVoteToken); // Lưu token mới
      setMessage('Vote token received successfully!');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to get vote token. Ensure your ID is valid and not used.';
      setError(errorMsg);
      // console.error("Error getting token:", err);
    } finally {
      setIsLoading(false); // Kết thúc loading
    }
  };

  const encryptVote = (voteOption) => {
    if (!voteOption) return '';
    try {
      const encrypt = new JSEncrypt();
      encrypt.setPublicKey(VOTING_SYSTEM_PUBLIC_KEY);
      const ciphertext = encrypt.encrypt(voteOption);
      // console.log("[DEBUG] Encrypted vote:", ciphertext);
      if (!ciphertext) {
        setError("Encryption failed. The public key might be invalid or the data too large for RSA.");
        return '';
      }
      return ciphertext;
    } catch (e) {
      // console.error("Encryption error:", e);
      setError("An error occurred during encryption.");
      return '';
    }
  };

  useEffect(() => {
    if (selectedOption) {
      clearMessages(); // Xóa thông báo khi người dùng chọn option mới
      const ciphertext = encryptVote(selectedOption);
      setEncryptedVote(ciphertext);
    } else {
      setEncryptedVote('');
    }
  }, [selectedOption]); // Chỉ chạy khi selectedOption thay đổi

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
      const response = await axios.post( // Lưu response lại
        `${API_BASE_URL}/submit-vote`,
        { encrypted_vote: encryptedVote },
        { headers: { Authorization: `Bearer ${voteToken}` } }
      );
      // Xóa token và reset form SAU KHI gửi thành công
      setVoteToken('');
      localStorage.removeItem('voteToken'); // << DI CHUYỂN DÒNG NÀY VÀO ĐÂY
      setSelectedOption('');
      setEncryptedVote('');
      setPersonalId(''); // Reset cả personal ID
      setMessage(response.data.message || 'Vote submitted successfully! It is now pending external processing.'); // Sử dụng message từ backend
      // console.log("[DEBUG] Vote submitted successfully", response.data);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to submit vote. Your token might be invalid or already used.';
      setError(errorMsg);
      // console.error("Error submitting vote:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Thêm nút để người dùng có thể chủ động xóa token nếu họ muốn bắt đầu lại
  const handleClearTokenAndRestart = () => {
    clearMessages();
    setVoteToken('');
    localStorage.removeItem('voteToken');
    setPersonalId(''); // Có thể reset cả personal ID
    setSelectedOption('');
    setEncryptedVote('');
    setMessage('Token cleared. You can request a new token.');
  };

  return (
    <div>
      <h1>Secure Electronic Voting</h1> {/* Thêm tiêu đề */}
      {message && <p style={{ color: 'green', border: '1px solid green', padding: '10px' }}>{message}</p>}
      {error && <p style={{ color: 'red', border: '1px solid red', padding: '10px' }}>{error}</p>}

      {!voteToken ? (
        <section>
          <h2>Step 1: Get Your Vote Token</h2>
          <label htmlFor="personalId">Personal ID:</label>
          <input
            id="personalId"
            type="text"
            placeholder="Enter Personal ID (e.g., MSV123)"
            value={personalId}
            onChange={(e) => setPersonalId(e.target.value)}
            disabled={isLoading}
          />
          <button onClick={handleGetToken} disabled={isLoading || !personalId}>
            {isLoading ? 'Getting Token...' : 'Get Token'}
          </button>
        </section>
      ) : (
        <section>
          <h2>Step 2: Cast Your Vote</h2>
          <p>Your Vote Token: <code>{voteToken}</code></p>
          <p>Please select your preferred candidate:</p>
          <div>
            {VOTE_OPTIONS.map(option => (
              <button
                key={option}
                onClick={() => setSelectedOption(option)}
                disabled={isLoading}
                style={{
                  margin: '5px',
                  padding: '10px 15px',
                  border: selectedOption === option ? '2px solid blue' : '1px solid #ccc',
                  backgroundColor: selectedOption === option ? 'lightblue' : 'white',
                  cursor: 'pointer'
                }}
              >
                {option}
              </button>
            ))}
          </div>
          {selectedOption && <p>You selected: <strong>{selectedOption}</strong></p>}
          
          {/* Không nhất thiết phải hiển thị encryptedVote cho người dùng cuối */}
          {/* {encryptedVote && (
            <div>
              <p>Encrypted Vote (for submission):</p>
              <textarea value={encryptedVote} readOnly rows={3} style={{ width: '90%', fontSize: '0.8em', color: '#555' }} />
            </div>
          )} */}

          <button 
            onClick={handleSubmitVote} 
            disabled={isLoading || !selectedOption || !encryptedVote}
            style={{ marginTop: '20px', padding: '10px 20px', fontSize: '1.1em' }}
          >
            {isLoading ? 'Submitting Vote...' : 'Submit Encrypted Vote'}
          </button>
          <button 
            onClick={handleClearTokenAndRestart} 
            disabled={isLoading}
            style={{ marginTop: '20px', marginLeft: '10px', padding: '10px 15px', backgroundColor: '#f0f0f0' }}
          >
            Clear Token & Restart
          </button>
        </section>
      )}
    </div>
  );
}

export default VotingForm;