import { cls } from '../../utils/format'

interface FieldProps {
  label?: string
  error?: string
  hint?: string
  id?: string
  required?: boolean
  children: React.ReactNode
}

export function Field({ label, error, hint, id, required, children }: FieldProps) {
  return (
    <div>
      {label && (
        <label htmlFor={id} className="label">
          {label}
          {required && <span className="ml-0.5 text-red-500">*</span>}
        </label>
      )}
      {children}
      {hint && !error && <p className="mt-1.5 text-xs text-slate-400">{hint}</p>}
      {error && (
        <p role="alert" className="mt-1.5 text-xs font-medium text-red-600">
          {error}
        </p>
      )}
    </div>
  )
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
}

export function Input({ className, error, ...rest }: InputProps) {
  return (
    <input
      className={cls(
        'input',
        error && 'border-red-400 focus:border-red-500 focus:ring-red-500/20',
        className,
      )}
      {...rest}
    />
  )
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean
  options?: { value: string; label: string }[]
  placeholder?: string
}

export function Select({ className, error, options, placeholder, ...rest }: SelectProps) {
  return (
    <select
      className={cls(
        'input appearance-none',
        error && 'border-red-400 focus:border-red-500 focus:ring-red-500/20',
        className,
      )}
      {...rest}
    >
      {placeholder && <option value="">{placeholder}</option>}
      {options?.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  )
}