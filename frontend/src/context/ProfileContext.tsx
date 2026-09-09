import { createContext, useContext, useMemo } from 'react'
import type { Profile, RecommendationResult, Scheme } from '../types'
import { useLocalStorage } from '../hooks/useFetch'

interface JourneyState {
  profile: Profile | null
  setProfileData: (profile: Profile) => void
  recommendations: RecommendationResult[] | null
  setRecommendationsData: (recs: RecommendationResult[] | null) => void
  selectedScheme: Scheme | null
  setSelectedSchemeData: (scheme: Scheme | null) => void
  loanRequired: number | null
  setLoanRequired: (n: number | null) => void
  reset: () => void
}

const ProfileContext = createContext<JourneyState | null>(null)

export function ProfileProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfile] = useLocalStorage<Profile | null>('saksham-profile', null)
  const [recommendations, setRecommendations] = useLocalStorage<RecommendationResult[] | null>(
    'saksham-recommendations',
    null,
  )
  const [selectedScheme, setSelectedScheme] = useLocalStorage<Scheme | null>(
    'saksham-selected-scheme',
    null,
  )
  const [loanRequired, setLoanRequired] = useLocalStorage<number | null>('saksham-loan', null)

  const value = useMemo<JourneyState>(
    () => ({
      profile,
      setProfileData: setProfile,
      recommendations,
      setRecommendationsData: setRecommendations,
      selectedScheme,
      setSelectedSchemeData: setSelectedScheme,
      loanRequired,
      setLoanRequired,
      reset: () => {
        setProfile(null)
        setRecommendations(null)
        setSelectedScheme(null)
        setLoanRequired(null)
      },
    }),
    [profile, recommendations, selectedScheme, loanRequired, setProfile, setRecommendations, setSelectedScheme, setLoanRequired],
  )

  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>
}

export function useProfile(): JourneyState {
  const ctx = useContext(ProfileContext)
  if (!ctx) throw new Error('useProfile must be used within ProfileProvider')
  return ctx
}