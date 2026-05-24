const BASE = "/api";

export type DataType = "string" | "number" | "date" | "currency" | "list" | "object";

export interface FieldDef {
  name: string;
  data_type: DataType;
  required: boolean;
  hint: string;
  regex?: string | null;
  children?: FieldDef[] | null;
}

export interface DocumentTemplate {
  id: string;
  code: string;
  name: string;
  description: string;
  file_formats: string[];
  active: boolean;
  fields: FieldDef[];
}

export interface RequiredDocument {
  template_id: string;
  required: boolean;
  min_count: number;
  max_count: number;
}

export interface ApplicationType {
  id: string;
  code: string;
  name: string;
  description: string;
  active: boolean;
  required_documents: RequiredDocument[];
}

export interface Artifacts {
  json_schema: Record<string, unknown>;
  vlm_prompt: string;
}

export interface TemplateSample {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  uploaded_at: string;
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

export const api = {
  listAppTypes: () => req<ApplicationType[]>("/application-types"),
  createAppType: (body: Partial<ApplicationType>) =>
    req<ApplicationType>("/application-types", { method: "POST", body: JSON.stringify(body) }),
  updateAppType: (id: string, body: Partial<ApplicationType>) =>
    req<ApplicationType>(`/application-types/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  listTemplates: () => req<DocumentTemplate[]>("/document-templates"),
  getTemplate: (id: string) => req<DocumentTemplate>(`/document-templates/${id}`),
  createTemplate: (body: Partial<DocumentTemplate>) =>
    req<DocumentTemplate>("/document-templates", { method: "POST", body: JSON.stringify(body) }),
  updateTemplate: (id: string, body: Partial<DocumentTemplate>) =>
    req<DocumentTemplate>(`/document-templates/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  artifacts: (id: string) => req<Artifacts>(`/document-templates/${id}/artifacts`),

  listSamples: (tid: string) => req<TemplateSample[]>(`/document-templates/${tid}/samples`),
  uploadSample: async (tid: string, file: File): Promise<TemplateSample> => {
    const form = new FormData();
    form.append("file", file);
    const r = await fetch(`${BASE}/document-templates/${tid}/samples`, {
      method: "POST",
      body: form,
    });
    if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
    return r.json();
  },
  deleteSample: async (tid: string, sid: string): Promise<void> => {
    const r = await fetch(`${BASE}/document-templates/${tid}/samples/${sid}`, { method: "DELETE" });
    if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  },

  suggestFields: (body: { document_type_name: string; description?: string; sample_text?: string }) =>
    req<{ fields: FieldDef[]; provider: string }>("/suggest", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
