import type { ReactNode } from 'react'
import { PageHeader } from './PageHeader'
import './CaseWorkspace.css'

type CaseWorkspaceProps = {
  title?: string
  titleAs?: 'h1' | 'h2'
  subtitle?: string
  actions?: ReactNode
  leftTitle?: string
  left: ReactNode
  rightTitle?: string
  right: ReactNode
  className?: string
}

const CaseWorkspace = ({
  title,
  titleAs = 'h2',
  subtitle,
  actions,
  leftTitle,
  left,
  rightTitle,
  right,
  className,
}: CaseWorkspaceProps) => {
  // PageHeader handles title rendering, titleAs is ignored for now but kept in props for compatibility if needed.
  return (
    <section className={['case-workspace', className].filter(Boolean).join(' ')}>
      {title || subtitle || actions ? (
        <PageHeader
          title={title || ''}
          subtitle={subtitle}
          actions={actions}
        />
      ) : null}
      <div className="case-workspace-grid">
        <div className="case-workspace-card">
          {leftTitle ? <div className="case-workspace-title">{leftTitle}</div> : null}
          {left}
        </div>
        <div className="case-workspace-card">
          {rightTitle ? <div className="case-workspace-title">{rightTitle}</div> : null}
          {right}
        </div>
      </div>
    </section>
  )
}

export default CaseWorkspace
