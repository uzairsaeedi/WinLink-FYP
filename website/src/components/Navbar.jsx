import React, { useState, useEffect } from 'react'
import { FiMenu, FiX } from 'react-icons/fi'
import './Navbar.css'

function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const scrollToSection = (id) => {
    const element = document.getElementById(id)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
      setIsMobileMenuOpen(false)
    }
  }

  return (
    <nav className={`navbar ${isScrolled ? 'scrolled' : ''}`}>
      <div className="container navbar-container">
        <div className="navbar-logo" onClick={() => scrollToSection('hero')}>
          <div className="logo-icon">
            <img 
              src="/WinLink-FYP/WinLink_logo.png"
              alt="WinLink Logo" 
              className="logo-image"
              onError={(e) => {
                console.error('Logo failed to load from:', e.target.src);
                e.target.style.display = 'none';
              }}
              onLoad={() => console.log('Logo loaded successfully from:', document.querySelector('.logo-image')?.src)}
            />
          </div>
          <span className="logo-text">WinLink</span>
        </div>

        <ul className={`navbar-menu ${isMobileMenuOpen ? 'active' : ''}`}>
          <li><a onClick={() => scrollToSection('hero')}>Home</a></li>
          <li><a onClick={() => scrollToSection('features')}>Features</a></li>
          <li><a onClick={() => scrollToSection('architecture')}>How It Works</a></li>
          <li><a onClick={() => scrollToSection('download')}>Download</a></li>
        </ul>

        <div className="navbar-actions">
          <button className="btn btn-primary" onClick={() => scrollToSection('download')}>
            Get Started
          </button>
          <button 
            className="mobile-menu-toggle" 
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            {isMobileMenuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
          </button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
