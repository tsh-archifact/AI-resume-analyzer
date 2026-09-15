import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import { ComparePage } from './pages/ComparePage'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { RewritePage } from './pages/RewritePage'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<RegisterPage />} />

            <Route element={<ProtectedRoute />}>
              <Route path="compare" element={<ComparePage />} />
              <Route path="rewrite" element={<RewritePage />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
