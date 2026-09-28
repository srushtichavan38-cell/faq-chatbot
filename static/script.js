const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const chatMessages = document.getElementById("chatMessages");
const clearBtn = document.getElementById("clearBtn");

const welcomeMessage = "Hello! 👋 I'm the FAQ Assistant.\nAsk me a question and I'll try to help.";

function addMessage(text, sender, meta = "") {
    const row = document.createElement("div");
    row.className = `message-row ${sender}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    if (meta) {
        const metaEl = document.createElement("div");
        metaEl.className = "message-meta";
        metaEl.textContent = meta;
        bubble.appendChild(metaEl);
    }

    row.appendChild(bubble);
    chatMessages.appendChild(row);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return row;
}

function showWelcome() {
    chatMessages.innerHTML = "";
    addMessage(welcomeMessage, "bot");
}

async function sendMessage(message) {
    const cleaned = message.trim();
    if (!cleaned) return;
    if (cleaned.length > 500) {
        addMessage("Please keep your question under 500 characters.", "bot");
        return;
    }

    addMessage(cleaned, "user");
    input.value = "";
    input.focus();
    sendBtn.disabled = true;

    const thinkingRow = addMessage("Thinking...", "bot");
    thinkingRow.querySelector(".bubble").classList.add("thinking");

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: cleaned })
        });

        const data = await response.json().catch(() => ({}));
        thinkingRow.remove();

        if (!response.ok) {
            throw new Error(data.error || "The server could not process your question.");
        }

        addMessage(data.answer || "I could not find an answer.", "bot");
    } catch (error) {
        thinkingRow.remove();
        addMessage(`Sorry, I couldn't connect to the chatbot. ${error.message}`, "bot");
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(input.value);
});

document.querySelectorAll(".suggestion-btn").forEach((button) => {
    button.addEventListener("click", () => sendMessage(button.textContent));
});

clearBtn.addEventListener("click", showWelcome);
showWelcome();
