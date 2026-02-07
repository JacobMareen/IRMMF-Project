
import { useMemo, useState } from 'react'
import { getDomainMeta } from '../../utils/domainMetadata'
import './FrameworkVisuals.css'

type DomainData = {
    domain: string
    status: string
    remaining: number
    answered: number
    total: number
}

type FrameworkRadarProps = {
    domains: DomainData[]
    onDomainClick: (domain: DomainData) => void
}

const RADIUS = 180 // Increased from 150
const CENTER = 250 // Increased from 200 (SVG Size 500x500)

const FrameworkRadar = ({ domains, onDomainClick }: FrameworkRadarProps) => {
    const [hoveredDomain, setHoveredDomain] = useState<string | null>(null)

    // Helper to calculate polar coordinates
    const polarToCartesian = (centerX: number, centerY: number, radius: number, angleInDegrees: number) => {
        const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0
        return {
            x: centerX + (radius * Math.cos(angleInRadians)),
            y: centerY + (radius * Math.sin(angleInRadians))
        }
    }

    // Helper to create slice path
    const describeArc = (x: number, y: number, radius: number, startAngle: number, endAngle: number) => {
        const start = polarToCartesian(x, y, radius, endAngle)
        const end = polarToCartesian(x, y, radius, startAngle)
        const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1"
        return [
            "M", x, y,
            "L", start.x, start.y,
            "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y,
            "L", x, y
        ].join(" ")
    }

    const slices = useMemo(() => {
        if (domains.length === 0) return []
        const sliceAngle = 360 / domains.length

        return domains.map((d, index) => {
            const startAngle = index * sliceAngle
            const endAngle = startAngle + sliceAngle
            const meta = getDomainMeta(d.domain)

            // Calculate fill radius based on completion
            const pct = d.total > 0 ? (d.answered / d.total) : 0

            // Ghost Bar: If answered is low, show a faint "potential" bar?
            // Actually, the background slice already represents the "Total Capacity".
            // Let's just rely on the background slice being visible.

            // Min radius for visibility, Max radius slightly less than full
            const fillRadius = (RADIUS * 0.2) + (RADIUS * 0.8 * pct)

            // Label position - Push further out
            const labelAngle = startAngle + sliceAngle / 2
            // increased buffer from 30 to 45 for better separation
            const labelPos = polarToCartesian(CENTER, CENTER, RADIUS + 45, labelAngle)

            return {
                data: d,
                meta,
                pathBg: describeArc(CENTER, CENTER, RADIUS, startAngle, endAngle), // Full slice background
                pathFill: describeArc(CENTER, CENTER, fillRadius, startAngle, endAngle), // Progress fill
                labelPos,
                labelAnchor: labelAngle > 180 ? 'end' : 'start',
                index
            }
        })
    }, [domains])

    const activeMeta = hoveredDomain ? getDomainMeta(hoveredDomain) : null
    const activeData = hoveredDomain ? domains.find(d => d.domain === hoveredDomain) : null

    return (
        <div className="framework-radar-container">
            <svg width="600" height="500" className="radar-svg" viewBox={`0 0 ${CENTER * 2} ${CENTER * 2}`}>
                {/* Background Slices */}
                {slices.map((slice) => (
                    <path
                        key={`bg-${slice.data.domain}`}
                        d={slice.pathBg}
                        className="radar-slice radar-slice-bg"
                        fill="transparent"
                        onClick={() => onDomainClick(slice.data)}
                        onMouseEnter={() => setHoveredDomain(slice.data.domain)}
                        onMouseLeave={() => setHoveredDomain(null)}
                    />
                ))}

                {/* Filled Progress */}
                {slices.map((slice) => (
                    <path
                        key={`fill-${slice.data.domain}`}
                        d={slice.pathFill}
                        className="radar-slice radar-slice-fill"
                        fill={slice.meta.color}
                        onClick={() => onDomainClick(slice.data)}
                        onMouseEnter={() => setHoveredDomain(slice.data.domain)}
                        style={{ pointerEvents: 'none' }} // Let background handle events
                    />
                ))}

                {/* Stroke Separators */}
                {slices.map((slice) => (
                    <path
                        key={`stroke-${slice.data.domain}`}
                        d={slice.pathBg}
                        fill="none"
                        stroke="var(--bg-card)" // Match background to create "gap"
                        strokeWidth="2"
                        style={{ pointerEvents: 'none' }}
                    />
                ))}

                {/* Labels */}
                {slices.map((slice) => (
                    <text
                        key={`label-${slice.data.domain}`}
                        x={slice.labelPos.x}
                        y={slice.labelPos.y}
                        className="radar-label"
                        dominantBaseline="middle"
                        textAnchor={slice.labelPos.x < CENTER ? 'end' : 'start'}
                        style={{ fontWeight: 500, fontSize: '0.85rem', fill: 'var(--text-primary)' }}
                    >
                        {slice.meta.label}
                    </text>
                ))}
            </svg>

            {/* Center Info Hub */}
            <div className="radar-center-info">
                {activeMeta && activeData ? (
                    <>
                        <div className="radar-center-icon">{activeMeta.icon}</div>
                        <h4 className="radar-center-title">{activeMeta.label}</h4>
                        <div className="radar-center-stat">
                            {Math.round((activeData.answered / activeData.total) * 100)}% Complete
                        </div>
                    </>
                ) : (
                    <>
                        <div className="radar-center-icon" style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>IRMMF</div>
                        <h4 className="radar-center-title" style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>Insider Risk Management<br />Maturity Framework</h4>
                        <div className="radar-center-stat" style={{ fontSize: '0.75rem', lineHeight: '1.4', maxWidth: '200px' }}>
                            The IRMMF evaluates an organization's maturity across governance, human-centric culture, and technical controls.
                            Hover over a domain to view progress or click to manage details.
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}

export default FrameworkRadar
