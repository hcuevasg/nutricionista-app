import { Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import PrivateRoute from './components/PrivateRoute'
import { lazyPage } from './utils/lazyPage'

// Páginas: el login se carga de inmediato; el resto bajo demanda para aligerar la primera carga
import LoginPage from './pages/LoginPage'
const RegisterPage = lazyPage(() => import('./pages/RegisterPage'))
const DashboardPage = lazyPage(() => import('./pages/DashboardPage'))
const PatientsPage = lazyPage(() => import('./pages/PatientsPage'))
const PatientFormPage = lazyPage(() => import('./pages/PatientFormPage'))
const PatientDetailPage = lazyPage(() => import('./pages/PatientDetailPage'))
const IsAkPage = lazyPage(() => import('./pages/IsAkPage'))
const PautasPage = lazyPage(() => import('./pages/PautasPage'))
const PautaFormPage = lazyPage(() => import('./pages/PautaFormPage'))
const ConfigPage = lazyPage(() => import('./pages/ConfigPage'))
const ProfilePage = lazyPage(() => import('./pages/ProfilePage'))
const AntecedentesPage = lazyPage(() => import('./pages/AntecedentesPage'))
const RecetasPage = lazyPage(() => import('./pages/RecetasPage'))
const RecetaFormPage = lazyPage(() => import('./pages/RecetaFormPage'))
const IsAkReportPage = lazyPage(() => import('./pages/IsAkReportPage'))
const PautaReportPage = lazyPage(() => import('./pages/PautaReportPage'))
const AgendaPage = lazyPage(() => import('./pages/AgendaPage'))
const PortalPage = lazyPage(() => import('./pages/PortalPage'))
const PatientProgressPage = lazyPage(() => import('./pages/PatientProgressPage'))
const PrivacyPage = lazyPage(() => import('./pages/PrivacyPage'))
const EvolucionPage = lazyPage(() => import('./pages/EvolucionPage'))
const LaboratorioPage = lazyPage(() => import('./pages/LaboratorioPage'))

function PageLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-light">
      <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" role="status" aria-label="Cargando" />
    </div>
  )
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
      <ToastProvider>
        <Suspense fallback={<PageLoading />}>
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
          <Route path="/patients/:id/laboratorio" element={<PrivateRoute><LaboratorioPage /></PrivateRoute>} />
          <Route path="/recetas" element={<PrivateRoute><RecetasPage /></PrivateRoute>} />
          <Route path="/recetas/new" element={<PrivateRoute><RecetaFormPage /></PrivateRoute>} />
          <Route path="/recetas/:recetaId/edit" element={<PrivateRoute><RecetaFormPage /></PrivateRoute>} />
          <Route path="/agenda" element={<PrivateRoute><AgendaPage /></PrivateRoute>} />
          <Route path="/config" element={<PrivateRoute><ConfigPage /></PrivateRoute>} />
          <Route path="/profile" element={<PrivateRoute><ProfilePage /></PrivateRoute>} />

          {/* Redirect to dashboard by default */}
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
        </Suspense>
      </ToastProvider>
      </AuthProvider>
    </Router>
  )
}
