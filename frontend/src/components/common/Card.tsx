import { cls } from '../../utils/format'

export default function Card({
  className,
  hover,
  children,
  ...rest
}: React.HTMLAttributes<HTMLDivElement> & { hover?: boolean }) {
  return (
    <div className={cls('card', hover && 'card-hover', className)} {...rest}>
      {children}
    </div>
  )
}