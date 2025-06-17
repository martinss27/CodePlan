import React from 'react';
import Signup from './pages/Signup';
import Login from './pages/Login';  
import { Routes, Route, useNavigate } from 'react-router-dom';

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Login />} />
      </Routes>
    </div>
  );
}


export default App;
