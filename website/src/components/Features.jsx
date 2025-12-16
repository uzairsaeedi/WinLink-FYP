import React from 'react'
import { 
  FiCpu, FiShield, FiActivity, FiZap, FiLock, FiMonitor,
  FiServer, FiTarget, FiTrendingUp, FiGitBranch, FiCloud, FiCode
} from 'react-icons/fi'
import './Features.css'

function Features() {
  const features = [
    {
      icon: <FiCpu />,
      title: 'Intelligent Load Balancing',
      description: 'Automatically distribute tasks across workers based on CPU, memory, network latency, and current load for optimal performance.'
    },
    {
      icon: <FiShield />,
      title: 'Enterprise Security',
      description: 'TLS encryption, HMAC authentication, and Windows Job Objects for process isolation ensure your tasks run securely.'
    },
    {
      icon: <FiActivity />,
      title: 'Real-time Monitoring',
      description: 'Live dashboards showing CPU, memory, disk, and network metrics for all connected workers with historical data visualization.'
    },
    {
      icon: <FiZap />,
      title: 'Multi-Worker Support',
      description: 'Connect and manage multiple worker PCs simultaneously with automatic worker discovery via UDP broadcast.'
    },
    {
      icon: <FiTarget />,
      title: 'GPU Detection',
      description: 'Automatically detect GPU-capable workers and assign ML/AI tasks to machines with NVIDIA GPU support.'
    },
    {
      icon: <FiLock />,
      title: 'Process Isolation',
      description: 'Each task runs in an isolated process with configurable CPU and memory limits for maximum safety.'
    },
    {
      icon: <FiServer />,
      title: 'Task Templates',
      description: 'Pre-built templates for common computing tasks including data processing, ML training, and system monitoring.'
    },
    {
      icon: <FiMonitor />,
      title: 'Modern UI',
      description: 'Beautiful PyQt5-based interface with glassmorphic design, real-time charts, and system tray integration.'
    },
    {
      icon: <FiTrendingUp />,
      title: 'Performance Analytics',
      description: 'Track task completion times, resource utilization trends, and worker performance metrics over time.'
    },
    {
      icon: <FiGitBranch />,
      title: 'Task Queue Management',
      description: 'View all tasks with status indicators, progress tracking, and detailed execution logs in real-time.'
    },
    {
      icon: <FiCloud />,
      title: 'Docker Support',
      description: 'Optional containerization for maximum task isolation and security using Docker Desktop on Windows.'
    },
    {
      icon: <FiCode />,
      title: 'Custom Python Tasks',
      description: 'Execute any Python code remotely with full stdout/stderr capture and error handling.'
    }
  ]

  return (
    <section id="features" className="features">
      <div className="bg-decoration bg-decoration-3"></div>
      
      <div className="container">
        <div className="section-header">
          <h2>Powerful Features</h2>
          <p>
            Everything you need for distributed computing, from intelligent task distribution 
            to comprehensive monitoring and enterprise-grade security.
          </p>
        </div>

        <div className="features-grid">
          {features.map((feature, index) => (
            <div 
              key={index} 
              className="feature-card glass"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="feature-icon">{feature.icon}</div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default Features
