import { useState, useEffect } from 'react'
import { client as apiClient } from '../api/client'
import './TermsOfServiceModal.css'

interface TermsStatus {
    latest_version: string
    has_accepted: boolean
    accepted_at: string | null
    required: boolean
}

const TermsOfServiceModal = () => {
    const [loading, setLoading] = useState(true)
    const [show, setShow] = useState(false)
    const [status, setStatus] = useState<TermsStatus | null>(null)
    const [accepting, setAccepting] = useState(false)

    useEffect(() => {
        fetchStatus()
    }, [])

    const fetchStatus = async () => {
        try {
            const data = await apiClient.get<TermsStatus>('/auth/terms/status')
            setStatus(data)
            if (data.required && !data.has_accepted) {
                setShow(true)
            }
        } catch (error) {
            console.error('Failed to check terms status:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleAccept = async () => {
        if (!status) return
        setAccepting(true)
        try {
            await apiClient.post('/auth/terms/accept', { version: status.latest_version })
            setShow(false)
        } catch (error) {
            console.error('Failed to accept terms:', error)
            alert('Failed to accept terms. Please try again.')
        } finally {
            setAccepting(false)
        }
    }

    if (loading || !show) return null

    return (
        <div className="terms-modal-overlay">
            <div className="terms-modal-content">
                <h2>Terms of Service Update</h2>
                <div className="terms-body">
                    <p>Please review and accept our latest Terms of Service to continue using the platform.</p>
                    <div className="terms-scroll-area">
                        <h3>1. Introduction</h3>
                        <p>Welcome to IRMMF Command Center. By accessing our services, you agree to these terms.</p>
                        <h3>2. Licensing</h3>
                        <p>Your license determines your access level and usage limits.</p>
                        <h3>3. Data Privacy</h3>
                        <p>We process your data in accordance with GDPR and other applicable regulations.</p>
                        <p><em>(This is a placeholder for the full legal text)</em></p>
                    </div>
                </div>
                <div className="terms-actions">
                    <button
                        className="btn btn-primary"
                        onClick={handleAccept}
                        disabled={accepting}
                    >
                        {accepting ? 'Accepting...' : `I Accept (Version ${status?.latest_version})`}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default TermsOfServiceModal
