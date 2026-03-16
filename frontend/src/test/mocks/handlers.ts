import { http, HttpResponse } from 'msw'

const API = 'http://localhost:8000'

export const handlers = [
  // Auth
  http.post(`${API}/auth/login`, () => {
    return HttpResponse.json({
      access_token: 'fake-token-123',
      token_type: 'bearer',
      user: { id: 1, username: 'testuser', email: 'test@test.com', name: 'Test User' },
    })
  }),

  http.get(`${API}/auth/me`, () => {
    return HttpResponse.json({
      id: 1,
      username: 'testuser',
      email: 'test@test.com',
      name: 'Test User',
      clinic_name: 'Clínica Test',
    })
  }),

  // Patients
  http.get(`${API}/patients`, () => {
    return HttpResponse.json({
      items: [
        { id: 1, name: 'Ana García', sex: 'F', birth_date: '1990-05-15', email: 'ana@test.com', phone: '912345678', nutritionist_id: 1, created_at: '2024-01-01T00:00:00', updated_at: '2024-01-01T00:00:00', allergies: [] },
        { id: 2, name: 'Carlos López', sex: 'M', birth_date: '1985-03-20', email: 'carlos@test.com', phone: '987654321', nutritionist_id: 1, created_at: '2024-01-01T00:00:00', updated_at: '2024-01-01T00:00:00', allergies: ['gluten'] },
      ],
      total: 2,
      skip: 0,
      limit: 50,
    })
  }),
]
