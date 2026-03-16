import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { http, HttpResponse } from 'msw'
import { server } from '../test/mocks/server'
import { AuthProvider } from '../context/AuthContext'
import { ToastProvider } from '../context/ToastContext'
import PatientsPage from './PatientsPage'

const API = 'http://localhost:8000'

function renderPage() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <ToastProvider>
          <PatientsPage />
        </ToastProvider>
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('PatientsPage', () => {
  beforeEach(() => {
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('user', JSON.stringify({ id: 1, username: 'testuser', email: 'test@test.com' }))
  })

  it('renders the patient list from API', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Ana García')).toBeInTheDocument()
      expect(screen.getByText('Carlos López')).toBeInTheDocument()
    })
  })

  it('shows total count in footer', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/2 de 2 paciente/)).toBeInTheDocument()
    })
  })

  it('shows empty state when no patients match search', async () => {
    server.use(
      http.get(`${API}/patients`, () =>
        HttpResponse.json({ items: [], total: 0, skip: 0, limit: 50 })
      )
    )

    renderPage()
    const input = await screen.findByPlaceholderText(/Buscar/)
    await userEvent.type(input, 'zzz-no-match')

    await waitFor(() => {
      expect(screen.getByText(/Sin resultados para/)).toBeInTheDocument()
    })
  })

  it('shows error message when API fails', async () => {
    server.use(
      http.get(`${API}/patients`, () => HttpResponse.error())
    )

    renderPage()

    // Both the inline error div and the toast show the same message — use getAllByText
    await waitFor(() => {
      const matches = screen.getAllByText('Error al cargar pacientes')
      expect(matches.length).toBeGreaterThan(0)
    })
  })

  it('shows "Cargar más" button when there are more results', async () => {
    server.use(
      http.get(`${API}/patients`, () =>
        HttpResponse.json({
          items: [{ id: 1, name: 'Ana García', sex: 'F', birth_date: '1990-05-15' }],
          total: 60,
          skip: 0,
          limit: 50,
        })
      )
    )

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/Cargar más/)).toBeInTheDocument()
    })
  })

  it('clears auth from localStorage on 401 response', async () => {
    server.use(
      http.get(`${API}/patients`, () =>
        HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
      )
    )

    renderPage()

    // axios interceptor removes token + user on 401
    await waitFor(() => {
      expect(localStorage.getItem('token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()
    })
  })
})
