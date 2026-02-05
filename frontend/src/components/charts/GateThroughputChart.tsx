import { Bar } from 'react-chartjs-2'
import type { ChartData, ChartOptions } from 'chart.js'

type GateThroughputChartProps = {
    legitimacy: number
    credentialing: number
    adversarial: number
}

export const GateThroughputChart = ({
    legitimacy,
    credentialing,
    adversarial,
}: GateThroughputChartProps) => {
    const data: ChartData<'bar'> = {
        labels: ['Legitimacy', 'Credentialing', 'Adversarial'],
        datasets: [
            {
                label: 'Completion Rate (%)',
                data: [legitimacy, credentialing, adversarial],
                backgroundColor: [
                    'rgba(59, 130, 246, 0.7)', // Blue
                    'rgba(139, 92, 246, 0.7)', // Purple
                    'rgba(239, 68, 68, 0.7)',  // Red
                ],
                borderColor: [
                    '#3b82f6',
                    '#8b5cf6',
                    '#ef4444',
                ],
                borderWidth: 1,
                borderRadius: 4,
            },
        ],
    }

    const options: ChartOptions<'bar'> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                callbacks: {
                    label: (item) => `${item.formattedValue}%`,
                },
            },
        },
        scales: {
            y: {
                beginAtZero: true,
                max: 100,
                grid: {
                    color: 'rgba(255, 255, 255, 0.05)',
                },
                ticks: {
                    color: '#9ca3af',
                    font: { size: 10 },
                },
            },
            x: {
                grid: {
                    display: false,
                },
                ticks: {
                    color: '#9ca3af',
                    font: { size: 11, family: "'Montserrat', sans-serif" },
                },
            },
        },
    }

    return (
        <div style={{ height: '200px', width: '100%' }}>
            <Bar data={data} options={options} />
        </div>
    )
}
