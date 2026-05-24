import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, DocumentTemplate } from "../api";

export default function DocumentTemplatesPage() {
  const [rows, setRows] = useState<DocumentTemplate[]>([]);
  const [showNew, setShowNew] = useState(false);
  const [draft, setDraft] = useState({ code: "", name: "", description: "" });

  const load = () => api.listTemplates().then(setRows).catch(console.error);
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!draft.code || !draft.name) return;
    const t = await api.createTemplate({
      ...draft,
      file_formats: ["pdf", "jpg", "png"],
      active: true,
      fields: [],
    });
    setDraft({ code: "", name: "", description: "" });
    setShowNew(false);
    load();
    window.location.assign(`/templates/${t.id}`);
  };

  return (
    <>
      <div className="topbar">
        <h2>Document Templates</h2>
        <button className="primary" onClick={() => setShowNew((v) => !v)}>+ New</button>
      </div>

      {showNew && (
        <div className="card">
          <h3>New Document Template</h3>
          <div className="row">
            <div><label>Code</label><input value={draft.code}
              onChange={(e) => setDraft({ ...draft, code: e.target.value })} /></div>
            <div><label>Name</label><input value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })} /></div>
          </div>
          <div className="row">
            <div><label>Description</label><input value={draft.description}
              onChange={(e) => setDraft({ ...draft, description: e.target.value })} /></div>
          </div>
          <div style={{ marginTop: 12 }}>
            <button className="primary" onClick={create}>Create & Edit Fields</button>
          </div>
        </div>
      )}

      <div className="card">
        <table>
          <thead>
            <tr><th>Code</th><th>Name</th><th>Fields</th><th>Status</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td><Link to={`/templates/${r.id}`}>{r.code}</Link></td>
                <td>{r.name}</td>
                <td>{r.fields.length}</td>
                <td><span className={"badge " + (r.active ? "" : "inactive")}>
                  {r.active ? "Active" : "Inactive"}</span></td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan={4} style={{ color: "#888" }}>No templates yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
