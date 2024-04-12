import React from 'react';
import { NavLink } from 'react-router-dom';

function Header() {
  return (
    <header>
      <div>
        <h2> EventifyInbox</h2>
      </div>
      <nav>
        <div className='nav-links'>
          <p>
            <NavLink 
              to="/" 
              className={({ isActive }) => isActive ? 'active' : undefined}
            >
              Home
            </NavLink>
          </p>
          <p>
            <NavLink 
              to="/email" 
              className={({ isActive }) => isActive ? 'active' : undefined}
            >
              Email
            </NavLink>
          </p>
          <p>
            <NavLink 
              to="/calendar" 
              className={({ isActive }) => isActive ? 'active' : undefined}
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
