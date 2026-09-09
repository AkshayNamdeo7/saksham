import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './en'
import hi from './hi'

const saved = localStorage.getItem('saksham-lang')

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    hi: { translation: hi },
  },
  lng: saved === 'hi' || saved === 'en' ? saved : 'en',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
})

export function setAppLanguage(lang: 'en' | 'hi') {
  localStorage.setItem('saksham-lang', lang)
  i18n.changeLanguage(lang)
}

export default i18n