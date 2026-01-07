import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [message, setMessage] = useState('')

  useEffect(() => {
    // Fetch the root endpoint from FastAPI
    fetch('http://localhost:8000/')
      .then((response) => response.json())
      .then((data) => setMessage(data.message))
      .catch((error) => console.error('Error fetching data:', error));
  }, [])

  return (
    <div style={{ textAlign: 'center', marginTop: '50px' }}>
      <h1>React + FastAPI</h1>
      <p>The backend says:</p>
      <h2 style={{ color: '#646cff' }}>{message || "Loading..."}</h2>
    </div>
  )
}

export default App
