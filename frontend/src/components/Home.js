import React, { useState, useEffect } from 'react';
import nylasimg from '../assets/nylas.png';
import langchainimg from '../assets/langchain.png';

function Home() {
  const [isConnected, setIsConnected] = useState(localStorage.getItem('nylasConnected') === 'true');

  useEffect(() => {
    const queryParams = new URLSearchParams(window.location.search);
    const isNylasConnected = queryParams.get('nylasConnected') === 'true';
    
    if (isNylasConnected) {
      setIsConnected(true);
      localStorage.setItem('nylasConnected', 'true'); 
      window.history.replaceState(null, null, window.location.pathname);
    }
  }, []);

  const handleConnectClick = () => {
    window.location.href = 'http://127.0.0.1:5000/nylas';
  };

  return (
    <div>
      <div className='image-container'>
        <img src={langchainimg} alt='Langchain Logo' />
        <img src={nylasimg} alt='Nylas Logo' />
      </div>
      <div className='home-text'>
        <h1>Home Page</h1>
        <p>Welcome! This application uses Langchain Agents and Nylas to create calendar events for when users receive emails that contain tasks.</p>
        {isConnected ? (
          <p>You're connected to Nylas API!</p>
        ) : (
          <button className='connect-nylas-button' onClick={handleConnectClick}>Connect to Nylas</button>
        )}
      </div>
    </div>
  );
}

export default Home;
