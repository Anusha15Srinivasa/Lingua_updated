const socket = io();

socket.on('message', function(data){
    addMessage(data.message, data.author, data.recipient);
});

document.addEventListener("DOMContentLoaded", function(){
    fetch('/messages')
        .then(response => response.json())
        .then(data => {
            data.forEach(msg => addMessage(msg.content, msg.author, msg.recipient));
        });
});

function addMessage(msg, author, recipient) {
    let chatBox = document.getElementById('chat-box');
    let messageElement = document.createElement('div');
    messageElement.textContent = `${author} to ${recipient}: ${msg}`;
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
