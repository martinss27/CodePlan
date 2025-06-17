import React from 'react'
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
function Signup() {
  const [username, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const handleSignup = () => {
    console.log(username, email, password);
  }
  const handleNavigate = async () => {
      const response = await fetch('http://localhost:8000/users/register', {
        headers: {
          'Content-Type': 'application/json',
        },
        method: 'POST',
        body: JSON.stringify({ username, email, password }),
      });
      try {
        const data = await response.json();
        console.log(data);
        navigate('/login');
      } catch (error) {
        console.error('Error:', error);
      }
  } 
  return (
    <div>
      <h1>Signup</h1>
      <input type="text" placeholder="Name" value={username} onChange={(e) => setName(e.target.value)} />
      <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button onClick={handleSignup}>Signup</button>
      <button onClick={handleNavigate}>Login</button>
    </div>
  )
}

export default Signup
