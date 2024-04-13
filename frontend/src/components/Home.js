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
    window.location.href = 'https://api.eventifyinbox.com/nylas';
  };

  return (
    <div className="login-container">
      <div className="login-content">
        <div className='image-container'>
          <img className='langchainimg' src={langchainimg} alt='Langchain Logo' />
          <img className='nylasimg' src={nylasimg} alt='Nylas Logo' />
        </div>
        <div className='home-text'>
          <p>Welcome! This application uses Langchain Agents and Nylas to create calendar events for when users receive emails that contain tasks.</p>
          {isConnected ? (
            <p>You're connected to Nylas API!</p>
          ) : (
            <button className='connect-nylas-button' onClick={handleConnectClick}>Connect to Nylas</button>
          )}
        </div>
      </div>
    </div>
  );
}

export default Home;
