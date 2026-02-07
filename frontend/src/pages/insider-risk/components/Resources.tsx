
import React, { useState, useEffect, useMemo } from 'react'
import { apiFetch } from '../../../lib/api'
import type { Template, TemplateFilter } from '../../../types/resources'

const Resources: React.FC = () => {
    const [templates, setTemplates] = useState<Template[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [filter, setFilter] = useState<TemplateFilter>({ type: '', search: '' })

    useEffect(() => {
        const loadTemplates = async () => {
            try {
                const response = await apiFetch('/content/templates')
                if (!response.ok) throw new Error('Failed to load templates')
                const data = await response.json()
                setTemplates(data)
            } catch (err) {
                setError('Unable to load resources. Please try again later.')
            } finally {
                setLoading(false)
            }
        }
        loadTemplates()
    }, [])

    const filteredTemplates = useMemo(() => {
        return templates.filter(t => {
            if (filter.type && t.type !== filter.type) return false
            if (filter.search && !t.title.toLowerCase().includes(filter.search.toLowerCase())) return false
            return true
        })
    }, [templates, filter])

    const downloadTemplate = async (templateId: string, title: string) => {
        try {
            const response = await apiFetch(`/content/templates/${templateId}`)
            if (!response.ok) throw new Error('Download failed')
            const data = await response.json()

            // Create blob and download
            const blob = new Blob([data.content], { type: 'text/markdown' })
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `${title.replace(/\s+/g, '_')}.md`
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
        } catch {
            alert('Failed to download template.')
        }
    }

    return (
        <section className="irp-section">
            <div className="irp-section-header">
                <div>
                    <h2>Resource Library</h2>
                    <p>Standardized templates, playbooks, and training materials.</p>
                </div>
            </div>

            <div className="filters">
                <div className="filter-row">
                    <div className="filter-group">
                        <label>Type</label>
                        <select
                            value={filter.type}
                            onChange={(e) => setFilter({ ...filter, type: e.target.value })}
                        >
                            <option value="">All Types</option>
                            <option value="playbook">Playbooks</option>
                            <option value="policy">Policies</option>
                            <option value="training">Training</option>
                        </select>
                    </div>
                    <div className="filter-group">
                        <label>Search</label>
                        <input
                            type="text"
                            placeholder="Search resources..."
                            className="form-input"
                            value={filter.search}
                            onChange={(e) => setFilter({ ...filter, search: e.target.value })}
                            style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-input)', color: 'var(--text-main)' }}
                        />
                    </div>
                </div>
            </div>

            {loading ? (
                <div className="rec-loading"><div className="spinner" /><p>Loading resources...</p></div>
            ) : error ? (
                <div className="empty-state"><p>{error}</p></div>
            ) : filteredTemplates.length === 0 ? (
                <div className="empty-state">
                    <h3>No Resources Found</h3>
                    <p>Try adjusting your filters.</p>
                </div>
            ) : (
                <div className="irp-policy-grid">
                    {filteredTemplates.map(template => (
                        <div key={template.id} className="irp-card">
                            <div className="irp-card-title">{template.title}</div>
                            <p className="irp-muted" style={{ minHeight: '3em' }}>{template.description}</p>
                            <div className="irp-meta">
                                <span className="badge">{template.type}</span>
                                <span className="badge">v{template.version}</span>
                                <span className="badge">{template.format.toUpperCase()}</span>
                            </div>
                            <div style={{ marginTop: '16px' }}>
                                <button className="btn btn-primary btn-sm" onClick={() => downloadTemplate(template.id, template.title)}>
                                    Download Template
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </section>
    )
}

export default Resources
