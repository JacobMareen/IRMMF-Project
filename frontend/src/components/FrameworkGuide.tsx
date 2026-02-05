
import { useState } from 'react'
import './visuals/FrameworkVisuals.css'

export const FrameworkGuide = () => {
    const [isOpen, setIsOpen] = useState(false)

    if (!isOpen) {
        return (
            <button
                className="ah-btn secondary"
                onClick={() => setIsOpen(true)}
                style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem' }}
            >
                ℹ️ Methodology Guide
            </button>
        )
    }

    return (
        <div className="domain-overlay-backdrop active" onClick={() => setIsOpen(false)}>
            <div className="framework-guide-modal" onClick={(e) => e.stopPropagation()}>
                <div className="guide-header">
                    <h2>IRMMF Methodology</h2>
                    <button className="guide-close" onClick={() => setIsOpen(false)}>×</button>
                </div>
                <div className="guide-content">
                    <p className="guide-intro">
                        The <strong>Insider Risk Management Maturity Framework (IRMMF)</strong> uses a hybrid model to score organization maturity.
                        It combines "What" capabilities exist (Domains) with "How well" they operate (Axes of Quality).
                    </p>

                    <div className="guide-section">
                        <h3>9 Domains (Capabilities)</h3>
                        <p>The core functional areas of the program, from Governance and Culture to Technical Controls and Response.</p>
                    </div>

                    <div className="guide-section">
                        <h3>9 Axes of Quality</h3>
                        <div className="axes-grid">
                            <div className="axis-item"><strong>G</strong>overnance - Mandate & Oversight</div>
                            <div className="axis-item"><strong>E</strong>xecution - Consistency & Adoption</div>
                            <div className="axis-item"><strong>T</strong>echnical - Automation & Integration</div>
                            <div className="axis-item"><strong>L</strong>egal - Defensibility & Ethics</div>
                            <div className="axis-item"><strong>H</strong>uman - Culture & Safety</div>
                            <div className="axis-item"><strong>V</strong>isibility - Data & Assets</div>
                            <div className="axis-item"><strong>R</strong>esilience - Recovery & Learning</div>
                            <div className="axis-item"><strong>F</strong>riction - Usability & By-pass</div>
                            <div className="axis-item"><strong>W</strong>eight - Control Lag Management</div>
                        </div>
                    </div>

                    <div className="guide-section">
                        <h3>Scoring Model</h3>
                        <p>
                            Maturity is calculated using a <strong>Weighted Hybrid Mean</strong>.
                            This blends 75% arithmetic progress (building capabilities) with a 25% harmonic penalty (ensuring no critical gaps are left behind).
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
