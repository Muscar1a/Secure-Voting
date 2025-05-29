import logo from './logo.svg';
import './App.css';
import VotingForm from './components/VotingForm';
import VoteResults from "./components/VoteResults";
import ThankYou from './components/ThankYou';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import React from 'react';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<VotingForm />} />
          <Route path="/thankyou" element={<ThankYou />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
