# WinLink Website

Official website for WinLink - Distributed Computing Platform for Windows.

## 🚀 Quick Start

### Prerequisites

- Node.js 16+ and npm

### Installation

```bash
# Navigate to website directory
cd website

# Install dependencies
npm install

# Start development server
npm run dev
```

The website will be available at `http://localhost:5173`

## 📦 Build

To create a production build:

```bash
npm run build
```

The built files will be in the `dist` folder, ready for deployment.

## 🎨 Features

- **Modern React Design**: Built with React 18 and Vite for fast development
- **Responsive Layout**: Fully responsive design that works on all devices
- **Glassmorphic UI**: Beautiful glass-effect design matching the WinLink app theme
- **Smooth Animations**: Framer Motion powered animations for better UX
- **SEO Optimized**: Meta tags and semantic HTML for better search visibility
- **Fast Performance**: Optimized bundle size and lazy loading

## 🎨 Design Theme

The website matches the WinLink application's design:

- **Color Scheme**: Dark gradient (#141e30 → #243b55)
- **Glass Effect**: Translucent panels with backdrop blur
- **Accent Colors**: 
  - Blue: #4fc3f7
  - Purple: #9c27b0
  - Green: #66bb6a
- **Typography**: Segoe UI font family

## 📁 Project Structure

```
website/
├── public/              # Static assets
│   └── favicon.svg
├── src/
│   ├── components/      # React components
│   │   ├── Navbar.jsx
│   │   ├── Hero.jsx
│   │   ├── Features.jsx
│   │   ├── Architecture.jsx
│   │   ├── Download.jsx
│   │   └── Footer.jsx
│   ├── App.jsx         # Main app component
│   ├── main.jsx        # Entry point
│   ├── index.css       # Global styles
│   └── App.css         # App-level styles
├── index.html
├── package.json
└── vite.config.js
```

## 🚀 Deployment

### GitHub Pages

1. Build the project:
   ```bash
   npm run build
   ```

2. Deploy to GitHub Pages:
   ```bash
   # Install gh-pages
   npm install -g gh-pages

   # Deploy
   gh-pages -d dist
   ```

### Netlify

1. Build command: `npm run build`
2. Publish directory: `dist`

### Vercel

1. Import your GitHub repository
2. Vercel will auto-detect Vite
3. Deploy with one click

## 🛠️ Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally

### Adding New Sections

1. Create a new component in `src/components/`
2. Import and add it to `App.jsx`
3. Update navigation in `Navbar.jsx`
4. Add corresponding CSS file

## 🎯 Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## 📝 License

MIT License - see the main project LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
