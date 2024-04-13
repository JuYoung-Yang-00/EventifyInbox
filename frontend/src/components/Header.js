import React from 'react';
import { NavLink } from 'react-router-dom';

function Header() {
  return (
    <header className="header">
      <div className="header-title">
        <h2>Eventify Inbox</h2>
      </div>
      <nav className="header-nav">
        <div className='nav-links'>
          <p>
            <NavLink 
              to="/" 
              activeClassName="active"
              className="nav-link"
            >
              Home
            </NavLink>
          </p>
          <p>
            <NavLink 
              to="/email" 
              activeClassName="active"
              className="nav-link"
            >
              Email
            </NavLink>
          </p>
          <p>
            <NavLink 
              to="/calendar" 
              activeClassName="active"
              className="nav-link"
            >
              Calendar
            </NavLink>
          </p>
        </div>
      </nav>
    </header>
  );
}

export default Header;
