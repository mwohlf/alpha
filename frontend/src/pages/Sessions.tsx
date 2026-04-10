import { useEffect, useRef } from "react";
import { useSessionsStore } from "../store/useSessionsStore";
import "./Sessions.css";

function displayName(user: { username?: string | null; first_name?: string | null; last_name?: string | null }): string {
  if (user.first_name || user.last_name) {
    return [user.first_name, user.last_name].filter(Boolean).join(" ");
  }
  return user.username ? `@${user.username}` : "Unknown";
}

export default function Sessions() {
  const { users, selectedUserId, messages, loadingUsers, loadingMessages, error, fetchUsers, selectUser } =
    useSessionsStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="sessions">
      <div className="sessions-master">
        <h2>Users</h2>
        {loadingUsers && <p className="sessions-status">Loading...</p>}
        {error && <p className="sessions-error">{error}</p>}
        <ul>
          {users.map((user) => (
            <li
              key={user.user_id}
              className={user.user_id === selectedUserId ? "active" : ""}
              onClick={() => selectUser(user.user_id)}
            >
              <span className="sessions-user-name">{displayName(user)}</span>
              <span className="sessions-user-count">{user.message_count}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="sessions-detail">
        <div className="sessions-messages">
          {loadingMessages && <p className="sessions-status">Loading...</p>}
          {!selectedUserId && !loadingMessages && (
            <p className="sessions-status">Select a user to view messages.</p>
          )}
          {messages.map((msg) => (
            <div key={msg.id} className={`sessions-bubble-row ${msg.outgoing ? "outgoing" : "incoming"}`}>
              <div className="sessions-bubble">
                {!msg.outgoing && (
                  <span className="sessions-bubble-chat">{msg.chat.title ?? `Chat ${msg.chat.chat_id}`}</span>
                )}
                <p className="sessions-bubble-text">{msg.text ?? <em>non-text message</em>}</p>
                <span className="sessions-bubble-time">{new Date(msg.date).toLocaleString()}</span>
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
}
