import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { CheckCircle2, ExternalLink, Send, ShieldAlert, X } from 'lucide-react'
import type { ChatMessage } from '../../types'
import { api } from '../../services/api'

const SUGGESTIONS = [
  { key: 'scheme', en: 'Which scheme may suit me?', hi: 'कौन सी योजना मेरे लिए उपयुक्त हो सकती है?' },
  { key: 'documents', en: 'What documents might I need?', hi: 'मुझे कौन से दस्तावेज़ चाहिए?' },
  { key: 'emi', en: 'How can I estimate my EMI?', hi: 'मैं अपनी EMI का अनुमान कैसे लगाऊं?' },
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
          ? 'नमस्ते! मैं सक्षम सहायक हूँ। बताएं आपको किस चीज़ में मदद चाहिए — व्यवसाय ऋण, शिक्षा ऋण, कौशल प्रशिक्षण, या अन्य सरकारी सहायता?'
          : 'Namaste! I am the Saksham assistant. Tell me what you need help with — a business loan, education loan, skill training, or other government support.',
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
      const reply: ChatMessage = {
        role: 'assistant',
        content: res.message,
        structured: res.structured ?? undefined,
        step: res.step ?? undefined,
        totalSteps: res.total_steps ?? undefined,
      }
      setMessages([...next, reply])
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
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto bg-slate-50 p-4">
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} lang={lang} />
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

function MessageBubble({ message, lang }: { message: ChatMessage; lang: string }) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl bg-brand-700 px-3.5 py-2.5 text-sm leading-relaxed text-white">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[92%] space-y-2 rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm leading-relaxed text-slate-700">
        {message.step !== undefined && (
          <StepBadge step={message.step} total={message.totalSteps ?? 7} lang={lang} />
        )}
        <p className="whitespace-pre-wrap">{message.content}</p>
        {message.structured && message.structured.length > 0 && (
          <div className="space-y-2 pt-2">
            {message.structured.map((card) => (
              <SchemeResultCard key={card.scheme_slug} card={card} lang={lang} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StepBadge({ step, total, lang }: { step: number; total: number; lang: string }) {
  return (
    <div className="mb-1 inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-2.5 py-1 text-[11px] font-medium text-brand-700">
      <span className="h-1.5 w-1.5 rounded-full bg-brand-600" />
      {lang === 'hi' ? `चरण ${step}/${total}` : `Step ${step}/${total}`}
    </div>
  )
}

function SchemeResultCard({ card, lang }: { card: NonNullable<ChatMessage['structured']>[number]; lang: string }) {
  const verified = card.data_confidence === 'verified'
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
      <div className="flex items-start justify-between gap-2">
        <p className="text-[13px] font-semibold text-slate-800">{card.scheme_name}</p>
        <span className="ml-2 shrink-0 rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-medium text-slate-600">
          {card.match_score}%
        </span>
      </div>

      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
        {verified ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
            <CheckCircle2 className="h-3 w-3" /> Verified
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700">
            <ShieldAlert className="h-3 w-3" /> Needs review
          </span>
        )}
        {card.interest_display && (
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600">
            {card.interest_display}
          </span>
        )}
        {card.max_loan != null && card.max_loan > 0 && (
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600">
            ₹{card.max_loan.toLocaleString('en-IN')}
          </span>
        )}
      </div>

      {card.reasons.length > 0 && (
        <ul className="mt-2 space-y-0.5">
          {card.reasons.slice(0, 3).map((r, i) => (
            <li key={i} className="flex items-start gap-1.5 text-[12px] text-slate-600">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-brand-500" />
              <span>{r}</span>
            </li>
          ))}
        </ul>
      )}

      {card.official_scheme_url && (
        <a
          href={card.official_scheme_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-brand-700 hover:text-brand-800 hover:underline"
        >
          <ExternalLink className="h-3 w-3" />
          {lang === 'hi' ? 'आधिकारिक स्रोत देखें' : 'Official source'}
        </a>
      )}
    </div>
  )
}