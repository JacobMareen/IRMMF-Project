import {
    Chart as ChartJS,
    ArcElement,
    Tooltip,
    Legend,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    PointElement,
    LineElement,
    RadialLinearScale,
    BarController,
    DoughnutController,
} from 'chart.js'

export const registerCharts = () => {
    ChartJS.register(
        ArcElement,
        Tooltip,
        Legend,
        CategoryScale,
        LinearScale,
        BarElement,
        Title,
        PointElement,
        LineElement,
        RadialLinearScale,
        BarController,
        DoughnutController
    )
}
