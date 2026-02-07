
export interface Template {
    id: string
    title: string
    description: string
    type: 'playbook' | 'policy' | 'training' | 'other'
    format: string
    version: string
    author: string
    content?: string
}

export interface TemplateFilter {
    type: string
    search: string
}
