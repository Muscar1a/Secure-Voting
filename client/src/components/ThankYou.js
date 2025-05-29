// components/ThankYou.js
import React from 'react';
import { useNavigate } from 'react-router-dom';

const ThankYou = () => {
  const navigate = useNavigate();

  return (
    <div>
      <div>
        <div style={{ fontSize: '50px', color: '#4CAF50' }}>✓</div>
        <h1 style={{ color: '#4CAF50' }}>Thank You!</h1>
        <p>Your vote has been submitted successfully and is now being processed.</p>
        <p>You can safely close this window or return to the home page.</p>
        
        <div style={{ marginTop: 20, display: 'flex', justifyContent: 'center', gap: '10px' }}>
          <button 
            onClick={() => navigate('/')}
            style={{
              padding: '10px 20px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            Return to Home
          </button>

          <button 
            onClick={() => navigate('/results')}
            style={{
              padding: '10px 20px',
              backgroundColor: '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            View Results
          </button>
      </div>
    </div>
  </div>          
  );
};

export default ThankYou;