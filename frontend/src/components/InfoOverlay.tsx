import { useState, useRef, useEffect } from 'react'
import './InfoOverlay.css'

type InfoOverlayProps = {
    title: string
    children: React.ReactNode
    position?: 'top' | 'bottom' | 'left' | 'right'
}

export const InfoOverlay = ({ title, children, position = 'top' }: InfoOverlayProps) => {
    const [isOpen, setIsOpen] = useState(false)
    const containerRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false)
            }
        }

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside)
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside)
        }
    }, [isOpen])

    return (
        <div className="io-container" ref={containerRef}>
            <button
                className={`io-trigger ${isOpen ? 'active' : ''}`}
                onClick={() => setIsOpen(!isOpen)}
                aria-label={`More info about ${title}`}
                title={title} // Fallback for accessibility
            >
                ⓘ
            </button>

            {isOpen && (
                <div className={`io-popup io-position-${position}`}>
                    <div className="io-header">
                        <span className="io-title">{title}</span>
                        <button className="io-close" onClick={() => setIsOpen(false)}>×</button>
                    </div>
                    <div className="io-content">
                        {children}
                    </div>
                </div>
            )}
        </div>
    )
}
