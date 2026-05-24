import { Fragment, useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, Artifacts, DataType, DocumentTemplate, FieldDef } from "../api";

const TYPES: DataType[] = ["string", "number", "date", "currency", "list", "object"];

const newField = (): FieldDef => ({
  name: "", data_type: "string", required: false, hint: "",
});

function FieldRows({
  fields, onChange, depth = 0,
}: {
  fields: FieldDef[];
  onChange: (next: FieldDef[]) => void;
  depth?: number;
}) {
  const set = (i: number, patch: Partial<FieldDef>) =>
    onChange(fields.map((x, idx) => (idx === i ? { ...x, ...patch } : x)));
  const remove = (i: number) => onChange(fields.filter((_, idx) => idx !== i));

  return (
    <table style={depth > 0 ? { background: "#fafbfa" } : undefined}>
      {depth === 0 && (
        <thead>
          <tr>
            <th>Name</th><th>Type</th><th>Required</th>
            <th>Hint</th><th>Pattern</th><th></th>
          </tr>
        </thead>
      )}
      <tbody>
        {fields.map((f, i) => {
          const nested = f.data_type === "list" || f.data_type === "object";
          return (
            <Fragment key={i}>
              <tr>
                <td style={{ paddingLeft: 8 + depth * 16 }}>
                  <input value={f.name} onChange={(e) => set(i, { name: e.target.value })} />
                </td>
                <td>
                  <select value={f.data_type}
                    onChange={(e) => {
                      const dt = e.target.value as DataType;
                      const isNested = dt === "list" || dt === "object";
                      set(i, {
                        data_type: dt,
                        children: isNested ? (f.children ?? []) : null,
                      });
                    }}>
                    {TYPES.map((x) => <option key={x}>{x}</option>)}
                  </select>
                </td>
                <td style={{ textAlign: "center" }}>
                  <input type="checkbox" checked={f.required}
                    onChange={(e) => set(i, { required: e.target.checked })}
                    style={{ width: "auto" }} />
                </td>
                <td><input value={f.hint}
                  onChange={(e) => set(i, { hint: e.target.value })} /></td>
                <td><input value={f.regex ?? ""}
                  onChange={(e) => set(i, { regex: e.target.value || null })} /></td>
                <td><button onClick={() => remove(i)}>✕</button></td>
              </tr>
              {nested && (
                <tr>
                  <td colSpan={6} style={{ paddingLeft: 8 + (depth + 1) * 16, background: "#fafbfa" }}>
                    <div style={{ fontSize: 11, color: "#666", margin: "4px 0" }}>
                      {f.data_type === "list" ? "Item shape" : "Properties"}:
                    </div>
                    <FieldRows
                      fields={f.children ?? []}
                      onChange={(next) => set(i, { children: next })}
                      depth={depth + 1}
                    />
                    <button style={{ marginTop: 6 }}
                      onClick={() => set(i, { children: [...(f.children ?? []), newField()] })}>
                      + Add child
                    </button>
                  </td>
                </tr>
              )}
            </Fragment>
          );
        })}
      </tbody>
    </table>
  );
}

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
      setArtifacts(await api.artifacts(id));
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
        <FieldRows fields={fields} onChange={setFields} />
        <div style={{ marginTop: 12 }}>
          <button onClick={() => setFields([...fields, newField()])}>+ Add field</button>
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
