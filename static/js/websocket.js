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

    setTimeout(() => isLocalChange = false, 100);  
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

