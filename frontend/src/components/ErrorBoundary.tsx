import { Component, type ErrorInfo, type ReactNode } from 'react'
import { reportError } from '../utils/errorReporter'

/** Muestra un aviso en vez de una pantalla en blanco y reporta el error. */
export default class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    reportError(error.message, `${error.stack ?? ''}\n\nComponentes:${info.componentStack ?? ''}`)
  }

  render() {
    if (!this.state.failed) return this.props.children
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-light p-6">
        <div className="bg-white rounded-xl shadow-sm border border-border p-8 max-w-md text-center space-y-4">
          <h1 className="text-lg font-bold text-gray-900">Algo salió mal</h1>
          <p className="text-sm text-gray-600">
            Ocurrió un error inesperado en esta pantalla. Quedó registrado para revisarlo; tus datos guardados no se
            perdieron.
          </p>
          <button onClick={() => window.location.reload()}
            className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm font-medium">
            Recargar la página
          </button>
        </div>
      </div>
    )
  }
}
