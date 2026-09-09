import { AlertTriangle } from 'lucide-react'
import Button from './Button'

export default function ErrorState({
  message,
  onRetry,
}: {
  message?: string
  onRetry?: () => void
}) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-2xl border border-red-200 bg-red-50 px-6 py-12 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
        <AlertTriangle className="h-6 w-6 text-red-600" aria-hidden />
      </span>
      <div>
        <p className="font-semibold text-red-800">Unable to load data</p>
        <p className="mt-1 text-sm text-red-600">
          {message || 'Unable to load data. Please try again.'}
        </p>
      </div>
      {onRetry && <Button variant="secondary" onClick={onRetry}>Retry</Button>}
    </div>
  )
}