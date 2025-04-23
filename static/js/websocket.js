// Get the room ID from the URL (for example, "/room/1/")
const roomId = window.location.pathname.split('/')[2];

// WebSocket connection to the room's document
const socket = new WebSocket(`ws://127.0.0.1:8000/ws/document/${roomId}/`);

// When a WebSocket message is received (like content update)
socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    // Handle content update
    if (data.content) {
        loadContent(data.content);  // Load the content into the document area
    }
    
    // Handle active editing users
    if (data.editingUsers) {
        updateEditingUsers(data.editingUsers);  // Update the list of users who are editing
    }
};
setInterval(saveContent, 3000);  // Auto-save every 3 seconds


// When WebSocket is open, log the connection
socket.onopen = () => {
    loadContent();  // ✅ pulls saved content
    setInterval(saveContent, 3000);  // ✅ auto-save
    editor.focus();
};

// When WebSocket connection closes, log the closure
socket.onclose = function(event) {
    console.log('WebSocket connection closed');
};

// Function to load the document content when a WebSocket message is received
function loadContent() {
    fetch(`/get-document/${roomId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.content !== lastContent) {
                editor.innerHTML = data.content;
                lastContent = data.content;
                hljs.highlightAll();
            }
        });
}


// Function to update the editing users in the UI
function updateEditingUsers(editingUsers) {
    const userListElement = document.getElementById('editing-users');
    if (userListElement) {
        userListElement.innerHTML = ''; // Clear the existing list
        editingUsers.forEach(user => {
            const userItem = document.createElement('li');
            userItem.textContent = user;
            userListElement.appendChild(userItem);
        });
    }
}

// Function to send content via WebSocket (when content is modified)
function sendContent(content) {
    socket.send(JSON.stringify({
        'content': content,
        'username': getUserName() // Send the username (you can retrieve it from the session)
    }));
}

// Function to send "editing" status to the server
function sendEditingStatus() {
    socket.send(JSON.stringify({
        'username': getUserName(),
        'editing': true
    }));
}

// Function to save document content via AJAX to the backend
function manualSave() {
    fetch(`/save-document/${roomId}/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}"
        },
        body: JSON.stringify({ content: editor.innerHTML })
    }).then(() => {
        alert("Document saved manually!");
    });
}

// Add an event listener to capture document changes and send updates to the server
document.getElementById('document').addEventListener('input', function() {
    const content = this.innerText;  // Get content from the editable area
    sendContent(content);           // Send content through WebSocket
    saveDocumentContent(roomId, content);  // Save content via AJAX
    sendEditingStatus();  // Send "editing" status to server
});

// Function to get the username of the logged-in user (you might have it stored globally or in the session)
function getUserName() {
    return document.getElementById('user-name').value;  // Assuming the username is stored in an element with id "user-name"
}

// When there is an error with the WebSocket connection
socket.onerror = function(error) {
    console.error('WebSocket Error:', error);
};
