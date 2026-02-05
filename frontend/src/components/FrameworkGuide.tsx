
import { useMemo, useState } from 'react'
import './visuals/FrameworkVisuals.css'
import { DOMAIN_METADATA } from '../utils/domainMetadata'

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

    const domains = useMemo(() => Object.values(DOMAIN_METADATA), [])

    return (
        <div className="domain-overlay-backdrop active" onClick={() => setIsOpen(false)}>
            <div className="framework-guide-modal" onClick={(e) => e.stopPropagation()}>
                <div className="guide-header">
                    <div>
                        <h2>IRMMF Methodology Guide</h2>
                        <p className="guide-subtitle">A practical reference for interpreting maturity, risk, and capability depth.</p>
                    </div>
                    <button className="guide-close" onClick={() => setIsOpen(false)}>×</button>
                </div>
                <div className="guide-body">
                    <aside className="guide-nav">
                        <div className="guide-nav-title">Contents</div>
                        <a href="#guide-overview">Overview</a>
                        <a href="#guide-domains">Domains & Capabilities</a>
                        <a href="#guide-axes">Axes of Quality</a>
                        <a href="#guide-scoring">Scoring Model</a>
                        <a href="#guide-evidence">Evidence & Confidence</a>
                        <a href="#guide-benchmark">Benchmarking</a>
                        <a href="#guide-interpret">How to Read Results</a>
                        <a href="#guide-glossary">Glossary</a>
                    </aside>
                    <div className="guide-content">
                        <section id="guide-overview" className="guide-section">
                            <h3>Overview</h3>
                            <p className="guide-intro">
                                The <strong>Insider Risk Management Maturity Framework (IRMMF)</strong> measures both depth and quality of
                                insider risk programs. It combines <strong>Domains</strong> (what capabilities exist) with <strong>Axes of Quality</strong>
                                (how consistently, ethically, and effectively those capabilities operate).
                            </p>
                            <p>
                                The objective is to highlight strengths, expose blind spots, and drive a roadmap that aligns security outcomes
                                with business resilience. Scores reflect both maturity and operational integrity, not just policy coverage.
                            </p>
                        </section>

                        <section id="guide-domains" className="guide-section">
                            <h3>Domains & Capabilities</h3>
                            <p>
                                Domains represent the nine functional pillars of the program. Each domain includes a set of capability tags
                                used throughout the assessment to provide granular context and targeted recommendations.
                            </p>
                            <div className="guide-domain-grid">
                                {domains.map((domain) => (
                                    <div key={domain.id} className="guide-domain-card">
                                        <div className="guide-domain-header">
                                            <span className="guide-domain-icon">{domain.icon}</span>
                                            <div>
                                                <div className="guide-domain-title">{domain.label}</div>
                                                <div className="guide-domain-desc">{domain.description}</div>
                                            </div>
                                        </div>
                                        <div className="guide-domain-capabilities">
                                            {(domain.capabilities || []).map((cap) => (
                                                <span key={cap} className="guide-cap-tag">{cap}</span>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>

                        <section id="guide-axes" className="guide-section">
                            <h3>Axes of Quality</h3>
                            <p>
                                Axes measure the quality of execution across domains. A domain can only be considered mature if it performs
                                consistently across governance, execution, technical enablement, and legal defensibility.
                            </p>
                            <div className="axes-grid">
                                <div className="axis-item"><strong>G</strong>overnance - Mandate, ownership, and oversight.</div>
                                <div className="axis-item"><strong>E</strong>xecution - Consistency, adoption, and operational discipline.</div>
                                <div className="axis-item"><strong>T</strong>echnical - Tooling, automation, and integration maturity.</div>
                                <div className="axis-item"><strong>L</strong>egal - Defensibility, proportionality, and ethics.</div>
                                <div className="axis-item"><strong>H</strong>uman - Culture, safety, and workforce alignment.</div>
                                <div className="axis-item"><strong>V</strong>isibility - Coverage of data, users, and assets.</div>
                                <div className="axis-item"><strong>R</strong>esilience - Response, recovery, and learning loops.</div>
                                <div className="axis-item"><strong>F</strong>riction - Usability, bypass risk, and employee impact.</div>
                                <div className="axis-item"><strong>W</strong>eight - Control lag and decay management.</div>
                            </div>
                        </section>

                        <section id="guide-scoring" className="guide-section">
                            <h3>Scoring Model</h3>
                            <p>
                                IRMMF uses a <strong>Weighted Hybrid Mean</strong>: 75% arithmetic progress (capability build-out) and 25%
                                harmonic penalty (gap sensitivity). The harmonic component prevents isolated blind spots from being masked by
                                high scores elsewhere.
                            </p>
                            <div className="guide-callout">
                                Tip: A single weak axis in a critical domain will materially lower the composite score.
                            </div>
                        </section>

                        <section id="guide-evidence" className="guide-section">
                            <h3>Evidence & Confidence</h3>
                            <p>
                                Evidence confidence captures how strongly each response is supported by artifacts or verified controls.
                                Low confidence results help distinguish “paper maturity” from operational reality.
                            </p>
                            <ul className="guide-list">
                                <li>High confidence: tooling, metrics, and audit evidence confirmed.</li>
                                <li>Medium confidence: partial artifacts or informal attestations.</li>
                                <li>Low confidence: aspirational or unverified statements.</li>
                            </ul>
                        </section>

                        <section id="guide-benchmark" className="guide-section">
                            <h3>Benchmarking</h3>
                            <p>
                                Benchmarks compare your scores against simulated industry baselines. Use them to prioritize
                                domains where the gap is highest and risk exposure is greatest.
                            </p>
                        </section>

                        <section id="guide-interpret" className="guide-section">
                            <h3>How to Read Results</h3>
                            <ul className="guide-list">
                                <li>Start with the maturity radar to see domain balance.</li>
                                <li>Review gaps between declared vs. verified scores.</li>
                                <li>Use capability tags to translate gaps into concrete workstreams.</li>
                                <li>Pin an executive summary once aligned with leadership.</li>
                            </ul>
                        </section>

                        <section id="guide-glossary" className="guide-section">
                            <h3>Glossary</h3>
                            <div className="guide-glossary">
                                <div>
                                    <strong>Domain:</strong> A functional pillar of insider risk capability.
                                </div>
                                <div>
                                    <strong>Axis:</strong> A quality dimension applied across domains.
                                </div>
                                <div>
                                    <strong>Hybrid Mean:</strong> Arithmetic average with harmonic penalty for weak links.
                                </div>
                                <div>
                                    <strong>Confidence:</strong> Evidence strength behind a score.
                                </div>
                            </div>
                        </section>
                    </div>
                </div>
            </div>
        </div>
    )
}
