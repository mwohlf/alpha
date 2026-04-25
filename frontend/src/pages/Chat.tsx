import { useEffect, useRef, useState } from "react";
import { useChatStore } from "../store/useChatStore";
import { useModelsStore } from "../store/useModelsStore";
import "./Chat.css";

export default function Chat() {
  const { history, loading, error, sendMessage, clearHistory, selectedModel } =
    useChatStore();
  const { fetchModels } = useModelsStore();
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchModels();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading]);

  useEffect(() => {
    if (!loading) inputRef.current?.focus();
  }, [loading]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    setInput("");
    sendMessage(trimmed);
  }

  return (
    <div className="chat">
      <div className="chat-toolbar">
        <span className="chat-title section-label">Ollama Chat</span>
        <div className="chat-toolbar-right">
          <span className="chat-model-label">
            {selectedModel ?? "Default model"}
          </span>
          <button
            className="chat-clear btn-ghost"
            onClick={clearHistory}
            disabled={loading}
          >
            Clear
          </button>
        </div>
      </div>

      <div className="chat-messages">
        {history.length === 0 && !loading && (
          <p className="chat-status page-status">
            Send a message to start a conversation.
          </p>
        )}
        {history.map((msg, i) => (
          <div key={i} className={`chat-bubble-row ${msg.role}`}>
            <div className="chat-bubble">
              <p className="chat-bubble-text">{msg.content}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-bubble-row assistant">
            <div className="chat-bubble chat-bubble-thinking">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}
        {error && <p className="chat-error page-error">{error}</p>}
        <div ref={bottomRef} />
      </div>

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          className="chat-input field-input"
          type="text"
          placeholder="Message Ollama…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <button
          className="chat-send btn-primary"
          type="submit"
          disabled={!input.trim() || loading}
        >
          Send
        </button>
      </form>
    </div>
  );
}
