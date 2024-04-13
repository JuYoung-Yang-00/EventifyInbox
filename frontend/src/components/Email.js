import React, { useState, useEffect } from 'react';

function Email() {
  const [emails, setEmails] = useState([]);
  const [selectedEmail, setSelectedEmail] = useState(null);

  useEffect(() => {
    fetch('https://api.eventifyinbox.com/nylas/recent-emails', {
      credentials: 'include', 
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      if (Array.isArray(data)) {
        setEmails(data);
      } else {
        console.error('Received data is not an array:', data);
      }
    })
    .catch(error => console.error('Error fetching emails:', error));
  }, []);

  const handleEmailSelect = (email) => {
    setSelectedEmail(email);
  };

  return (
    <div className='email-container'>
      <div className='email-list-container'>
        {emails.map((email, index) => (
          <div key={index} className='email-item' onClick={() => handleEmailSelect(email)}>
            <h2>{email.subject}</h2>
            <p>From: {email.from_[0].name} <span>({email.from_[0].email})</span></p>
            <p>Date: {new Date(email.date * 1000).toLocaleDateString()}</p>
          </div>
        ))}
      </div>
      <div className='email-content-container'>
        {selectedEmail ? (
          <div className='email-content'>
            <h3>{selectedEmail.subject}</h3>
            <p>Date: {new Date(selectedEmail.date * 1000).toLocaleDateString()}</p>
            <p>From: {selectedEmail.from_[0].name} <span>({selectedEmail.from_[0].email})</span></p>
            <div dangerouslySetInnerHTML={{ __html: selectedEmail.body }}></div>
          </div>
        ) : (
          <div className='email-content-placeholder'>
            <p>Select an email to view its content.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Email;
