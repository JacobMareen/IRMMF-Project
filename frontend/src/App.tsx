import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import AppLayout from './layout/AppLayout'
import CommandCenter from './pages/CommandCenter'
import AssessmentHub from './pages/AssessmentHub'
import AssessmentIntake from './pages/AssessmentIntake'
import AssessmentFlow from './pages/AssessmentFlow'
import AssessmentResults from './pages/AssessmentResults'
import AssessmentReview from './pages/AssessmentReview'
import AssessmentRisks from './pages/AssessmentRisks'
import DynamicWorkforce from './pages/DynamicWorkforce'
import PiaCompliance from './pages/PiaCompliance'
import Cases from './pages/Cases'
import CaseFlow from './pages/CaseFlow'
import InsiderRiskProgram from './pages/InsiderRiskProgram'
import Settings from './pages/Settings'
import Notifications from './pages/Notifications'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import CaseManagement from './pages/CaseManagement'

const RequireAuth = () => {
  const user = localStorage.getItem('irmmf_user')
  if (!user) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<RequireAuth />}>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<CommandCenter />} />
            <Route path="assessment" element={<AssessmentHub />} />
            <Route path="assessment/intake" element={<AssessmentIntake />} />
            <Route path="assessment/flow" element={<AssessmentFlow />} />
            <Route path="assessment/results" element={<AssessmentResults />} />
            <Route path="assessment/review" element={<AssessmentReview />} />
            <Route path="assessment/risks" element={<AssessmentRisks />} />
            <Route path="insider-risk-program" element={<InsiderRiskProgram />} />
            <Route path="workforce" element={<DynamicWorkforce />} />
            <Route path="case-management" element={<CaseManagement />}>
              <Route index element={<Navigate to="compliance" replace />} />
              <Route path="compliance" element={<PiaCompliance />} />
              <Route path="cases" element={<Cases />} />
              <Route path="notifications" element={<Notifications />} />
            </Route>
            <Route path="pia" element={<Navigate to="/case-management/compliance" replace />} />
            <Route path="cases" element={<Navigate to="/case-management/cases" replace />} />
            <Route path="cases/:caseId/flow/:step" element={<CaseFlow />} />
            <Route path="cases/:caseId/flow" element={<CaseFlow />} />
            <Route path="notifications" element={<Navigate to="/case-management/notifications" replace />} />
            <Route path="recommendations" element={<Navigate to="/insider-risk-program" replace />} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
