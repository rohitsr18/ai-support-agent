# app.py - Entry point for the AI Customer Support Agent API
# Sets up the FastAPI server with endpoints for chat and health check.

# Load environment variables from .env file (e.g. OPENAI_API_KEY)
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from agent import handle_message

# Create the FastAPI application instance
app = FastAPI()


# Request model: each chat message must include a session_id and the user's message
class ChatRequest(BaseModel):
    session_id: str   # Unique ID to track conversation history per user
    message: str      # The user's chat message


@app.post("/chat")
def chat(request: ChatRequest):
    """Main chat endpoint — receives a user message, processes it through the
    agent, and returns the AI-generated reply."""
    reply = handle_message(
        session_id=request.session_id,
        message=request.message
    )
    return {"reply": reply}


@app.get("/")
def health():
    """Health check endpoint — returns server status."""
    return {"status": "running"}


@app.get("/app", response_class=HTMLResponse)
def public_chat_app():
        """Simple browser chat UI for public testing and demos."""
        return """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AI Support Agent</title>
    <style>
        :root {
            --bg: #f6f7fb;
            --card: #ffffff;
            --ink: #141822;
            --muted: #6f7a90;
            --brand: #0d6efd;
            --user: #e7f0ff;
            --bot: #f1f3f8;
            --line: #d7deea;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Segoe UI, Tahoma, Arial, sans-serif;
            background: radial-gradient(circle at top left, #eef4ff 0%, var(--bg) 45%);
            color: var(--ink);
            min-height: 100vh;
            display: grid;
            place-items: center;
            padding: 20px;
        }
        .shell {
            width: min(840px, 100%);
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 16px;
            box-shadow: 0 18px 50px rgba(24, 39, 75, 0.12);
            overflow: hidden;
        }
        .head {
            padding: 16px 18px;
            border-bottom: 1px solid var(--line);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
        }
        .title { font-weight: 700; font-size: 18px; }
        .note { color: var(--muted); font-size: 13px; }
        .chat {
            height: 60vh;
            overflow-y: auto;
            padding: 16px;
            background: linear-gradient(180deg, #ffffff 0%, #fafcff 100%);
        }
        .msg {
            margin: 10px 0;
            padding: 12px 14px;
            border-radius: 12px;
            max-width: 85%;
            white-space: pre-wrap;
            line-height: 1.35;
        }
        .user { margin-left: auto; background: var(--user); border: 1px solid #c9dcff; }
        .bot { margin-right: auto; background: var(--bot); border: 1px solid #e1e6f0; }
        .foot {
            border-top: 1px solid var(--line);
            padding: 12px;
            display: grid;
            gap: 8px;
        }
        .row {
            display: grid;
            grid-template-columns: 1fr;
            gap: 8px;
        }
        input, textarea, button {
            font: inherit;
            border-radius: 10px;
            border: 1px solid var(--line);
            padding: 10px 12px;
            width: 100%;
        }
        textarea { min-height: 70px; resize: vertical; }
        button {
            background: var(--brand);
            color: #fff;
            border: none;
            cursor: pointer;
            font-weight: 600;
        }
        button:disabled { opacity: 0.65; cursor: wait; }
    </style>
</head>
<body>
    <main class="shell">
        <header class="head">
            <div class="title">AI Support Agent</div>
            <div class="note">Public chat demo</div>
        </header>
        <section id="chat" class="chat"></section>
        <section class="foot">
            <input id="session" placeholder="Session ID (example: user-1)" value="public-user-1" />
            <div class="row">
                <textarea id="message" placeholder="Type your question..."></textarea>
                <button id="send">Send</button>
            </div>
        </section>
    </main>

    <script>
        const chatEl = document.getElementById("chat");
        const sessionEl = document.getElementById("session");
        const messageEl = document.getElementById("message");
        const sendEl = document.getElementById("send");

        function append(role, text) {
            const div = document.createElement("div");
            div.className = "msg " + (role === "user" ? "user" : "bot");
            div.textContent = text;
            chatEl.appendChild(div);
            chatEl.scrollTop = chatEl.scrollHeight;
        }

        async function sendMessage() {
            const session_id = sessionEl.value.trim();
            const message = messageEl.value.trim();
            if (!session_id || !message) return;

            append("user", message);
            messageEl.value = "";
            sendEl.disabled = true;

            try {
                const res = await fetch("/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ session_id, message })
                });
                const data = await res.json();
                append("bot", data.reply || "No reply received.");
            } catch (err) {
                append("bot", "Error: could not reach server.");
            } finally {
                sendEl.disabled = false;
                messageEl.focus();
            }
        }

        sendEl.addEventListener("click", sendMessage);
        messageEl.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        append("bot", "Welcome. Ask about orders, returns, refunds, or delivery.");
    </script>
</body>
</html>
"""