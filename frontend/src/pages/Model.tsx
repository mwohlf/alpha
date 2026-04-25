import { useEffect, useState } from "react";
import { useModelsStore } from "../store/useModelsStore";
import { useChatStore } from "../store/useChatStore";
import "./Model.css";

function formatSize(bytes?: number | null): string {
  if (!bytes) return "—";
  const gb = bytes / 1e9;
  return gb >= 1 ? `${gb.toFixed(1)} GB` : `${(bytes / 1e6).toFixed(0)} MB`;
}

export default function Model() {
  const { models, selected, loading, error, fetchModels, selectModel, deleteModel, addModel } = useModelsStore();
  const { selectedModel: defaultModel, setSelectedModel: setDefaultModel } = useChatStore();
  const [addName, setAddName] = useState("");
  const [pulling, setPulling] = useState(false);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  return (
    <div className="models">
      <div className="models-master">
        <div className="models-master-header">
          <h2 className="section-label">Models</h2>
        </div>
        <form className="models-add-form" onSubmit={async (e) => {
          e.preventDefault();
          const name = addName.trim();
          if (!name) return;
          setPulling(true);
          await addModel(name);
          setAddName("");
          setPulling(false);
        }}>
          <input
            className="models-add-input field-input"
            type="text"
            placeholder="Pull model…"
            value={addName}
            onChange={(e) => setAddName(e.target.value)}
            disabled={pulling || loading}
          />
          <button className="models-add-btn btn-primary" type="submit" disabled={!addName.trim() || pulling || loading}>
            {pulling ? "…" : "Pull"}
          </button>
        </form>
        {error && <p className="models-error page-error">{error}</p>}
        <ul className="models-list">
          {loading && models.length === 0 && (
            <li className="models-status page-status">Loading…</li>
          )}
          {models.map((model) => (
            <li
              key={model.name}
              className={model.name === selected?.name ? "active" : ""}
              onClick={() => selectModel(model)}
            >
              <span className="models-item-name">{model.name}</span>
              <span className="models-item-badges">
                {model.details?.parameter_size && (
                  <span className="models-item-badge">{model.details.parameter_size}</span>
                )}
                {model.name === defaultModel && (
                  <span className="models-item-badge models-item-badge--default">default</span>
                )}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="models-detail">
        {!selected ? (
          <p className="models-status page-status">Select a model to view details.</p>
        ) : (
          <div className="models-detail-content">
            <div className="models-detail-header">
              <h2>{selected.name}</h2>
            </div>
            <table className="models-detail-table">
              <tbody>
                <tr>
                  <td>Size</td>
                  <td>{formatSize(selected.size)}</td>
                </tr>
                {selected.details?.family && (
                  <tr><td>Family</td><td>{selected.details.family}</td></tr>
                )}
                {selected.details?.parameter_size && (
                  <tr><td>Parameters</td><td>{selected.details.parameter_size}</td></tr>
                )}
                {selected.details?.quantization_level && (
                  <tr><td>Quantization</td><td>{selected.details.quantization_level}</td></tr>
                )}
                {selected.details?.format && (
                  <tr><td>Format</td><td>{selected.details.format}</td></tr>
                )}
                {selected.modified_at && (
                  <tr>
                    <td>Modified</td>
                    <td>{new Date(selected.modified_at).toLocaleString()}</td>
                  </tr>
                )}
                {selected.digest && (
                  <tr>
                    <td>Digest</td>
                    <td className="models-digest">{selected.digest.slice(0, 24)}…</td>
                  </tr>
                )}
              </tbody>
            </table>
            <div className="models-detail-actions">
              {selected.name === defaultModel ? (
                <button
                  className="models-default-btn btn-ghost models-default-btn--active"
                  onClick={() => setDefaultModel(null)}
                >
                  Default ✓
                </button>
              ) : (
                <button
                  className="models-default-btn btn-ghost"
                  onClick={() => setDefaultModel(selected.name)}
                >
                  Set as default
                </button>
              )}
              <button
                className="models-delete-btn btn-danger"
                onClick={() => deleteModel(selected.name)}
                disabled={loading}
              >
                Delete
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
