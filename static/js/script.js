function handleUserMessage() {
    const userInput = document.getElementById('user-input');
    const userMessage = userInput.value.trim();

    if (userMessage === '') return;

    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML += `<div class="user-message">User: ${userMessage}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        chatBox.innerHTML += `<div class="bot-message">Bot: ${data.response}</div>`;
        if (data.ticket_id) {
            chatBox.innerHTML += `<div class="bot-message">Your ticket ID is ${data.ticket_id}.</div>`;
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    });

    userInput.value = ''; // Clear input field after sending
}
