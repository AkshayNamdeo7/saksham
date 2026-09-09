import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import FloatingAssistant from './components/assistant/FloatingAssistant'
import LoadingScreen from './components/common/LoadingScreen'
import ScrollToTop from './components/common/ScrollToTop'
import { ProfileProvider } from './context/ProfileContext'
import { ToastProvider } from './context/ToastContext'

const Home = lazy(() => import('./pages/Home'))
const Eligibility = lazy(() => import('./pages/Eligibility'))
const Recommendation = lazy(() => import('./pages/Recommendation'))
const Schemes = lazy(() => import('./pages/Schemes'))
const SchemeDetail = lazy(() => import('./pages/SchemeDetail'))
const Compare = lazy(() => import('./pages/Compare'))
const Calculator = lazy(() => import('./pages/Calculator'))
const Partners = lazy(() => import('./pages/Partners'))
const Assistant = lazy(() => import('./pages/Assistant'))
const Documents = lazy(() => import('./pages/Documents'))
const Application = lazy(() => import('./pages/Application'))
const About = lazy(() => import('./pages/About'))

const AdminLogin = lazy(() => import('./pages/admin/AdminLogin'))
const AdminLayout = lazy(() => import('./pages/admin/AdminLayout'))
const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard'))
const AdminSchemes = lazy(() => import('./pages/admin/AdminSchemes'))
const AdminPartners = lazy(() => import('./pages/admin/AdminPartners'))
const AdminApplications = lazy(() => import('./pages/admin/AdminApplications'))
const AdminSettings = lazy(() => import('./pages/admin/AdminSettings'))

function withLoader(el: React.ReactNode) {
  return <Suspense fallback={<LoadingScreen />}>{el}</Suspense>
}

export default function App() {
  return (
    <ToastProvider>
      <ProfileProvider>
        <Routes>
          <Route
            path="/"
            element={
              <Suspense fallback={<LoadingScreen />}>
                <AppLayout />
              </Suspense>
            }
          >
            <Route index element={withLoader(<Home />)} />
            <Route path="/eligibility" element={withLoader(<Eligibility />)} />
            <Route path="/recommendation" element={withLoader(<Recommendation />)} />
            <Route path="/schemes" element={withLoader(<Schemes />)} />
            <Route path="/schemes/:id" element={withLoader(<SchemeDetail />)} />
            <Route path="/compare" element={withLoader(<Compare />)} />
            <Route path="/calculator" element={withLoader(<Calculator />)} />
            <Route path="/partners" element={withLoader(<Partners />)} />
            <Route path="/assistant" element={withLoader(<Assistant />)} />
            <Route path="/documents" element={withLoader(<Documents />)} />
            <Route path="/application" element={withLoader(<Application />)} />
            <Route path="/about" element={withLoader(<About />)} />
          </Route>
          <Route path="/admin/login" element={withLoader(<AdminLogin />)} />
          <Route path="/admin" element={withLoader(<AdminLayout />)}>
            <Route index element={withLoader(<AdminDashboard />)} />
            <Route path="dashboard" element={withLoader(<AdminDashboard />)} />
            <Route path="schemes" element={withLoader(<AdminSchemes />)} />
            <Route path="partners" element={withLoader(<AdminPartners />)} />
            <Route path="applications" element={withLoader(<AdminApplications />)} />
            <Route path="settings" element={withLoader(<AdminSettings />)} />
          </Route>
          <Route
            path="*"
            element={
              <div className="container-app py-24 text-center">
                <p className="text-4xl font-bold text-slate-900">404</p>
                <p className="mt-2 text-slate-500">Page not found.</p>
              </div>
            }
          />
        </Routes>
        <FloatingAssistant />
        <ScrollToTop />
      </ProfileProvider>
    </ToastProvider>
  )
}