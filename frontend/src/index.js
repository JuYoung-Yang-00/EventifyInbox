import React from 'react';
import { createRoot } from 'react-dom/client'; // Import createRoot
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Home from './components/Home';
import Email from './components/Email';
import Calendar from './components/Calendar';
import Header from './components/Header';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <div>
        <Header />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/email" element={<Email />} />
          <Route path="/calendar" element={<Calendar />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

const container = document.getElementById('root');
const root = createRoot(container); 
root.render(<App />);
