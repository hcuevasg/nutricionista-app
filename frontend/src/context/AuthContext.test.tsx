import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from './AuthContext'
import { MemoryRouter } from 'react-router-dom'
import { http, HttpResponse } from 'msw'
import { server } from '../test/mocks/server'

// Component that exposes auth state for testing
function AuthTestWidget() {
  const { user, token, isAuthenticated, logout } = useAuth()
  return (
    <div>
      <span data-testid="auth-status">{isAuthenticated ? 'authenticated' : 'not-authenticated'}</span>
      <span data-testid="username">{user?.username ?? ''}</span>
      <span data-testid="token">{token ?? ''}</span>
      <button onClick={logout}>Logout</button>
    </div>
  )
}

function renderWithProviders() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <AuthTestWidget />
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // localStorage is cleared in afterEach via setup.ts polyfill
  })

  it('starts unauthenticated when localStorage is empty', () => {
    renderWithProviders()
    expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated')
    expect(screen.getByTestId('token')).toHaveTextContent('')
  })

  it('restores session from localStorage on mount', async () => {
    localStorage.setItem('token', 'stored-token-abc')
    localStorage.setItem('user', JSON.stringify({ id: 1, username: 'storeduser', email: 'stored@test.com' }))

    renderWithProviders()

    // User and token should be restored immediately from localStorage
    expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated')
    expect(screen.getByTestId('username')).toHaveTextContent('storeduser')
  })

  it('clears localStorage and state on logout', async () => {
    localStorage.setItem('token', 'stored-token')
    localStorage.setItem('user', JSON.stringify({ id: 1, username: 'testuser', email: 'test@test.com' }))

    renderWithProviders()
    expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated')

    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: 'Logout' }))
    })

    expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated')
    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
  })

  it('handles failed profile refresh gracefully (expired token)', async () => {
    // Simulate a stored token that fails profile refresh
    server.use(
      http.get('http://localhost:8000/auth/me', () => {
        return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
      })
    )

    localStorage.setItem('token', 'expired-token')
    localStorage.setItem('user', JSON.stringify({ id: 1, username: 'olduser', email: 'old@test.com' }))

    // Should not throw — AuthContext catches the error silently
    expect(() => renderWithProviders()).not.toThrow()
  })
})
