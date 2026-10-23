import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import PrivateRoute from './components/PrivateRoute'

// Pages
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import PatientsPage from './pages/PatientsPage'
import PatientFormPage from './pages/PatientFormPage'
import PatientDetailPage from './pages/PatientDetailPage'
import IsAkPage from './pages/IsAkPage'
import PautasPage from './pages/PautasPage'
import PautaFormPage from './pages/PautaFormPage'
import ConfigPage from './pages/ConfigPage'
import ProfilePage from './pages/ProfilePage'
import AntecedentesPage from './pages/AntecedentesPage'
import RecetasPage from './pages/RecetasPage'
import RecetaFormPage from './pages/RecetaFormPage'
import IsAkReportPage from './pages/IsAkReportPage'
import PautaReportPage from './pages/PautaReportPage'
import AgendaPage from './pages/AgendaPage'
import PortalPage from './pages/PortalPage'
import PatientProgressPage from './pages/PatientProgressPage'
import PrivacyPage from './pages/PrivacyPage'
import EvolucionPage from './pages/EvolucionPage'

export default function App() {
  return (
    <Router>
      <AuthProvider>
      <ToastProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/portal/:token" element={<PortalPage />} />
          <Route path="/privacidad" element={<PrivacyPage />} />

          {/* Protected routes */}
          <Route path="/dashboard" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
          <Route path="/patients" element={<PrivateRoute><PatientsPage /></PrivateRoute>} />
          <Route path="/patients/new" element={<PrivateRoute><PatientFormPage /></PrivateRoute>} />
          <Route path="/patients/:id" element={<PrivateRoute><PatientDetailPage /></PrivateRoute>} />
          <Route path="/patients/:id/edit" element={<PrivateRoute><PatientFormPage /></PrivateRoute>} />
          <Route path="/patients/:id/isak" element={<PrivateRoute><IsAkPage /></PrivateRoute>} />
          <Route path="/patients/:id/isak/:evalId/report" element={<PrivateRoute><IsAkReportPage /></PrivateRoute>} />
          <Route path="/patients/:id/pautas" element={<PrivateRoute><PautasPage /></PrivateRoute>} />
          <Route path="/patients/:id/pautas/new" element={<PrivateRoute><PautaFormPage /></PrivateRoute>} />
          <Route path="/patients/:id/pautas/:pautaId" element={<PrivateRoute><PautaFormPage /></PrivateRoute>} />
          <Route path="/patients/:id/pautas/:pautaId/edit" element={<PrivateRoute><PautaFormPage /></PrivateRoute>} />
          <Route path="/patients/:id/pautas/:pautaId/report" element={<PrivateRoute><PautaReportPage /></PrivateRoute>} />
          <Route path="/patients/:id/antecedentes" element={<PrivateRoute><AntecedentesPage /></PrivateRoute>} />
          <Route path="/patients/:id/progress" element={<PrivateRoute><PatientProgressPage /></PrivateRoute>} />
          <Route path="/patients/:id/evolucion" element={<PrivateRoute><EvolucionPage /></PrivateRoute>} />
          <Route path="/recetas" element={<PrivateRoute><RecetasPage /></PrivateRoute>} />
          <Route path="/recetas/new" element={<PrivateRoute><RecetaFormPage /></PrivateRoute>} />
          <Route path="/recetas/:recetaId/edit" element={<PrivateRoute><RecetaFormPage /></PrivateRoute>} />
          <Route path="/agenda" element={<PrivateRoute><AgendaPage /></PrivateRoute>} />
          <Route path="/config" element={<PrivateRoute><ConfigPage /></PrivateRoute>} />
          <Route path="/profile" element={<PrivateRoute><ProfilePage /></PrivateRoute>} />

          {/* Redirect to dashboard by default */}
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </ToastProvider>
      </AuthProvider>
    </Router>
  )
}
