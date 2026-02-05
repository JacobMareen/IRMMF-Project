import { useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../lib/api'
import './Register.css'

const Register = () => {
    const [formData, setFormData] = useState({
        company_name: '',
        admin_name: '',
        admin_email: '',
    })
    const [status, setStatus] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [successData, setSuccessData] = useState<{ tenant_key: string; login_url: string } | null>(
        null
    )

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target
        setFormData((prev) => ({ ...prev, [name]: value }))
    }

    const handleSubmit = async () => {
        if (!formData.company_name || !formData.admin_name || !formData.admin_email) {
            setError('All fields are required.')
            return
        }

        setStatus('Registering...')
        setError(null)

        try {
            const resp = await apiFetch('/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            })

            if (!resp.ok) {
                const err = await resp.json()
                setError(err.detail || 'Registration failed.')
                setStatus(null)
                return
            }

            const data = await resp.json()
            setSuccessData({
                tenant_key: data.tenant_key,
                login_url: data.login_url || `/login?tenant=${data.tenant_key}`,
            })
            setStatus('Registration successful!')
        } catch (err) {
            console.error(err)
            setError('Network error. Please try again.')
            setStatus(null)
        }
    }

    if (successData) {
        return (
            <section className="register-page">
                <div className="register-card success-card">
                    <div className="register-header">
                        <h1>🎉 Welcome Aboard!</h1>
                        <p>Your workspace has been provisioned successfully.</p>
                    </div>
                    <div className="success-details">
                        <p>
                            <strong>Company:</strong> {formData.company_name}
                        </p>
                        <p>
                            <strong>Tenant Key:</strong> <code className="tenant-key">{successData.tenant_key}</code>
                        </p>
                        <p className="note">
                            Please save your Tenant Key. You will need it to log in.
                        </p>
                    </div>
                    <div className="register-actions">
                        <Link to={`/login?tenant=${successData.tenant_key}&email=${formData.admin_email}`} className="btn-primary">
                            Proceed to Login
                        </Link>
                    </div>
                </div>
            </section>
        )
    }

    return (
        <section className="register-page">
            <div className="register-card">
                <div className="register-header">
                    <h1>Create Workspace</h1>
                    <p>Get started with IRMMF today.</p>
                </div>
                <div className="register-form">
                    <label>
                        Company Name
                        <input
                            type="text"
                            name="company_name"
                            placeholder="Acme Corp"
                            value={formData.company_name}
                            onChange={handleChange}
                        />
                    </label>
                    <label>
                        Admin Full Name
                        <input
                            type="text"
                            name="admin_name"
                            placeholder="Jane Doe"
                            value={formData.admin_name}
                            onChange={handleChange}
                        />
                    </label>
                    <label>
                        Work Email
                        <input
                            type="email"
                            name="admin_email"
                            placeholder="jane@acme.com"
                            value={formData.admin_email}
                            onChange={handleChange}
                        />
                    </label>

                    {error && <div className="error-message">{error}</div>}
                    {status && !successData && <div className="status-message">{status}</div>}

                    <button className="register-btn" onClick={handleSubmit} disabled={status === 'Registering...'}>
                        {status === 'Registering...' ? 'Provisioning...' : 'Create Account'}
                    </button>

                    <div className="login-link">
                        Already have an account? <Link to="/login">Sign In</Link>
                    </div>
                </div>
            </div>
        </section>
    )
}

export default Register
