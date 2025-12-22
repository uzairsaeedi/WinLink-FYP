import React from 'react'
import { FiDownload, FiGithub, FiCheckCircle, FiAlertCircle } from 'react-icons/fi'
import './Download.css'

function Download() {
  const requirements = [
    'Windows 10/11 (x64)',
    'Python 3.8+ (3.9+ recommended)',
    '4GB RAM minimum (8GB recommended)',
    '100MB free disk space',
    'Windows PowerShell 5.1+'
  ]

  const optionalRequirements = [
    'Docker Desktop (for containerization)'
  ]

  return (
    <section id="download" className="download">
      <div className="container">
        <div className="section-header">
          <h2>Download WinLink</h2>
          <p>
            Get started with WinLink in minutes. Free and open-source.
          </p>
        </div>

        <div className="download-content">
          <div className="download-main glass">
            <div className="download-header">
              <h3>Latest Release</h3>
              <span className="version-badge">v1.0.0</span>
            </div>

            <p className="download-description">
              Download the complete WinLink distributed computing platform for Windows. 
              Includes both Master and Worker applications with full documentation.
            </p>

            <div className="download-buttons">
              <a 
                href="https://github.com/uzairsaeedi/WinLink-Production/archive/refs/heads/main.zip" 
                className="btn btn-primary download-btn"
                download
              >
                <FiDownload />
                Download WinLink
                <span className="file-size">~5 MB</span>
              </a>

              <a 
                href="https://github.com/uzairsaeedi/WinLink-FYP.git" 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn btn-secondary"
              >
                <FiGithub />
                View on GitHub
              </a>
            </div>
          </div>

          <div className="requirements-panel glass">
            <h4>System Requirements</h4>
            <ul className="requirements-list">
              {requirements.map((req, index) => (
                <li key={index}>
                  <FiCheckCircle className="req-icon check" />
                  {req}
                </li>
              ))}
            </ul>

            <h4 className="optional-header">Optional</h4>
            <ul className="requirements-list">
              {optionalRequirements.map((req, index) => (
                <li key={index}>
                  <FiAlertCircle className="req-icon optional" />
                  {req}
                </li>
              ))}
            </ul>

            <div className="help-section">
              <h4>Need Help?</h4>
              <p>
                Check out the comprehensive documentation and setup guides in the repository.
              </p>
              <a 
                href="https://github.com/uzairsaeedi/WinLink-FYP#readme" 
                target="_blank" 
                rel="noopener noreferrer"
                className="help-link"
              >
                Read Documentation →
              </a>
            </div>
          </div>
        </div>

        <div className="features-highlight">
          <div className="highlight-item">
            <h4>✓ Automated Setup</h4>
            <p>One-click installation script handles all dependencies</p>
          </div>
          <div className="highlight-item">
            <h4>✓ SSL Certificates</h4>
            <p>Auto-generated TLS certificates for secure communication</p>
          </div>
          <div className="highlight-item">
            <h4>✓ Firewall Config</h4>
            <p>Automated Windows Firewall configuration</p>
          </div>
          <div className="highlight-item">
            <h4>✓ Ready to Use</h4>
            <p>Start distributing tasks in under 5 minutes</p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Download
