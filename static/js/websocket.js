// Get the room ID from the URL (for example, "/room/1/")
/*const roomId = window.location.pathname.split('/')[2];

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
function saveContent() {
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: 'save_document',
            content: document.getElementById('document').innerHTML
        }));
    }
}
function manualSave() {
    saveContent();  // Use WebSocket save
    alert("Document saved!");
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
};*/
const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
const socket = new WebSocket(
    `${wsScheme}://${window.location.host}/ws/document/${roomId}/`
);

const editor = document.getElementById('editor');
const saveButton = document.getElementById('save-button');
const cursorsContainer = document.getElementById('cursors-container');

let isLocalChange = false;

socket.onopen = () => {
    console.log("WebSocket connection established.");
};

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'edit' && !isLocalChange) {
        editor.value = data.content;
    }

    if (data.type === 'cursor') {
        updateCursors(data.cursors);
    }
};

socket.onclose = () => {
    console.log("WebSocket connection closed.");
};

editor.addEventListener('input', () => {
    isLocalChange = true;

    socket.send(JSON.stringify({
        type: 'edit',
        content: editor.value
    }));

    setTimeout(() => isLocalChange = false, 100);  // Avoid echo loop
});

editor.addEventListener('keyup', () => {
    const position = editor.selectionStart;
    socket.send(JSON.stringify({
        type: 'cursor',
        username: username,
        position: position
    }));
});

saveButton.addEventListener('click', () => {
    socket.send(JSON.stringify({
        type: 'save',
        content: editor.value
    }));
});

function updateCursors(cursors) {
    cursorsContainer.innerHTML = '';

    for (const user in cursors) {
        if (user !== username) {
            const pos = cursors[user];
            const marker = document.createElement('div');
            marker.className = 'cursor-marker';
            marker.style.top = `${getCursorYPosition(editor, pos)}px`;
            marker.innerText = user;
            cursorsContainer.appendChild(marker);
        }
    }
}

function getCursorYPosition(textarea, position) {
    const dummy = document.createElement('div');
    dummy.style.visibility = 'hidden';
    dummy.style.position = 'absolute';
    dummy.style.whiteSpace = 'pre-wrap';
    dummy.style.wordWrap = 'break-word';
    dummy.style.width = `${textarea.offsetWidth}px`;
    dummy.style.font = window.getComputedStyle(textarea).font;
    dummy.textContent = textarea.value.substring(0, position);

    document.body.appendChild(dummy);
    const height = dummy.offsetHeight;
    document.body.removeChild(dummy);

    const scrollOffset = textarea.scrollTop;

    return height - scrollOffset;
}
