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
import InsiderRiskProgramLayout from './pages/InsiderRiskProgramLayout'
import InsiderRiskRoadmap from './pages/InsiderRiskRoadmap'
import Settings from './pages/Settings'
import Notifications from './pages/Notifications'
import Login from './pages/Login'
import Register from './pages/Register'
import NotFound from './pages/NotFound'
import CaseManagement from './pages/CaseManagement'
import ExternalInbox from './pages/ExternalInbox'
import ExternalDropbox from './pages/ExternalDropbox'
import TriageInbox from './pages/TriageInbox'
import { ToastProvider } from './context/ToastContext'

const RequireAuth = () => {
  const user = localStorage.getItem('irmmf_user')
  if (!user) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/external/inbox" element={<ExternalInbox />} />
          <Route path="/external/dropbox" element={<ExternalDropbox />} />
          <Route element={<RequireAuth />}>
            <Route path="/" element={<AppLayout />}>
              <Route index element={<CommandCenter />} />
              <Route path="assessment" element={<AssessmentHub />} />
              <Route path="assessment/intake" element={<AssessmentIntake />} />
              <Route path="assessment/flow" element={<AssessmentFlow />} />
              <Route path="assessment/results" element={<AssessmentResults />} />
              <Route path="assessment/review" element={<AssessmentReview />} />
              <Route path="assessment/risks" element={<Navigate to="/insider-risk-program/risks" replace />} />
              <Route path="insider-risk-program" element={<InsiderRiskProgramLayout />}>
                <Route index element={<Navigate to="policy" replace />} />
                <Route path="policy" element={<InsiderRiskProgram view="policy" />} />
                <Route path="controls" element={<InsiderRiskProgram view="controls" />} />
                <Route path="risks" element={<AssessmentRisks />} />
                <Route path="roadmap" element={<InsiderRiskRoadmap />} />
                <Route path="actions" element={<InsiderRiskProgram view="actions" />} />
              </Route>
              <Route path="workforce" element={<DynamicWorkforce />} />
              <Route path="case-management" element={<CaseManagement />}>
                <Route index element={<Navigate to="compliance" replace />} />
                <Route path="compliance" element={<PiaCompliance />} />
                <Route path="cases" element={<Cases />} />
                <Route path="inbox" element={<TriageInbox />} />
                <Route path="notifications" element={<Notifications />} />
              </Route>
              <Route path="pia" element={<Navigate to="/case-management/compliance" replace />} />
              <Route path="cases" element={<Navigate to="/case-management/cases" replace />} />
              <Route path="cases/:caseId/flow/:step" element={<CaseFlow />} />
              <Route path="cases/:caseId/flow" element={<CaseFlow />} />
              <Route path="notifications" element={<Navigate to="/case-management/notifications" replace />} />
              <Route path="recommendations" element={<Navigate to="/insider-risk-program/actions" replace />} />
              <Route path="settings" element={<Settings />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  )
}

export default App
