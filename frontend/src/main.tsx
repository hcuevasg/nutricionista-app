import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'
import { installErrorReporting } from './utils/errorReporter'
import { reloadForNewVersion } from './utils/lazyPage'
import './index.css'

installErrorReporting()

// Vite avisa cuando no puede precargar un archivo de una versión ya reemplazada
window.addEventListener('vite:preloadError', (event) => {
  if (reloadForNewVersion()) event.preventDefault()
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)
