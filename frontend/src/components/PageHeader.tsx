import type { ReactNode } from 'react'
import './PageHeader.css'

type PageHeaderProps = {
    title: string
    subtitle?: string
    statusNote?: string | null
    actions?: ReactNode
    className?: string
}

export const PageHeader = ({
    title,
    subtitle,
    statusNote,
    actions,
    className,
}: PageHeaderProps) => {
    return (
        <div className={['page-header', className].filter(Boolean).join(' ')}>
            <div>
                <h1 className="page-header-title">{title}</h1>
                {subtitle && <p className="page-header-subtitle">{subtitle}</p>}
                {statusNote && <div className="page-header-note">{statusNote}</div>}
            </div>
            {actions && <div className="page-header-actions">{actions}</div>}
        </div>
    )
}
