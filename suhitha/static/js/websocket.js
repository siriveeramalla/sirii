const socket = new WebSocket(`ws://${window.location.host}/ws/document/${document_id}/`);

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    document.getElementById("document-content").innerText = data.content;

    // Display users currently editing
    let userList = document.getElementById("users-list");
    userList.innerHTML = "";
    data.users.forEach(user => {
        let li = document.createElement("li");
        li.innerText = user;
        userList.appendChild(li);
    });
};

// Send updates when user types
document.getElementById("document-content").addEventListener("input", function() {
    socket.send(JSON.stringify({
        content: this.innerText,
        user: currentUser
    }));
});
