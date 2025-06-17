import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const handleLogin = () => {
    console.log(email, password);
  }
  const handleNavigate = () => {
    const fetchData = async () => {
      const response = await fetch('http://localhost:8000/users/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      console.log(data);
    }
    fetchData();
    navigate('/');
  }
  return (
    <div>
      <h1>Login</h1>
      <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button onClick={handleLogin}>Login</button>
      <button onClick={handleNavigate}>Signup</button>
    </div>
  )
}

export default Login
