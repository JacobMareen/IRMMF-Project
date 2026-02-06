import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { apiFetch } from '../lib/api'
import './Register.css'

const Register = () => {
    const [formData, setFormData] = useState({
        company_name: '',
        admin_name: '',
        admin_email: '',
        industry_sector: '',
        employee_count: '',
        admin_job_title: '',
        admin_phone_number: '',
        admin_linkedin_url: '',
        marketing_consent: false,
        utm_campaign: '',
        utm_source: '',
        utm_medium: '',
    })
    const [searchParams] = useSearchParams()
    const [status, setStatus] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [emailWarning, setEmailWarning] = useState<string | null>(null)
    const [successData, setSuccessData] = useState<{ tenant_key: string; login_url: string } | null>(
        null
    )

    useEffect(() => {
        const campaign =
            searchParams.get('utm_campaign') ||
            searchParams.get('campaign') ||
            localStorage.getItem('irmmf_utm_campaign') ||
            ''
        const source =
            searchParams.get('utm_source') ||
            searchParams.get('source') ||
            localStorage.getItem('irmmf_utm_source') ||
            ''
        const medium =
            searchParams.get('utm_medium') ||
            searchParams.get('medium') ||
            localStorage.getItem('irmmf_utm_medium') ||
            ''
        if (!campaign && !source && !medium) return
        setFormData((prev) => ({
            ...prev,
            utm_campaign: prev.utm_campaign || campaign,
            utm_source: prev.utm_source || source,
            utm_medium: prev.utm_medium || medium,
        }))
    }, [searchParams])

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target
        setFormData((prev) => ({ ...prev, [name]: value }))
    }

    const blockedEmailDomains = [
        'gmail.com',
        'yahoo.com',
        'hotmail.com',
        'outlook.com',
        'icloud.com',
        'proton.me',
        'protonmail.com',
    ]

    const checkEmailDomain = (email: string) => {
        const trimmed = email.trim().toLowerCase()
        const domain = trimmed.split('@')[1] || ''
        if (domain && blockedEmailDomains.includes(domain)) {
            return 'Please use a company email address.'
        }
        return null
    }

    const handleSubmit = async () => {
        if (!formData.company_name || !formData.admin_name || !formData.admin_email) {
            setError('Company name, admin name, and work email are required.')
            return
        }
        if (!formData.industry_sector || !formData.employee_count) {
            setError('Industry sector and employee count are required.')
            return
        }
        const emailCheck = checkEmailDomain(formData.admin_email)
        if (emailCheck) {
            setError(emailCheck)
            return
        }

        const payload = {
            company_name: formData.company_name.trim(),
            admin_name: formData.admin_name.trim(),
            admin_email: formData.admin_email.trim(),
            industry_sector: formData.industry_sector.trim(),
            employee_count: formData.employee_count.trim(),
            admin_job_title: formData.admin_job_title.trim() || null,
            admin_phone_number: formData.admin_phone_number.trim() || null,
            admin_linkedin_url: formData.admin_linkedin_url.trim() || null,
            marketing_consent: Boolean(formData.marketing_consent),
            utm_campaign: formData.utm_campaign.trim() || null,
            utm_source: formData.utm_source.trim() || null,
            utm_medium: formData.utm_medium.trim() || null,
        }

        setStatus('Registering...')
        setError(null)

        try {
            const resp = await apiFetch('/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
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
            localStorage.removeItem('irmmf_utm_campaign')
            localStorage.removeItem('irmmf_utm_source')
            localStorage.removeItem('irmmf_utm_medium')
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
                            onChange={(event) => {
                                handleChange(event)
                                setEmailWarning(checkEmailDomain(event.target.value))
                            }}
                        />
                    </label>
                    {emailWarning ? <div className="status-message">{emailWarning}</div> : null}
                    <label>
                        Industry Sector
                        <select
                            name="industry_sector"
                            value={formData.industry_sector}
                            onChange={(event) =>
                                setFormData((prev) => ({ ...prev, industry_sector: event.target.value }))
                            }
                        >
                            <option value="">Select industry</option>
                            <option value="Financial Services">Financial Services</option>
                            <option value="Healthcare">Healthcare</option>
                            <option value="Manufacturing">Manufacturing</option>
                            <option value="Technology">Technology</option>
                            <option value="Retail">Retail</option>
                            <option value="Energy">Energy</option>
                            <option value="Government">Government</option>
                            <option value="Education">Education</option>
                            <option value="Other">Other</option>
                        </select>
                    </label>
                    <label>
                        Employee Count
                        <select
                            name="employee_count"
                            value={formData.employee_count}
                            onChange={(event) =>
                                setFormData((prev) => ({ ...prev, employee_count: event.target.value }))
                            }
                        >
                            <option value="">Select size</option>
                            <option value="1-50">1-50</option>
                            <option value="51-200">51-200</option>
                            <option value="201-1000">201-1000</option>
                            <option value="1001-5000">1001-5000</option>
                            <option value="5001-10000">5001-10000</option>
                            <option value="10000+">10000+</option>
                        </select>
                    </label>
                    <label>
                        Job Title (optional)
                        <input
                            type="text"
                            name="admin_job_title"
                            placeholder="CISO, Security Lead, HR Director"
                            value={formData.admin_job_title}
                            onChange={handleChange}
                        />
                    </label>
                    <label>
                        Phone Number (optional)
                        <input
                            type="tel"
                            name="admin_phone_number"
                            placeholder="+1 555 555 5555"
                            value={formData.admin_phone_number}
                            onChange={handleChange}
                        />
                    </label>
                    <label>
                        LinkedIn URL (optional)
                        <input
                            type="url"
                            name="admin_linkedin_url"
                            placeholder="https://www.linkedin.com/in/username"
                            value={formData.admin_linkedin_url}
                            onChange={handleChange}
                        />
                    </label>
                    <label className="register-consent">
                        <input
                            type="checkbox"
                            name="marketing_consent"
                            checked={Boolean(formData.marketing_consent)}
                            onChange={(event) =>
                                setFormData((prev) => ({ ...prev, marketing_consent: event.target.checked }))
                            }
                        />
                        I agree to receive product updates and marketing communications from IRMMF.
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
