import React, { useState, useEffect } from 'react'
import './TargetMaturityModal.css'

interface TargetMaturityModalProps {
    currentTargets: Record<string, number>
    onSave: (targets: Record<string, number>) => void
    onClose: () => void
}

const DOMAINS = [
    '1. Governance & Structure',
    '2. Policy & Procedure',
    '3. Awareness & Culture',
    '4. Legal, Privacy & Ethics',
    '5. Human-Centric Culture',
    '6. Executive Oversight',
    '7. Behavioral Analytics & Detection',
    '8. Investigation & Response',
]

export const TargetMaturityModal: React.FC<TargetMaturityModalProps> = ({
    currentTargets,
    onSave,
    onClose,
}) => {
    const [targets, setTargets] = useState<Record<string, number>>(currentTargets || {})

    const handleChange = (domain: string, value: string) => {
        const numVal = parseFloat(value)
        if (!isNaN(numVal) && numVal >= 0 && numVal <= 4) {
            setTargets((prev) => ({ ...prev, [domain]: numVal }))
        }
    }

    const handleSave = () => {
        onSave(targets)
        onClose()
    }

    return (
        <div className="tm-modal-overlay">
            <div className="tm-modal">
                <div className="tm-header">
                    <h3>Set Target Maturity</h3>
                    <button className="tm-close" onClick={onClose}>
                        &times;
                    </button>
                </div>
                <div className="tm-body">
                    <p className="tm-desc">
                        Define your expected maturity level (0.0 - 4.0) for each domain. This creates a gap
                        analysis baseline.
                    </p>
                    <div className="tm-grid">
                        {DOMAINS.map((domain) => (
                            <div key={domain} className="tm-row">
                                <span className="tm-domain">{domain}</span>
                                <input
                                    type="number"
                                    min="0"
                                    max="4"
                                    step="0.1"
                                    value={targets[domain] || 0}
                                    onChange={(e) => handleChange(domain, e.target.value)}
                                    className="tm-input"
                                />
                            </div>
                        ))}
                    </div>
                </div>
                <div className="tm-footer">
                    <button className="btn secondary" onClick={onClose}>
                        Cancel
                    </button>
                    <button className="btn primary" onClick={handleSave}>
                        Save Targets
                    </button>
                </div>
            </div>
        </div>
    )
}
