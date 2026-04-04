import { useEffect } from "react"; // 1. Import useEffect
import { useHelloStore } from "./store/useHelloStore";
import "./App.css";

function App() {
  const { message, loading, fetchAll, error } = useHelloStore();

  useEffect(() => {
    fetchAll();
  }, [fetchAll]); // Dependency array ensures it runs once

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error loading users!</p>;

  return (
    <div className="App">
      <header className="App-header">
        <img src="/app/logo.svg" className="App-logo" alt="logo" />
        <p>{message}</p>
        <p>
          Edit <code>src/App.tsx</code> and save to reload.
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </header>
    </div>
  );
}

export default App;
