import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, ApplicationType, DocumentTemplate, RequiredDocument } from "../api";

export default function ApplicationTypeEditorPage() {
  const { id = "" } = useParams();
  const [at, setAt] = useState<ApplicationType | null>(null);
  const [templates, setTemplates] = useState<DocumentTemplate[]>([]);
  const [reqs, setReqs] = useState<RequiredDocument[]>([]);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [list, tpls] = await Promise.all([api.listAppTypes(), api.listTemplates()]);
    const found = list.find((x) => x.id === id);
    if (!found) return;
    setAt(found);
    setReqs(found.required_documents);
    setTemplates(tpls);
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const save = async () => {
    setBusy(true);
    try {
      await api.updateAppType(id, { required_documents: reqs });
      await load();
    } finally { setBusy(false); }
  };

  const addReq = (template_id: string) => {
    if (reqs.some((r) => r.template_id === template_id)) return;
    setReqs([...reqs, { template_id, required: true, min_count: 1, max_count: 1 }]);
  };

  const updateReq = (i: number, patch: Partial<RequiredDocument>) =>
    setReqs((r) => r.map((x, idx) => (idx === i ? { ...x, ...patch } : x)));

  const removeReq = (i: number) =>
    setReqs((r) => r.filter((_, idx) => idx !== i));

  const tplName = (tid: string) => templates.find((t) => t.id === tid)?.name ?? tid;
  const tplCode = (tid: string) => templates.find((t) => t.id === tid)?.code ?? "";
  const unattached = templates.filter((t) => !reqs.some((r) => r.template_id === t.id));

  if (!at) return <div>Loading…</div>;

  return (
    <>
      <div className="topbar">
        <h2>{at.name} <span style={{ color: "#888", fontSize: 13 }}>({at.code})</span></h2>
        <button className="primary" onClick={save} disabled={busy}>Save</button>
      </div>

      <div className="card">
        <h3>Required Documents</h3>
        <table>
          <thead>
            <tr>
              <th>Template</th><th>Required</th><th>Min</th><th>Max</th><th></th>
            </tr>
          </thead>
          <tbody>
            {reqs.map((r, i) => (
              <tr key={r.template_id}>
                <td>
                  <div>{tplName(r.template_id)}</div>
                  <div style={{ color: "#888", fontSize: 11 }}>{tplCode(r.template_id)}</div>
                </td>
                <td style={{ textAlign: "center" }}>
                  <input type="checkbox" checked={r.required}
                    onChange={(e) => updateReq(i, { required: e.target.checked })}
                    style={{ width: "auto" }} />
                </td>
                <td><input type="number" min={0} value={r.min_count}
                  onChange={(e) => updateReq(i, { min_count: Number(e.target.value) })} /></td>
                <td><input type="number" min={1} value={r.max_count}
                  onChange={(e) => updateReq(i, { max_count: Number(e.target.value) })} /></td>
                <td><button onClick={() => removeReq(i)}>✕</button></td>
              </tr>
            ))}
            {reqs.length === 0 && (
              <tr><td colSpan={5} style={{ color: "#888" }}>No documents attached yet.</td></tr>
            )}
          </tbody>
        </table>

        {unattached.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <label>Add document template</label>
            <div style={{ display: "flex", gap: 8 }}>
              <select id="add-tpl" defaultValue="">
                <option value="" disabled>Select a template…</option>
                {unattached.map((t) => (
                  <option key={t.id} value={t.id}>{t.name} ({t.code})</option>
                ))}
              </select>
              <button onClick={() => {
                const el = document.getElementById("add-tpl") as HTMLSelectElement;
                if (el.value) { addReq(el.value); el.value = ""; }
              }}>+ Add</button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
