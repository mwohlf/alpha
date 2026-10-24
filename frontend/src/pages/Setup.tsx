import { useState } from "react";
import { useDatabaseStore } from "../store/useDatabaseStore";
import "./Setup.css";

export default function Setup() {
  const { wiping, error, lastWipe, wipe } = useDatabaseStore();
  const [confirming, setConfirming] = useState(false);

  async function handleWipe() {
    setConfirming(false);
    await wipe();
  }

  return (
    <div className="page">
      <h2 className="section-label">Setup</h2>

      <section className="setup-card">
        <h3>Database</h3>
        <p className="setup-text">
          Delete all stored Telegram messages and personas. The default
          personas are restored afterwards. This cannot be undone.
        </p>
        {confirming ? (
          <div className="setup-actions">
            <span className="setup-text">Wipe all data?</span>
            <button className="btn-danger setup-btn" onClick={handleWipe}>
              Yes, wipe
            </button>
            <button
              className="btn-ghost setup-btn"
              onClick={() => setConfirming(false)}
            >
              Cancel
            </button>
          </div>
        ) : (
          <div className="setup-actions">
            <button
              className="btn-danger setup-btn"
              onClick={() => setConfirming(true)}
              disabled={wiping}
            >
              {wiping ? "Wiping…" : "Wipe database"}
            </button>
          </div>
        )}
        {error && <p className="page-error">{error}</p>}
        {lastWipe && (
          <p className="setup-text">
            Deleted{" "}
            {Object.entries(lastWipe)
              .map(([table, rows]) => `${rows} from ${table}`)
              .join(", ")}
            .
          </p>
        )}
      </section>
    </div>
  );
}
