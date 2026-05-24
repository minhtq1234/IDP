import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, Artifacts, DataType, DocumentTemplate, FieldDef } from "../api";

const TYPES: DataType[] = ["string", "number", "date", "currency", "list", "object"];

const EMPTY_FIELD: FieldDef = { name: "", data_type: "string", required: false, hint: "" };

export default function TemplateEditorPage() {
  const { id = "" } = useParams();
  const [t, setT] = useState<DocumentTemplate | null>(null);
  const [fields, setFields] = useState<FieldDef[]>([]);
  const [artifacts, setArtifacts] = useState<Artifacts | null>(null);
  const [busy, setBusy] = useState(false);
  const [sample, setSample] = useState("");
  const [view, setView] = useState<"schema" | "prompt">("schema");

  const load = useCallback(async () => {
    const x = await api.getTemplate(id);
    setT(x);
    setFields(x.fields);
  }, [id]);
  useEffect(() => { load(); }, [load]);

  const save = async () => {
    setBusy(true);
    try {
      await api.updateTemplate(id, { fields });
      const a = await api.artifacts(id);
      setArtifacts(a);
    } finally { setBusy(false); }
  };

  const previewArtifacts = async () => {
    setBusy(true);
    try {
      await api.updateTemplate(id, { fields });
      setArtifacts(await api.artifacts(id));
    } finally { setBusy(false); }
  };

  const suggest = async () => {
    if (!t) return;
    setBusy(true);
    try {
      const r = await api.suggestFields({
        document_type_name: t.name,
        description: t.description,
        sample_text: sample,
      });
      setFields(r.fields);
    } catch (e) {
      alert("LLM suggest failed — check backend logs / LLM_PROVIDER. " + (e as Error).message);
    } finally { setBusy(false); }
  };

  const setF = (i: number, patch: Partial<FieldDef>) =>
    setFields((f) => f.map((x, idx) => (idx === i ? { ...x, ...patch } : x)));

  const remove = (i: number) =>
    setFields((f) => f.filter((_, idx) => idx !== i));

  if (!t) return <div>Loading…</div>;

  return (
    <>
      <div className="topbar">
        <h2>{t.name} <span style={{ color: "#888", fontSize: 13 }}>({t.code})</span></h2>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={previewArtifacts} disabled={busy}>Preview Schema & Prompt</button>
          <button className="primary" onClick={save} disabled={busy}>Save</button>
        </div>
      </div>

      <div className="card">
        <h3>LLM Field Suggestion</h3>
        <label>Sample document text (paste OCR or excerpt)</label>
        <textarea rows={4} value={sample} onChange={(e) => setSample(e.target.value)} />
        <div style={{ marginTop: 8 }}>
          <button onClick={suggest} disabled={busy}>Suggest fields</button>
          <span style={{ marginLeft: 12, color: "#666", fontSize: 12 }}>
            Uses authoring LLM configured in backend (Gemma or GPT-5).
          </span>
        </div>
      </div>

      <div className="card">
        <h3>Fields ({fields.length})</h3>
        <table>
          <thead>
            <tr>
              <th>Name</th><th>Type</th><th>Required</th><th>Hint</th><th>Pattern</th><th></th>
            </tr>
          </thead>
          <tbody>
            {fields.map((f, i) => (
              <tr key={i}>
                <td><input value={f.name} onChange={(e) => setF(i, { name: e.target.value })} /></td>
                <td>
                  <select value={f.data_type}
                    onChange={(e) => setF(i, { data_type: e.target.value as DataType })}>
                    {TYPES.map((x) => <option key={x}>{x}</option>)}
                  </select>
                </td>
                <td style={{ textAlign: "center" }}>
                  <input type="checkbox" checked={f.required}
                    onChange={(e) => setF(i, { required: e.target.checked })}
                    style={{ width: "auto" }} />
                </td>
                <td><input value={f.hint} onChange={(e) => setF(i, { hint: e.target.value })} /></td>
                <td><input value={f.regex ?? ""}
                  onChange={(e) => setF(i, { regex: e.target.value || null })} /></td>
                <td><button onClick={() => remove(i)}>✕</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ marginTop: 12 }}>
          <button onClick={() => setFields((f) => [...f, { ...EMPTY_FIELD }])}>+ Add field</button>
        </div>
      </div>

      {artifacts && (
        <div className="card">
          <h3>Generated Artifacts</h3>
          <div style={{ marginBottom: 8, display: "flex", gap: 8 }}>
            <button className={view === "schema" ? "primary" : ""} onClick={() => setView("schema")}>
              JSON Schema
            </button>
            <button className={view === "prompt" ? "primary" : ""} onClick={() => setView("prompt")}>
              VLM Prompt
            </button>
          </div>
          {view === "schema" ? (
            <pre>{JSON.stringify(artifacts.json_schema, null, 2)}</pre>
          ) : (
            <pre>{artifacts.vlm_prompt}</pre>
          )}
        </div>
      )}
    </>
  );
}
