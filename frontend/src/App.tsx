import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import ApplicationTypesPage from "./pages/ApplicationTypes";
import DocumentTemplatesPage from "./pages/DocumentTemplates";
import TemplateEditorPage from "./pages/TemplateEditor";

export default function App() {
  return (
    <div className="shell">
      <nav className="sidebar">
        <h1>GREENNODE IDP</h1>
        <NavLink to="/application-types">◈ Application Types</NavLink>
        <NavLink to="/templates">◧ Document Templates</NavLink>
      </nav>
      <main className="main">
        <Routes>
          <Route path="/" element={<Navigate to="/application-types" replace />} />
          <Route path="/application-types" element={<ApplicationTypesPage />} />
          <Route path="/templates" element={<DocumentTemplatesPage />} />
          <Route path="/templates/:id" element={<TemplateEditorPage />} />
        </Routes>
      </main>
    </div>
  );
}
