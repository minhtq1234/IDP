import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApplicationType } from "../api";

export default function ApplicationTypesPage() {
  const [rows, setRows] = useState<ApplicationType[]>([]);
  const [showNew, setShowNew] = useState(false);
  const [draft, setDraft] = useState({ code: "", name: "", description: "" });

  const load = () => api.listAppTypes().then(setRows).catch(console.error);
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!draft.code || !draft.name) return;
    await api.createAppType({ ...draft, active: true, required_documents: [] });
    setDraft({ code: "", name: "", description: "" });
    setShowNew(false);
    load();
  };

  return (
    <>
      <div className="topbar">
        <h2>Application Types</h2>
        <button className="primary" onClick={() => setShowNew((v) => !v)}>+ New</button>
      </div>

      {showNew && (
        <div className="card">
          <h3>New Application Type</h3>
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
            <button className="primary" onClick={create}>Create</button>
          </div>
        </div>
      )}

      <div className="card">
        <table>
          <thead>
            <tr><th>Code</th><th>Name</th><th>Documents</th><th>Status</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td><Link to={`/application-types/${r.id}`}>{r.code}</Link></td>
                <td>{r.name}</td>
                <td>{r.required_documents.length}</td>
                <td>
                  <span className={"badge " + (r.active ? "" : "inactive")}>
                    {r.active ? "Active" : "Inactive"}
                  </span>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan={4} style={{ color: "#888" }}>No application types yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
