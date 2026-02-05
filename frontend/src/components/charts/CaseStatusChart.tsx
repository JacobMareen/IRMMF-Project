import { Doughnut } from 'react-chartjs-2'
import type { ChartData, ChartOptions } from 'chart.js'

type CaseStatusChartProps = {
    open: number
    closed: number
    onHold: number
}

export const CaseStatusChart = ({ open, closed, onHold }: CaseStatusChartProps) => {
    const data: ChartData<'doughnut'> = {
        labels: ['Open', 'Closed', 'On Hold'],
        datasets: [
            {
                data: [open, closed, onHold],
                backgroundColor: [
                    '#d4af37', // Brand Gold
                    '#10b981', // Success Green
                    '#6b7280', // Muted Grey
                ],
                borderColor: '#1f2937', // Dark border matching card bg
                borderWidth: 2,
                hoverOffset: 4,
            },
        ],
    }

    const options: ChartOptions<'doughnut'> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'right',
                labels: {
                    color: '#9ca3af',
                    font: {
                        family: "'Montserrat', sans-serif",
                        size: 12,
                    },
                    usePointStyle: true,
                },
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: '#d4af37',
                bodyColor: '#fff',
                borderColor: '#374151',
                borderWidth: 1,
                padding: 10,
            },
        },
        cutout: '70%',
    }

    return (
        <div style={{ height: '200px', width: '100%' }}>
            <Doughnut data={data} options={options} />
        </div>
    )
}
