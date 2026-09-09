import { Outlet } from 'react-router-dom'
import Header from '../navigation/Header'
import Footer from '../navigation/Footer'

export default function AppLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}