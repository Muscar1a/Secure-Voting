// frontend/src/components/VotingForm.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import JSEncrypt from 'jsencrypt';
import { useNavigate } from 'react-router-dom';

const VOTING_SYSTEM_PUBLIC_KEY = `-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzXVFODm2NX+NTwGpB4Hc
cndgl6I2EYBnbugqqeAlEcR70mgB5xO0Er/jW/mwkmx+xs4LsgV8x+kyGj4ZLjS+
dWCUswytbYAXYL5+YdvtQS32W5T99Q9AWM1NTdjIVm8aPI6cL6xeVQUpjIrlUPqp
megF7gXCQtM3IV9PsQT2AUyZr49X+hmHocVySkbtaB0D7S8XkYbVgRzfJS0Rb0Ad
utTGH5HG+5GFDrsUxRHj30xU1ZAjvPj15hptUEzPPmFBfNHvxcyYNbqjkBDYT9zI
zCiyie9QRWrbhaQi2NgOXLZSRpE9sRN2o3ahbpvmvCILVTAo/5iliK8khMdinFfp
qwIDAQAB
-----END PUBLIC KEY-----`;

const API_BASE_URL = 'http://localhost:8000';

function VotingForm() {
  const [personalId, setPersonalId] = useState('');
  
  const [voteToken, setVoteToken] = useState(localStorage.getItem('voteToken') || '');
  const [selectedOption, setSelectedOption] = useState('');
  const [encryptedVote, setEncryptedVote] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');


  const VOTE_OPTIONS = ['Candidate A', 'Candidate B', 'Candidate C', 'Candidate D'];

  // localStorage.removeItem('voteToken');

  const clearMessages = () => {
    setMessage('');
    setError('');
  }

  const hashPersonalId = async (personalId) => {
    const encoder = new TextEncoder();
    const data = encoder.encode(personalId);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
  };

  const handleGetToken = async () => {
    clearMessages();
    if (!personalId) {
      setError('Please enter your Personal ID.');
      return;
    }
    setIsLoading(true);
    try {
      const hashedId = await hashPersonalId(personalId);
      // console.log("[DEBUG]", `${API_BASE_URL}/get-vote-token`);
      const response = await axios.post(`${API_BASE_URL}/get-vote-token`, { personal_id: hashedId });
      const newVoteToken = response.data.vote_token;
      setVoteToken(newVoteToken);
      localStorage.setItem('voteToken', newVoteToken);
      setMessage('Vote token received successfully!');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to get vote token. Ensure your ID is valid and not used.';
      setError(errorMsg);
      // console.error("Error getting token:", err);
    } finally {
      setIsLoading(false);
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
      clearMessages();
      const ciphertext = encryptVote(selectedOption);
      setEncryptedVote(ciphertext);
    } else {
      setEncryptedVote('');
    }
  }, [selectedOption]);

  const navigate = useNavigate();

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
      const response = await axios.post(
        `${API_BASE_URL}/submit-vote`,
        { encrypted_vote: encryptedVote },
        { headers: { Authorization: `Bearer ${voteToken}` } }
      );

      setVoteToken('');
      localStorage.removeItem('voteToken'); // << DI CHUYỂN DÒNG NÀY VÀO ĐÂY
      setSelectedOption('');
      setEncryptedVote('');
      setPersonalId('');
      setMessage(response.data.message || 'Vote submitted successfully! It is now pending external processing.');

      /*
      setTimeout(() => {
        navigate('/ThankYou', {
          state: {
            message: response.data.message,
            timestamp: new Date().toISOString()
          }
        });
      }, 1500);
      */

      navigate('/ThankYou');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to submit vote. Your token might be invalid or already used.';
      setError(errorMsg);
      // console.error("Error submitting vote:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearTokenAndRestart = () => {
    clearMessages();
    setVoteToken('');
    localStorage.removeItem('voteToken');
    setPersonalId('');
    setSelectedOption('');
    setEncryptedVote('');
    setMessage('Token cleared. You can request a new token.');
  };

  return (
    <div>
      <h1>Secure Electronic Voting</h1>
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