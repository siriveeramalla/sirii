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