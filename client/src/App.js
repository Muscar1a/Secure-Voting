import logo from './logo.svg';
import './App.css';
import VotingForm from './components/VotingForm';
import VoteResults from "./components/VoteResults";
function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Secure Voting System</h1>
      </header>
      <main>
        <VotingForm />
        <VoteResults />
      </main>
    </div>
  );
}

export default App;
