import { useEffect } from "react";
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

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

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
        <h2>Messages</h2>
        {loadingMessages && <p className="sessions-status">Loading...</p>}
        {!selectedUserId && !loadingMessages && <p className="sessions-status">Select a user to view messages.</p>}
        <ul>
          {messages.map((msg) => (
            <li key={msg.id} className="sessions-message">
              <div className="sessions-message-meta">
                <span className="sessions-message-chat">{msg.chat.title ?? `Chat ${msg.chat.chat_id}`}</span>
                <span className="sessions-message-date">{new Date(msg.date).toLocaleString()}</span>
              </div>
              <p className="sessions-message-text">{msg.text ?? <em>non-text message</em>}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
