import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import PrivateRoute from './components/PrivateRoute'

// Pages
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import PatientsPage from './pages/PatientsPage'
import PatientDetailPage from './pages/PatientDetailPage'
import IsAkPage from './pages/IsAkPage'
import ConfigPage from './pages/ConfigPage'

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes */}
          <Route path="/dashboard" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
          <Route path="/patients" element={<PrivateRoute><PatientsPage /></PrivateRoute>} />
          <Route path="/patients/:id" element={<PrivateRoute><PatientDetailPage /></PrivateRoute>} />
          <Route path="/patients/:id/isak" element={<PrivateRoute><IsAkPage /></PrivateRoute>} />
          <Route path="/config" element={<PrivateRoute><ConfigPage /></PrivateRoute>} />

          {/* Redirect to dashboard by default */}
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </AuthProvider>
    </Router>
  )
}
