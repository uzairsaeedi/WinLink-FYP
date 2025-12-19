import React from 'react'
import { FiDownload, FiZap, FiShield } from 'react-icons/fi'
import './Hero.css'

function Hero() {
  const scrollToDownload = () => {
    const element = document.getElementById('download')
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <section id="hero" className="hero">
      <div className="bg-decoration bg-decoration-1"></div>
      <div className="bg-decoration bg-decoration-2"></div>
      
      <div className="container">
        <div className="hero-content">
          <div className="hero-badge">
            <FiZap className="badge-icon" />
            <span>Distributed Computing Made Simple</span>
          </div>
          
          <h1 className="hero-title">
            Unlock the Power of<br />
            <span className="gradient-text">Distributed Computing</span>
          </h1>
          
          <p className="hero-description">
            WinLink is a cutting-edge distributed computing platform for Windows that 
            enables secure task distribution across multiple PCs with real-time monitoring, 
            intelligent load balancing, and enterprise-grade security.
          </p>
          
          <div className="hero-actions">
            <button className="btn btn-primary" onClick={scrollToDownload}>
              <FiDownload />
              Download For Windows
            </button>
            <button className="btn btn-secondary" onClick={() => {
              const element = document.getElementById('features')
              element?.scrollIntoView({ behavior: 'smooth' })
            }}>
              Learn More
            </button>
          </div>
          
          <div className="hero-stats">
            <div className="stat-item glass">
              <FiShield className="stat-icon" />
              <div className="stat-content">
                <div className="stat-value">TLS</div>
                <div className="stat-label">Encryption</div>
              </div>
            </div>
            <div className="stat-item glass">
              <FiZap className="stat-icon" />
              <div className="stat-content">
                <div className="stat-value">Real-time</div>
                <div className="stat-label">Monitoring</div>
              </div>
            </div>
            <div className="stat-item glass">
              <FiZap className="stat-icon" />
              <div className="stat-content">
                <div className="stat-value">Multi-Worker</div>
                <div className="stat-label">Support</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Hero
