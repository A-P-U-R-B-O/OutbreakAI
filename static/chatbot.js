document.addEventListener("DOMContentLoaded", function() {
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatWindow = document.getElementById("chat-window");
    const imageContainer = document.getElementById("image-container");
    const resetBtn = document.getElementById("reset-btn");

    function appendMessage(content, sender) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `msg ${sender}`;
        const msgText = document.createElement("div");
        msgText.className = "msg-text";
       msgText.innerHTML = DOMPurify.sanitize(marked.parse(content));
        msgDiv.appendChild(msgText);
        chatWindow.appendChild(msgDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    chatForm.onsubmit = async function(e) {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;
        appendMessage(text, "user");
        userInput.value = "";
        imageContainer.innerHTML = "";

        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        })
        .then(response => response.json())
        .then(data => {
            appendMessage(data.reply, "bot");
            imageContainer.innerHTML = "";
            if (data.image) {
                const img = document.createElement("img");
                img.src = "data:image/png;base64," + data.image;
                img.alt = "Simulation Chart";
                imageContainer.appendChild(img);
            }
        })
        .catch(() => {
            appendMessage("Error: Unable to connect to the server.", "bot");
        });
    };

    resetBtn.onclick = function() {
        fetch("/reset", { method: "POST" })
        .then(response => response.json())
        .then(data => {
            chatWindow.innerHTML = "";
            imageContainer.innerHTML = "";
            appendMessage(data.reply, "bot");
        });
    };

    // Optionally, focus input on load
    userInput.focus();
});
