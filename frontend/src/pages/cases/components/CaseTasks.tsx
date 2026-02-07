import React, { useState } from 'react'
import { useCase } from '../context/CaseContext'
import { useCaseActions } from '../hooks/useCaseActions'
import { RECOMMENDED_TASKS, TASK_STATUS_OPTIONS } from '../constants'

export const CaseTasks: React.FC = () => {
    const { caseData } = useCase()
    const { createTask, updateTaskStatus } = useCaseActions()

    const [taskDraft, setTaskDraft] = useState({ title: '', assignee: '' })
    const [status, setStatus] = useState('')

    const handleAddTask = async () => {
        if (!taskDraft.title.trim()) {
            setStatus('Task title required.')
            return
        }
        setStatus('Adding task...')
        const res = await createTask(taskDraft.title, taskDraft.assignee)
        if (res.success) {
            setTaskDraft({ title: '', assignee: '' })
            setStatus('Task added.')
        } else {
            setStatus(res.message || 'Error adding task.')
        }
    }

    const handleCreateRecommended = async (title: string) => {
        setStatus(`Adding ${title}...`)
        const res = await createTask(title)
        if (res.success) {
            setStatus('Task added.')
        } else {
            setStatus(res.message || 'Error adding task.')
        }
    }

    const handleAddAllRecommended = async () => {
        setStatus('Adding all recommended tasks...')
        for (const title of RECOMMENDED_TASKS) {
            await createTask(title)
        }
        setStatus('All tasks added.')
    }

    const handleUpdateStatus = async (taskId: number, newStatus: string) => {
        await updateTaskStatus(taskId, newStatus)
    }

    if (!caseData) return null
    const isAnonymized = caseData.is_anonymized

    const taskTotal = caseData.tasks.length
    const taskCompleted = caseData.tasks.filter(t => t.status === 'Completed').length
    const taskProgress = taskTotal === 0 ? 0 : Math.round((taskCompleted / taskTotal) * 100)

    return (
        <div className="case-flow-card">
            <h3>Tasks & Checklist</h3>
            <p className="case-flow-help">Track each investigative action and assignment.</p>

            <div className="case-flow-progress">
                <div className="case-flow-progress-bar" style={{ width: `${taskProgress}%` }} />
            </div>
            <div className="case-flow-muted">
                {taskTotal === 0 ? 'No tasks yet.' : `${taskCompleted} of ${taskTotal} tasks completed`}
            </div>

            {status && <div className="case-flow-status">{status}</div>}

            <label className="case-flow-label">
                Task
                <input
                    type="text"
                    value={taskDraft.title}
                    onChange={(e) => setTaskDraft({ ...taskDraft, title: e.target.value })}
                    disabled={isAnonymized}
                />
            </label>

            <label className="case-flow-label">
                Assignee
                <input
                    type="text"
                    value={taskDraft.assignee}
                    onChange={(e) => setTaskDraft({ ...taskDraft, assignee: e.target.value })}
                    disabled={isAnonymized}
                />
            </label>

            <button className="case-flow-btn outline" onClick={handleAddTask} disabled={isAnonymized}>
                Add task
            </button>

            {caseData.tasks.length === 0 ? (
                <div className="case-flow-muted">No tasks added.</div>
            ) : (
                caseData.tasks.map((task) => (
                    <div key={task.task_id} className="case-flow-row">
                        <div>
                            <strong>{task.title}</strong>
                            <div className="case-flow-muted">
                                {task.assignee || 'Unassigned'}
                                {task.due_at ? ` · due ${new Date(task.due_at).toLocaleDateString()}` : ''}
                            </div>
                        </div>
                        <div className="case-flow-inline">
                            {task.task_type === 'retaliation_check' && (
                                <span className="case-flow-tag">Retaliation</span>
                            )}
                            <select
                                className="case-flow-select"
                                value={task.status}
                                onChange={(e) => handleUpdateStatus(task.task_id, e.target.value)}
                                disabled={isAnonymized}
                            >
                                {TASK_STATUS_OPTIONS.map((option) => (
                                    <option key={`${task.task_id}-${option}`} value={option}>
                                        {option}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                ))
            )}

            <div className="case-flow-divider" />
            <h4 className="case-flow-subtitle">Recommended tasks</h4>
            <div className="case-flow-muted">Add best-practice actions (you can still customize).</div>
            <div className="case-flow-inline">
                {RECOMMENDED_TASKS.map((task) => (
                    <button
                        key={task}
                        className="case-flow-btn outline"
                        onClick={() => handleCreateRecommended(task)}
                        disabled={isAnonymized}
                    >
                        Add: {task}
                    </button>
                ))}
            </div>
            <button className="case-flow-btn outline" onClick={handleAddAllRecommended} disabled={isAnonymized}>
                Add all recommended
            </button>
        </div>
    )
}
