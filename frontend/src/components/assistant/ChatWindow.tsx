import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Send } from 'lucide-react'
import type { ChatMessage } from '../../types'
import { api } from '../../services/api'

const SUGGESTIONS = [
  { key: 'scheme', en: 'Which scheme may suit me?', hi: 'कौन सी योजना मेरे लिए उपयुक्त हो सकती है?' },
  { key: 'documents', en: 'What documents might I need?', hi: 'मुझे कौन से दस्तावेज़ चाहिए?' },
  { key: 'emi', en: 'How can I estimate my EMI?', hi: 'मैं अपनी EMI का अनुमान कैसे लगाऊं?' },
  { key: 'partner', en: 'How do I find a channel partner?', hi: 'मुझे चैनल पार्टनर कैसे मिलेगा?' },
  { key: 'why', en: 'Why was this scheme recommended?', hi: 'यह योजना क्यों अनुशंसित की गई?' },
]

export default function ChatWindow({
  standalone,
  onClose,
}: {
  standalone?: boolean
  onClose?: () => void
}) {
  const { t, i18n } = useTranslation()
  const lang = (i18n.language || 'en').startsWith('hi') ? 'hi' : 'en'
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        lang === 'hi'
          ? 'नमस्ते! मैं सक्षम सहायक हूँ। मैं आपकी योजना खोजने, EMI अनुमान और पार्टनर ढूंढने में मदद कर सकता हूँ।'
          : 'Namaste! I am the Saksham assistant. I can help you find schemes, estimate EMI, and locate partners.',
    },
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, busy])

  async function send(text: string) {
    const content = text.trim()
    if (!content || busy) return
    const next: ChatMessage[] = [...messages, { role: 'user', content }]
    setMessages(next)
    setInput('')
    setBusy(true)
    try {
      const res = await api.assistant.chat({
        message: content,
        language: lang,
        history: next,
      })
      setMessages([...next, { role: 'assistant', content: res.message }])
    } catch {
      setMessages([
        ...next,
        {
          role: 'assistant',
          content:
            lang === 'hi'
              ? 'क्षमा करें, कुछ गलत हुआ। कृपया दोबारा कोशिश करें।'
              : 'Sorry, something went wrong. Please try again.',
        },
      ])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      className={`flex flex-col overflow-hidden rounded-2xl bg-white shadow-elevated ${
        standalone ? 'h-[calc(100vh-16rem)] min-h-[420px]' : 'h-[540px]'
      }`}
    >
      <div className="flex items-center justify-between border-b border-slate-100 bg-navy px-4 py-3">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-white">
            🤖
          </span>
          <div>
            <p className="text-sm font-semibold text-white">Saksham AI Assistant</p>
            <p className="text-[11px] text-white/60">English · हिंदी</p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-white/80 hover:bg-white/10"
            aria-label={t('common.close')}
          >
            ✕
          </button>
        )}
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto bg-slate-50 p-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
                m.role === 'user'
                  ? 'bg-brand-700 text-white'
                  : 'border border-slate-200 bg-white text-slate-700'
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex items-center gap-1.5 text-slate-400">
            <span className="text-sm">AI</span>
            <span className="flex gap-1">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: '120ms' }} />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: '240ms' }} />
            </span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {messages.length <= 2 && (
        <div className="border-t border-slate-100 bg-white px-4 py-3">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            {t('assistant.suggested')}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {SUGGESTIONS.slice(0, 3).map((s) => (
              <button
                key={s.key}
                onClick={() => send(lang === 'hi' ? s.hi : s.en)}
                className="rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:border-brand-300 hover:text-brand-800"
              >
                {lang === 'hi' ? s.hi : s.en}
              </button>
            ))}
          </div>
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault()
          send(input)
        }}
        className="flex items-center gap-2 border-t border-slate-100 bg-white px-3 py-2.5"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t('assistant.placeholder')}
          className="input flex-1"
          aria-label={t('assistant.placeholder')}
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className="btn-primary px-3.5"
          aria-label={t('assistant.send')}
        >
          <Send className="h-4 w-4" aria-hidden />
        </button>
      </form>
    </div>
  )
}