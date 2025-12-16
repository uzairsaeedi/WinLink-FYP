import React from 'react'
import Navbar from './components/Navbar'
import Hero from './components/Hero'
import Features from './components/Features'
import Architecture from './components/Architecture'
import Download from './components/Download'
import Footer from './components/Footer'
import './App.css'

function App() {
  return (
    <div className="App">
      <Navbar />
      <Hero />
      <Features />
      <Architecture />
      <Download />
      <Footer />
    </div>
  )
}

export default App
