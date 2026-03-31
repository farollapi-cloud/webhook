import { Navigate, Route, Routes } from "react-router-dom"

import { Layout } from "@/components/Layout"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import CompaniesPage from "@/pages/CompaniesPage"
import CompanyDetailPage from "@/pages/CompanyDetailPage"
import CompanyNewPage from "@/pages/CompanyNewPage"
import LoginPage from "@/pages/LoginPage"

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route index element={<CompaniesPage />} />
          <Route path="companies/new" element={<CompanyNewPage />} />
          <Route path="companies/:id" element={<CompanyDetailPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
