import ChatWindow from '../components/assistant/ChatWindow'
import { useTranslation } from 'react-i18next'

export default function Assistant() {
  const { t } = useTranslation()
  return (
    <div className="container-app max-w-3xl py-12">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{t('assistant.title')}</h1>
        <p className="mt-2 text-slate-500">{t('assistant.subtitle')}</p>
      </div>
      <div className="mt-8">
        <ChatWindow standalone />
      </div>
    </div>
  )
}