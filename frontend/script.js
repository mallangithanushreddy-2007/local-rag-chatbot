const API_URL = 'http://127.0.0.1:8000/api';
let chatHistory = [];

async function uploadFiles() {
    const fileInput = document.getElementById('fileUpload');
    const status = document.getElementById('uploadStatus');
    
    if (fileInput.files.length === 0) return;
    
    status.innerText = "Uploading and processing...";
    const formData = new FormData();
    for (let file of fileInput.files) {
        formData.append('files', file);
    }
    
    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            status.innerText = "Documents processed successfully!";
            setTimeout(() => status.innerText = "", 3000);
        } else {
            status.innerText = "Failed to process documents.";
        }
    } catch (error) {
        status.innerText = "Error uploading documents.";
    }
}

function newChat() {
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.innerHTML = `
        <div class="empty-state" id="emptyState">
            <h1>Hello, Thanush</h1>
            <p>How can I help you today?</p>
        </div>
    `;
}

function handleEnter(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;
    
    input.value = '';
    
    const chatContainer = document.getElementById('chatContainer');
    const emptyState = document.getElementById('emptyState');
    if (emptyState) emptyState.remove();
    
    // Add user message
    const userDiv = document.createElement('div');
    userDiv.className = 'message user';
    userDiv.innerHTML = `
        <div class="avatar user-avatar">U</div>
        <div class="message-content"><p>${message}</p></div>
    `;
    chatContainer.appendChild(userDiv);
    
    // Add assistant placeholder
    const botDiv = document.createElement('div');
    botDiv.className = 'message';
    botDiv.innerHTML = `
        <div class="avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L9 9L2 12L9 15L12 22L15 15L22 12L15 9L12 2Z"/></svg>
        </div>
        <div class="message-content" id="loading-${Date.now()}">thinking...</div>
    `;
    chatContainer.appendChild(botDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    const contentDiv = botDiv.querySelector('.message-content');
    
    const model = document.getElementById('modelSelect').value;
    
    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: message,
                model: model
            })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let botMessage = "";
        contentDiv.innerHTML = "";
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            botMessage += decoder.decode(value, { stream: true });
            // Use marked.js to render markdown
            contentDiv.innerHTML = marked.parse(botMessage);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    } catch (error) {
        contentDiv.innerHTML = "Error connecting to backend.";
    }
}
