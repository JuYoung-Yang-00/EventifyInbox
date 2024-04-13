import React, { useState, useEffect } from 'react';

function Calendar() {
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);

  useEffect(() => {
    fetch('https://api.eventifyinbox.com/nylas/list-events', {
      credentials: 'include',
    })
    .then(response => response.json())
    .then(data => {
      console.log('Fetched events:', data);
      if (Array.isArray(data) && data.length > 0 && Array.isArray(data[0])) {
        setEvents(data[0]); 
      } else {
        console.error('Invalid data format:', data);
      }
    })
    .catch(error => console.error('Error fetching events:', error));
  }, []);

  const handleEventSelect = (event) => {
    setSelectedEvent(event);
  };

  return (
    <div className='calendar-container'>
      <div className='upcoming-event-container'>
        {events.map((event, index) => (
          <div key={index} className='event-item' onClick={() => handleEventSelect(event)}>
            <h2>{event.title}</h2>
            <p>From: {event.creator.email}</p>
            <p>Date: {new Date(event.when.start_time * 1000).toLocaleDateString()}</p>
          </div>
        ))}
      </div>
      <div className='event-content-container'>
        {selectedEvent ? (
          <div className='event-content'>
            <h3>{selectedEvent.title}</h3>
            <p>Date: {new Date(selectedEvent.when.start_time * 1000).toLocaleDateString()}</p>
            <p>From: {selectedEvent.creator.email}</p>
            <p>{selectedEvent.description}</p>
            <p>Location: {selectedEvent.location || "No location provided"}</p>
            <p>Time: {new Date(selectedEvent.when.start_time * 1000).toLocaleTimeString()} - {new Date(selectedEvent.when.end_time * 1000).toLocaleTimeString()}</p>
          </div>
        ) : (
          <div className='event-content-placeholder'>
            <p>Select an event to view its content.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Calendar;
