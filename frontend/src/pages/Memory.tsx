import { useEffect, useState } from "react";
import { useMemoryStore } from "../store/useMemoryStore";
import "./Memory.css";

export default function Memory() {
  const {
    memories,
    loading,
    error,
    fetchMemories,
    updateMemory,
    refreshMemory,
    media,
    fetchMedia,
    openMedia,
  } = useMemoryStore();

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [facts, setFacts] = useState("");
  const [busy, setBusy] = useState(false);

  const selected = memories.find((m) => m.chat_id === selectedId) ?? null;

  useEffect(() => {
    fetchMemories();
  }, []);

  useEffect(() => {
    if (selectedId !== null) fetchMedia(selectedId);
  }, [selectedId]);

  // reload the textarea whenever the stored facts of the selected chat change
  useEffect(() => {
    setFacts(selected?.facts ?? "");
  }, [selected?.chat_id, selected?.facts]);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    await action();
    setBusy(false);
  }

  const dirty = selected !== null && facts !== selected.facts;

  return (
    <div className="memory">
      <div className="memory-master">
        <div className="memory-master-header">
          <h2 className="section-label">Chats</h2>
        </div>
        {error && <p className="memory-error page-error">{error}</p>}
        <ul className="memory-list">
          {loading && memories.length === 0 && (
            <li className="page-status">Loading…</li>
          )}
          {!loading && memories.length === 0 && (
            <li className="page-status">No chats yet.</li>
          )}
          {memories.map((m) => (
            <li
              key={m.chat_id}
              className={selectedId === m.chat_id ? "active" : ""}
              onClick={() => setSelectedId(m.chat_id)}
            >
              <span className="memory-item-name">
                {m.title || m.chat_id}
              </span>
              <span className="memory-item-count">
                {m.facts ? m.facts.split("\n").length : 0}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="memory-detail">
        {!selected ? (
          <p className="page-status">
            Select a chat to see what is remembered about it.
          </p>
        ) : (
          <form
            className="memory-form"
            onSubmit={(e) => {
              e.preventDefault();
              run(() => updateMemory(selected.chat_id, facts));
            }}
          >
            <div className="memory-form-header">
              <h2>{selected.title || selected.chat_id}</h2>
              <span className="memory-meta">
                {selected.chat_type} ·{" "}
                {selected.updated_at
                  ? `updated ${new Date(selected.updated_at).toLocaleString()}`
                  : "nothing remembered yet"}
              </span>
            </div>

            <label className="memory-field-label">Facts — one per line</label>
            <textarea
              className="field-input memory-facts-input"
              value={facts}
              onChange={(e) => setFacts(e.target.value)}
              placeholder="- They want to be called Tom"
              disabled={busy}
            />

            <div className="memory-form-actions">
              <button
                type="submit"
                className="btn-primary memory-btn"
                disabled={busy || !dirty}
              >
                Save
              </button>
              <button
                type="button"
                className="btn-ghost memory-btn"
                disabled={busy || dirty}
                title="Fold messages since the last update into the facts now"
                onClick={() => run(() => refreshMemory(selected.chat_id))}
              >
                {busy ? "Working…" : "Update from chat"}
              </button>
            </div>

            <label className="memory-field-label">Media sent in this chat</label>
            {media.length === 0 ? (
              <p className="memory-meta">No media yet.</p>
            ) : (
              <ul className="memory-media-list">
                {media.map((item) => (
                  <li key={item.id}>
                    <a
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        openMedia(item.id);
                      }}
                    >
                      {item.message_type}
                    </a>
                    <span className="memory-meta">
                      {new Date(item.date).toLocaleString()}
                      {item.sender && selected.chat_type !== "private"
                        ? ` · ${item.sender}`
                        : ""}
                      {item.caption ? ` · ${item.caption}` : ""}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </form>
        )}
      </div>
    </div>
  );
}
