import React, { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
    children?: ReactNode
}

interface State {
    hasError: boolean
    error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null
    }

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error }
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo)
    }

    public render() {
        if (this.state.hasError) {
            return (
                <div style={{ padding: '2rem', color: '#ef4444', background: '#1a1a1a', minHeight: '100vh', fontFamily: 'monospace' }}>
                    <h1>Something went wrong.</h1>
                    <h2 style={{ fontSize: '1.2rem', marginTop: '1rem' }}>{this.state.error?.toString()}</h2>
                    <pre style={{ marginTop: '1rem', background: '#000', padding: '1rem', overflow: 'auto' }}>
                        {this.state.error?.stack}
                    </pre>
                </div>
            )
        }

        return this.props.children
    }
}
