const socket = io();

socket.on('message', function(data){
    addMessage(data.message, data.author, data.recipient);
});

document.addEventListener("DOMContentLoaded", function(){
    fetch('/messages')
        .then(response => response.json())
        .then(data => {
            const chatList = document.getElementById('chat-list');
            const groupedMessages = groupMessagesByRecipient(data);
            for (const recipient in groupedMessages) {
                const chatItem = document.createElement('div');
                chatItem.className = 'chat-item';
                chatItem.textContent = recipient;
                chatItem.onclick = () => loadChat(recipient, groupedMessages[recipient]);
                chatList.appendChild(chatItem);
            }
        });
});

function groupMessagesByRecipient(messages) {
    return messages.reduce((groups, message) => {
        const key = message.recipient === current_user ? message.author : message.recipient;
        if (!groups[key]) {
            groups[key] = [];
        }
        groups[key].push(message);
        return groups;
    }, {});
}

function loadChat(recipient, messages) {
    const chatBox = document.getElementById('chat-box');
    const chatHeader = document.getElementById('chat-recipient');
    chatBox.innerHTML = '';
    chatHeader.textContent = recipient;
    messages.forEach(msg => addMessage(msg.content, msg.author, msg.recipient));
}

function addMessage(msg, author, recipient) {
    let chatBox = document.getElementById('chat-box');
    let messageElement = document.createElement('div');
    messageElement.className = 'message';
    messageElement.innerHTML = `
        <span>${author} to ${recipient}: ${msg}</span>
        <select class="translate-dropdown" onchange="translateMessage(this)">
            <option value="">Translate</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="zh-cn">Chinese</option>
            <!-- Add more languages as needed -->
        </select>
    `;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function sendMessage() {
    let recipientInput = document.getElementById('recipient');
    let messageInput = document.getElementById('message');
    let recipient = recipientInput.value;
    let message = messageInput.value;
    socket.emit('message', {recipient: recipient, message: message});
    messageInput.value = '';
}

function translateMessage(selectElement) {
    let messageElement = selectElement.previousElementSibling;
    let text = messageElement.textContent;
    let dest_lang = selectElement.value;

    fetch('/translate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({text: text, dest_lang: dest_lang})
    })
    .then(response => response.json())
    .then(data => {
        messageElement.textContent = data.translated_text;
    });
}
