import { CSSProperties } from 'react'
import './RiskHeatmap.css'

export type RiskPoint = {
    id?: string
    scenario_id?: string
    scenario?: string
    name?: string
    category?: string
    description?: string
    likelihood?: number
    impact?: number
    risk_level?: string
    risk_score?: number
    mitigation_score?: number
    key_gaps?: string[]
}

type RiskHeatmapProps = {
    risks: RiskPoint[]
    size?: number | string
    dotRadius?: number
}

export const RiskHeatmap = ({ risks, size = '100%', dotRadius = 8 }: RiskHeatmapProps) => {
    const containerStyle: CSSProperties = {
        maxWidth: typeof size === 'number' ? `${size}px` : size,
        width: '100%',
    }

    // Group risks by coordinates to handle overlap
    const grouped: Record<string, RiskPoint[]> = {}
    risks.forEach((r) => {
        const l = Math.min(7, Math.max(1, Number(r.likelihood || 1)))
        const i = Math.min(7, Math.max(1, Number(r.impact || 1)))
        const key = `${l}-${i}`
        if (!grouped[key]) grouped[key] = []
        grouped[key].push(r)
    })

    const plottablePoints = Object.entries(grouped).flatMap(([key, group]) => {
        const [l, i] = key.split('-').map(Number)
        const count = group.length

        return group.map((r, idx) => {
            const xBase = (l - 0.5) / 7
            const yBase = (i - 0.5) / 7

            let offX = 0
            let offY = 0

            if (count > 1) {
                // Circular layout for overlaps
                const angle = (idx / count) * 2 * Math.PI
                // Jitter radius in pixels roughly 
                const radius = 14
                offX = Math.cos(angle) * radius
                offY = Math.sin(angle) * radius
            }

            return {
                ...r,
                key: `${r.id || r.scenario || idx}`,
                left: `calc(${xBase * 100}% + ${offX}px)`,
                top: `calc(${(1 - yBase) * 100}% + ${offY}px)`,
                l, i, offX
            }
        })
    })

    return (
        <div className="rh-heatmap" style={containerStyle}>
            <div className="rh-axis-labels">
                <span>7</span>
                <span>6</span>
                <span>5</span>
                <span>4</span>
                <span>3</span>
                <span>2</span>
                <span>1</span>
            </div>
            <div className="rh-heatmap-grid">
                {plottablePoints.map((p) => (
                    <div
                        key={p.key}
                        className={`rh-dot level-${(p.risk_level || 'green').toLowerCase()}`}
                        style={{
                            left: p.left,
                            top: p.top,
                            width: dotRadius * 2,
                            height: dotRadius * 2,
                            zIndex: 10 + (p.offX ? 1 : 0) // Bring jittered items forward slightly
                        }}
                        title={`${p.scenario || p.name}\nCategory: ${p.category || 'General'}\nScore: L${p.l} × I${p.i}`}
                    />
                ))}
            </div>
            <div className="rh-axis-spacer" />
            <div className="rh-axis-bottom">
                <span>1</span>
                <span>2</span>
                <span>3</span>
                <span>4</span>
                <span>5</span>
                <span>6</span>
                <span>7</span>
            </div>
        </div>
    )
}
