import React from 'react'
import { FiMonitor, FiServer, FiArrowRight, FiArrowDown } from 'react-icons/fi'
import './Architecture.css'

function Architecture() {
  return (
    <section id="architecture" className="architecture">
      <div className="container">
        <div className="section-header">
          <h2>How It Works</h2>
          <p>
            Simple and powerful architecture for distributed computing across your network
          </p>
        </div>

        <div className="architecture-diagram">
          <div className="arch-node master glass">
            <div className="node-icon">
              <FiMonitor />
            </div>
            <h3>Master PC</h3>
            <ul>
              <li>Create & dispatch tasks</li>
              <li>Monitor workers</li>
              <li>Manage task queue</li>
              <li>Collect results</li>
            </ul>
          </div>

          <div className="arch-arrow" role="img" aria-label="Secure TLS Connection">
            <span>Secure TLS Connection</span>
            <FiArrowRight className="arrow-icon arrow-right" aria-hidden="true" />
            <FiArrowDown className="arrow-icon arrow-down" aria-hidden="true" />
          </div>

          <div className="arch-node worker glass">
            <div className="node-icon">
              <FiServer />
            </div>
            <h3>Worker PCs</h3>
            <ul>
              <li>Receive tasks</li>
              <li>Execute in isolation</li>
              <li>Report progress</li>
              <li>Return results</li>
            </ul>
          </div>
        </div>

        <div className="workflow-steps">
          <div className="step glass">
            <div className="step-number">1</div>
            <h4>Setup Workers</h4>
            <p>Launch WinLink on worker PCs, configure resource limits, and start listening for tasks.</p>
          </div>

          <div className="step glass">
            <div className="step-number">2</div>
            <h4>Connect Master</h4>
            <p>Master automatically discovers workers on the network or connects manually via IP address.</p>
          </div>

          <div className="step glass">
            <div className="step-number">3</div>
            <h4>Submit Tasks</h4>
            <p>Create Python tasks using templates or custom code, then dispatch to optimal workers.</p>
          </div>

          <div className="step glass">
            <div className="step-number">4</div>
            <h4>Monitor & Collect</h4>
            <p>Watch real-time progress, view logs, and collect results from all workers in one place.</p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Architecture
