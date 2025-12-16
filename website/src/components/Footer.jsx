import React from 'react'
import { FiGithub, FiMail, FiHeart } from 'react-icons/fi'
import './Footer.css'

function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-content">
          <div className="footer-section">
            <div className="footer-logo">
              <div className="logo-icon-footer">
                {/* Use a relative path so it works both locally and on GitHub Pages */}
                <img src="WinLink_logo.png" alt="WinLink Logo" className="footer-logo-image" />
              </div>
              <span className="logo-text">WinLink</span>
            </div>
            <p className="footer-description">
              Distributed computing platform for Windows with enterprise-grade security and real-time monitoring.
            </p>
          </div>

          <div className="footer-section">
            <h4>Quick Links</h4>
            <ul>
              <li><a href="#hero">Home</a></li>
              <li><a href="#features">Features</a></li>
              <li><a href="#architecture">How It Works</a></li>
              <li><a href="#download">Download</a></li>
            </ul>
          </div>

          <div className="footer-section">
            <h4>Resources</h4>
            <ul>
              <li>
                <a href="https://github.com/ashhadhere/WinLink-FYP#readme" target="_blank" rel="noopener noreferrer">
                  Documentation
                </a>
              </li>
              <li>
                <a href="https://github.com/ashhadhere/WinLink-FYP" target="_blank" rel="noopener noreferrer">
                  GitHub Repository
                </a>
              </li>
              <li>
                <a href="https://github.com/ashhadhere/WinLink-FYP/issues" target="_blank" rel="noopener noreferrer">
                  Report Issues
                </a>
              </li>
            </ul>
          </div>

          <div className="footer-section">
            <h4>Connect</h4>
            <div className="social-links">
              <a
                href="https://github.com/ashhadhere/WinLink-FYP"
                target="_blank"
                rel="noopener noreferrer"
                className="social-link"
                title="GitHub"
              >
                <FiGithub />
              </a>
              <a
                href="mailto:contact@winlink.dev"
                className="social-link"
                title="Email"
              >
                <FiMail />
              </a>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <p>
            © {currentYear} WinLink. Made with <FiHeart className="heart-icon" /> for distributed computing enthusiasts.
          </p>
          <p className="footer-note">
            Open Source • MIT License
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer
