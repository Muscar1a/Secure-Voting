import logo from './logo.svg';
import './App.css';
import VotingForm from './components/VotingForm';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Secure Voting System</h1>
      </header>
      <main>
        <VotingForm />
      </main>
    </div>
  );
}

export default App;
