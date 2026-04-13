import { useEffect, useState } from "react";
import { usePersonaStore } from "../store/usePersonaStore";
import type { PersonaResponse } from "../generated/models";
import "./Persona.css";

type FormState = { name: string; content: string; is_active: boolean };

const EMPTY_FORM: FormState = { name: "", content: "", is_active: false };

export default function Persona() {
  const { personas, loading, error, fetchPersonas, createPersona, updatePersona } =
    usePersonaStore();

  const [selected, setSelected] = useState<PersonaResponse | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [isNew, setIsNew] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchPersonas();
  }, [fetchPersonas]);

  function selectPersona(p: PersonaResponse) {
    setSelected(p);
    setForm({ name: p.name, content: p.content, is_active: p.is_active });
    setIsNew(false);
  }

  function startNew() {
    setSelected(null);
    setForm(EMPTY_FORM);
    setIsNew(true);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim() || !form.content.trim()) return;
    setSaving(true);
    if (isNew) {
      await createPersona(form.name.trim(), form.content, form.is_active);
      setIsNew(false);
    } else if (selected) {
      await updatePersona(
        selected.id,
        form.name.trim(),
        form.content,
        form.is_active,
      );
    }
    setSaving(false);
    await fetchPersonas();
  }

  const dirty =
    isNew
      ? form.name.trim() !== "" || form.content !== ""
      : selected !== null &&
        (form.name !== selected.name ||
          form.content !== selected.content ||
          form.is_active !== selected.is_active);

  return (
    <div className="persona">
      <div className="persona-master">
        <div className="persona-master-header">
          <h2 className="section-label">Personas</h2>
          <button className="persona-new-btn btn-ghost" onClick={startNew}>
            New
          </button>
        </div>
        {error && <p className="persona-error page-error">{error}</p>}
        <ul className="persona-list">
          {loading && personas.length === 0 && (
            <li className="page-status">Loading…</li>
          )}
          {personas.map((p) => (
            <li
              key={p.id}
              className={selected?.id === p.id && !isNew ? "active" : ""}
              onClick={() => selectPersona(p)}
            >
              <span className="persona-item-name">{p.name}</span>
              {p.is_active && <span className="persona-item-badge">active</span>}
            </li>
          ))}
        </ul>
      </div>

      <div className="persona-detail">
        {!selected && !isNew ? (
          <p className="page-status">Select a persona to edit, or create a new one.</p>
        ) : (
          <form className="persona-form" onSubmit={handleSave}>
            <div className="persona-form-header">
              <h2>{isNew ? "New Persona" : selected?.name}</h2>
            </div>

            <label className="persona-field-label">Name</label>
            <input
              className="field-input persona-name-input"
              type="text"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="Persona name"
              disabled={saving}
            />

            <label className="persona-field-label">System prompt</label>
            <textarea
              className="field-input persona-content-input"
              value={form.content}
              onChange={(e) => setForm((f) => ({ ...f, content: e.target.value }))}
              placeholder="Enter the system prompt…"
              disabled={saving}
            />

            <label className="persona-active-label">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
                disabled={saving}
              />
              Set as active
            </label>

            <div className="persona-form-actions">
              <button
                type="submit"
                className="btn-primary persona-save-btn"
                disabled={saving || !dirty || !form.name.trim() || !form.content.trim()}
              >
                {saving ? "Saving…" : isNew ? "Create" : "Save"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
