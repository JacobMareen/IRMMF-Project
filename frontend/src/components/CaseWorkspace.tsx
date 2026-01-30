import { ReactNode } from 'react'
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
  const TitleTag = titleAs
  return (
    <section className={['case-workspace', className].filter(Boolean).join(' ')}>
      {title || subtitle || actions ? (
        <div className="case-workspace-header">
          <div>
            {title ? <TitleTag>{title}</TitleTag> : null}
            {subtitle ? <p className="case-workspace-subtitle">{subtitle}</p> : null}
          </div>
          {actions ? <div className="case-workspace-actions">{actions}</div> : null}
        </div>
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
