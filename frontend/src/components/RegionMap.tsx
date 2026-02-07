import React, { useState } from 'react'
import './RegionMap.css'

interface RegionMapProps {
    selectedRegion: string
    onSelect: (region: string) => void
}

const regions = [
    { id: 'BE', name: 'Belgium', cx: 400, cy: 300, r: 25 },
    { id: 'NL', name: 'Netherlands', cx: 430, cy: 260, r: 20 },
    { id: 'LU', name: 'Luxembourg', cx: 415, cy: 335, r: 10 },
    { id: 'IE', name: 'Ireland', cx: 280, cy: 230, r: 20 },
    { id: 'UK', name: 'United Kingdom', cx: 330, cy: 250, r: 35 },
    { id: 'EU', name: 'Rest of EU', cx: 480, cy: 350, r: 40 },
    { id: 'US', name: 'United States', cx: 150, cy: 250, r: 50 },
    { id: 'ROW', name: 'Rest of World', cx: 650, cy: 250, r: 60 },
]

export const RegionMap: React.FC<RegionMapProps> = ({ selectedRegion, onSelect }) => {
    const [hovered, setHovered] = useState<string | null>(null)

    return (
        <div className="region-map-container">
            <svg viewBox="0 0 800 500" className="region-map-svg">
                <defs>
                    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur stdDeviation="3" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                </defs>

                {/* Connection Lines (Abstract) */}
                <path d="M150,250 Q240,150 330,250" className="map-link" />
                <path d="M330,250 L400,300" className="map-link" />
                <path d="M400,300 L430,260" className="map-link" />
                <path d="M400,300 L415,335" className="map-link" />

                {regions.map((region) => {
                    const isSelected = selectedRegion === region.id || (selectedRegion === 'Standard' && region.id === 'EU')
                    const isHovered = hovered === region.id

                    return (
                        <g
                            key={region.id}
                            onClick={() => onSelect(region.id)}
                            onMouseEnter={() => setHovered(region.id)}
                            onMouseLeave={() => setHovered(null)}
                            className="region-node"
                            style={{ cursor: 'pointer' }}
                        >
                            <circle
                                cx={region.cx}
                                cy={region.cy}
                                r={region.r + (isSelected ? 5 : 0)}
                                fill={isSelected ? 'var(--primary)' : 'var(--bg-card)'}
                                stroke={isSelected ? 'var(--primary-light)' : 'var(--border-subtle)'}
                                strokeWidth={isHovered ? 3 : 2}
                                className="region-circle"
                            />
                            <text
                                x={region.cx}
                                y={region.cy + region.r + 20}
                                textAnchor="middle"
                                fill="var(--text-main)"
                                fontSize="12"
                                fontWeight={isSelected ? 'bold' : 'normal'}
                            >
                                {region.name}
                            </text>
                        </g>
                    )
                })}
            </svg>
        </div>
    )
}
