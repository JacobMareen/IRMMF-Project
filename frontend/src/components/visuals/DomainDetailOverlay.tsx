
import { getDomainMeta } from '../../utils/domainMetadata'
import type { DomainMeta } from '../../utils/domainMetadata'
import './FrameworkVisuals.css'

type DomainData = {
    domain: string
    status: string
    remaining: number
    answered: number
    total: number
}

type DomainDetailOverlayProps = {
    domainData: DomainData | null
    onClose: () => void
    onOpen: (domain: string) => void
    overrideEnabled: boolean
    onToggleOverride: (enabled: boolean) => void
}

const DomainDetailOverlay = ({ domainData, onClose, onOpen, overrideEnabled, onToggleOverride }: DomainDetailOverlayProps) => {
    // If no data, return empty invisible div (or null, but preserving animation needs care)
    // We rely on CSS 'active' class for visibility.
    // However, we need 'meta' and 'pct' even if domainData is null to avoid crashes if we render them.
    // We cast the fallback to DomainMeta to satisfy TS.
    const meta = domainData ? getDomainMeta(domainData.domain) : {
        id: '',
        icon: '',
        label: '',
        description: '',
        color: '',
        longDescription: '',
        capabilities: []
    } as DomainMeta

    const pct = domainData && domainData.total > 0 ? Math.round((domainData.answered / domainData.total) * 100) : 0

    return (
        <div className={`domain-overlay-backdrop ${domainData ? 'active' : ''}`} onClick={onClose}>
            <div className={`domain-overlay ${domainData ? 'active' : ''}`} onClick={(e) => e.stopPropagation()}>
                <div className="domain-overlay-header">
                    <div>
                        <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span>{meta.icon}</span>
                            {meta.label}
                        </h2>
                    </div>
                    <button className="domain-overlay-close" onClick={onClose}>×</button>
                </div>

                <div className="domain-overlay-content">
                    <p style={{ color: 'var(--text-sub)', lineHeight: '1.6', marginTop: 0 }}>
                        {meta.longDescription || meta.description}
                    </p>

                    {meta.capabilities && meta.capabilities.length > 0 && (
                        <div className="domain-capabilities">
                            <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Key Capabilities</h4>
                            <ul style={{ margin: 0, paddingLeft: '1.2rem', color: 'var(--text-sub)', fontSize: '0.9rem' }}>
                                {meta.capabilities.map((cap, i) => (
                                    <li key={i} style={{ marginBottom: '0.25rem' }}>{cap}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <div className="ah-divider" style={{ margin: '1.5rem 0', borderTop: '1px solid var(--border-color)' }} />

                    <div className="domain-stat-grid">
                        <div className="domain-stat-item">
                            <span className="domain-stat-val" style={{ color: meta.color }}>{pct}%</span>
                            <span className="domain-stat-label">Completion</span>
                        </div>
                        <div className="domain-stat-item">
                            <span className="domain-stat-val">{domainData?.remaining || 0}</span>
                            <span className="domain-stat-label">Questions Remaining</span>
                        </div>
                        <div className="domain-stat-item">
                            <span className="domain-stat-val">{domainData?.answered || 0}</span>
                            <span className="domain-stat-label">Answered</span>
                        </div>
                        <div className="domain-stat-item">
                            <span className="domain-stat-val">{domainData?.total || 0}</span>
                            <span className="domain-stat-label">Total Scope</span>
                        </div>
                    </div>

                    <h3 style={{ fontSize: '1rem', marginTop: '2rem' }}>Assessment Status</h3>
                    <p>
                        {domainData?.status === 'completed'
                            ? 'All questions in the active path have been answered.'
                            : 'There are open questions waiting for your input.'}
                    </p>

                    <div className="ah-divider" style={{ margin: '1.5rem 0', borderTop: '1px solid var(--border-color)' }} />

                    <div className="ah-divider" style={{ margin: '1.5rem 0', borderTop: '1px solid var(--border-color)' }} />

                    {/* Deep Dive Unlock Section */}
                    {overrideEnabled ? (
                        <div className="check-card active" onClick={() => onToggleOverride(false)}>
                            <div className="check-card-icon">✓</div>
                            <div className="check-card-content">
                                <h4>Deep Dive Active</h4>
                                <p>Extended question set enabled. Uncheck to revert to standard scope.</p>
                            </div>
                        </div>
                    ) : (
                        <div className="unlock-card" onClick={() => onToggleOverride(true)}>
                            <div className="unlock-icon">🔒</div>
                            <div className="unlock-content">
                                <h4>Unlock Deep Dive</h4>
                                <p>Reveal advanced capability questions for this domain.</p>
                            </div>
                            <button className="ah-btn sm">Unlock</button>
                        </div>
                    )}

                </div>

                <div className="domain-actions">
                    <button
                        className="ah-btn primary"
                        onClick={() => domainData && onOpen(domainData.domain)}
                        disabled={!domainData}
                    >
                        Open Domain Assessment
                    </button>
                </div>
            </div>
        </div>
    )
}

export default DomainDetailOverlay
