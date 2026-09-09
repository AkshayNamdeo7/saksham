import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { MessageSquareText, X } from 'lucide-react'
import ChatWindow from './ChatWindow'

export default function FloatingAssistant() {
  const [open, setOpen] = useState(false)
  const location = useLocation()

  if (location.pathname === '/assistant' || location.pathname.startsWith('/admin')) {
    return null
  }

  return (
    <div className="fixed bottom-5 right-5 z-40">
      {open && (
        <div className="mb-3 w-[92vw] max-w-sm">
          <ChatWindow onClose={() => setOpen(false)} />
        </div>
      )}
      <button
        onClick={() => setOpen(!open)}
        aria-label={open ? 'Close AI assistant' : 'Open AI assistant'}
        aria-expanded={open}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-700 text-white shadow-elevated transition hover:scale-105 hover:bg-brand-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
      >
        {open ? <X className="h-6 w-6" /> : <MessageSquareText className="h-6 w-6" />}
      </button>
    </div>
  )
}