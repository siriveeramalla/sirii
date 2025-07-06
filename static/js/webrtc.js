let localStream;
let peerConnections = {};
const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
const config = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };
const videoGrid = document.getElementById("video-grid");
const localVideo = document.createElement("video");
localVideo.muted = true;
videoGrid.appendChild(localVideo);
const callSocket = new WebSocket(
    `${wsScheme}://${window.location.host}/ws/call/${roomId}/`
);

const startButton = document.getElementById("start-video-call");

if (startButton) {
    startButton.addEventListener("click", startVideoCall);
} else {
    console.error("Start video button not found");
}

function startVideoCall() {
    const callSocket = new WebSocket(
    `${wsScheme}://${window.location.host}/ws/call/${roomId}/`
);


    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        .then(stream => {
            localStream = stream;
            localVideo.srcObject = stream;
            localVideo.play();

            callSocket.send(JSON.stringify({
                type: "join-call",
                username: username
            }));
        })
        .catch(error => {
            console.error("Error accessing media devices.", error);
        });
}

callSocket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "join-call" && data.username !== username) {
        createOffer(data.username);
    } else if (data.type === "offer") {
        handleOffer(data.offer, data.username);
    } else if (data.type === "answer") {
        handleAnswer(data.answer, data.username);
    } else if (data.type === "ice-candidate") {
        handleNewICECandidate(data.candidate, data.username);
    }
};

function createOffer(remoteUsername) {
    const peer = new RTCPeerConnection(config);
    localStream.getTracks().forEach(track => peer.addTrack(track, localStream));

    peer.onicecandidate = event => {
        if (event.candidate) {
            callSocket.send(JSON.stringify({
                type: "ice-candidate",
                candidate: event.candidate,
                username: username,
                target: remoteUsername
            }));
        }
    };

    peer.ontrack = event => {
        const remoteVideo = document.createElement("video");
        remoteVideo.srcObject = event.streams[0];
        remoteVideo.autoplay = true;
        videoGrid.appendChild(remoteVideo);
    };

    peer.createOffer()
        .then(offer => {
            peer.setLocalDescription(offer);
            callSocket.send(JSON.stringify({
                type: "offer",
                offer: offer,
                username: username,
                target: remoteUsername
            }));
        });

    peerConnections[remoteUsername] = peer;
}

function handleOffer(offer, remoteUsername) {
    const peer = new RTCPeerConnection(config);
    localStream.getTracks().forEach(track => peer.addTrack(track, localStream));

    peer.onicecandidate = event => {
        if (event.candidate) {
            callSocket.send(JSON.stringify({
                type: "ice-candidate",
                candidate: event.candidate,
                username: username,
                target: remoteUsername
            }));
        }
    };

    peer.ontrack = event => {
        const remoteVideo = document.createElement("video");
        remoteVideo.srcObject = event.streams[0];
        remoteVideo.autoplay = true;
        videoGrid.appendChild(remoteVideo);
    };

    peer.setRemoteDescription(new RTCSessionDescription(offer))
        .then(() => peer.createAnswer())
        .then(answer => {
            peer.setLocalDescription(answer);
            callSocket.send(JSON.stringify({
                type: "answer",
                answer: answer,
                username: username,
                target: remoteUsername
            }));
        });

    peerConnections[remoteUsername] = peer;
}

function handleAnswer(answer, remoteUsername) {
    const peer = peerConnections[remoteUsername];
    if (peer) {
        peer.setRemoteDescription(new RTCSessionDescription(answer));
    }
}

function handleNewICECandidate(candidate, remoteUsername) {
    const peer = peerConnections[remoteUsername];
    if (peer) {
        peer.addIceCandidate(new RTCIceCandidate(candidate));
    }
}