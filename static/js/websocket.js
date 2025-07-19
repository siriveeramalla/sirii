        let editor = document.getElementById("editor");
        let lastContent = editor.innerHTML;
        let activeCursors = new Map();
        let saveTimeout;
        let lastSavedContent = editor.innerHTML;
        let isConnected = false;
        let connectionAttempts = 0;
        let maxConnectionAttempts = 5;
        let isLocalChange = false;
        let socketProtocol = window.location.protocol === "https:" ? "wss" : "ws";
        let socket = new WebSocket(`${socketProtocol}://${window.location.host}/ws/document/${roomId}/`);
        let callStartTime;
        let callTimer;
        function formatText(command) {
            document.execCommand(command, false, null);
            editor.focus();
            sendUpdate();
        }

        function changeFontSize(size) {
            document.execCommand('fontSize', false, '7');
            const fontElements = document.querySelectorAll('font[size="7"]');
            fontElements.forEach(element => {
                element.removeAttribute('size');
                element.style.fontSize = size + 'px';
            });
            editor.focus();
            sendUpdate();
        }

        function changeTextColor(color) {
            document.execCommand('foreColor', false, color);
            editor.focus();
            sendUpdate();
        }

        function changeBackgroundColor(color) {
            document.execCommand('backColor', false, color);
            editor.focus();
            sendUpdate();
        }

        function insertTable() {
            const tableHTML = `
                <table style="border-collapse: collapse; width: 100%; margin: 15px 0;">
                    <tr>
                        <th style="border: 1px solid #ddd; padding: 12px; background-color: #f8f9fa;">Header 1</th>
                        <th style="border: 1px solid #ddd; padding: 12px; background-color: #f8f9fa;">Header 2</th>
                        <th style="border: 1px solid #ddd; padding: 12px; background-color: #f8f9fa;">Header 3</th>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 12px;">Cell 1</td>
                        <td style="border: 1px solid #ddd; padding: 12px;">Cell 2</td>
                        <td style="border: 1px solid #ddd; padding: 12px;">Cell 3</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 12px;">Cell 4</td>
                        <td style="border: 1px solid #ddd; padding: 12px;">Cell 5</td>
                        <td style="border: 1px solid #ddd; padding: 12px;">Cell 6</td>
                    </tr>
                </table>
            `;
            document.execCommand('insertHTML', false, tableHTML);
            editor.focus();
            sendUpdate();
        }

        function insertHR() {
            const hrHTML = '<hr style="border: none; height: 2px; background: linear-gradient(45deg, #667eea, #764ba2); margin: 20px 0; border-radius: 1px;">';
            document.execCommand('insertHTML', false, hrHTML);
            editor.focus();
            sendUpdate();
        }

        
       
        function showToast(message, type = 'success') {
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.remove();
            }, 4000);
        }

    
        function updateConnectionStatus(status) {
            const statusElement = document.querySelector('.connection-status');
            const saveStatus = document.getElementById('save-status');
            
            statusElement.className = `connection-status ${status}`;
            
            switch(status) {
                case 'connected':
                    saveStatus.textContent = 'Connected & Synced';
                    isConnected = true;
                    break;
                case 'connecting':
                    saveStatus.textContent = 'Connecting...';
                    isConnected = false;
                    break;
                case 'disconnected':
                    saveStatus.textContent = 'Auto-save mode';
                    isConnected = false;
                    break;
            }
        }

      
        function connectWebSocket() {
            console.log("Attempting WebSocket connection...");
            updateConnectionStatus('connecting');
            
            try {
                const wsUrl = `${socketProtocol}://${window.location.host}/ws/document/${roomId}/`;
                console.log("Connecting to:", wsUrl);
                
                socket = new WebSocket(wsUrl);
                
                socket.onopen = () => {
                    console.log("✅ WebSocket connected");
                    updateConnectionStatus('connected');
                    connectionAttempts = 0;
                    showToast('Connected to real-time collaboration!', 'success');
                };

                socket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log("Received WebSocket message:", data);

                        if (data.type === "edit" && data.username !== currentUsername) {
                        document.getElementById("editor").value = data.content;
    }
                        if (data.type === 'edit' && !isLocalChange && data.content !== lastContent) {
                            editor.innerHTML = data.content;
                            lastContent = data.content;
                            updateLastEditTime();
                        }

                      
                        if (data.type === 'cursor') {
                            updateCursors(data.cursors || {});
                        }

                      
                        if (data.type === "user_joined" || data.type === "user_left") {
                            updateActiveUsers();
                        }

                       
                        if (data.type === 'video_call_start' && data.username !== username) {
                            showToast(`${data.username} started a video call`, 'success');
                        }

                        if (data.type === 'video_call_end' && data.username !== username) {
                            showToast(`${data.username} ended the video call`, 'success');
                        }
                    } catch (error) {
                        console.error("Error parsing WebSocket message:", error);
                    }
                };

                socket.onclose = (event) => {
                    console.log("❌ WebSocket disconnected");
                    updateConnectionStatus('disconnected');
                    
                    if (connectionAttempts < maxConnectionAttempts) {
                        connectionAttempts++;
                        console.log(`Reconnecting... (${connectionAttempts}/${maxConnectionAttempts})`);
                        setTimeout(() => {
                            updateConnectionStatus('connecting');
                            connectWebSocket();
                        }, 2000 * connectionAttempts);
                    } else {
                        console.log("Max reconnection attempts reached, switching to auto-save mode");
                        startAutoSaveMode();
                        showToast('Connection lost. Working in offline mode.', 'error');
                    }
                };

                socket.onerror = (error) => {
                    console.error("WebSocket error:", error);
                    updateConnectionStatus('disconnected');
                };

            } catch (error) {
                console.error("Failed to create WebSocket:", error);
                updateConnectionStatus('disconnected');
                startAutoSaveMode();
            }
        }

       
        function startAutoSaveMode() {
            console.log("Starting auto-save mode (WebSocket unavailable)");
            updateConnectionStatus('disconnected');
            
            setInterval(() => {
                if (!isConnected) {
                    autoSave();
                }
            }, 3000);
        }

       
        function autoSave(force = false) {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(() => {
                const currentContent = editor.innerHTML;
                if (currentContent !== lastSavedContent || force) {
                    const saveStatus = document.getElementById('save-status');
                    const originalText = saveStatus.textContent;
                    saveStatus.textContent = 'Saving...';
                    
                    fetch(`/save-document/${roomId}/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': '{{ csrf_token }}'
                        },
                        body: JSON.stringify({ content: currentContent })
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Save failed');
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.status === 'success') {
                            lastSavedContent = currentContent;
                            updateLastEditTime();
                            if (!isConnected) {
                                saveStatus.textContent = 'Auto-saved ✓';
                                setTimeout(() => {
                                    if (!isConnected) {
                                        saveStatus.textContent = 'Auto-save mode';
                                    }
                                }, 2000);
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Auto-save error:', error);
                        if (!isConnected) {
                            saveStatus.textContent = 'Save Error ✗';
                            setTimeout(() => {
                                saveStatus.textContent = originalText;
                            }, 3000);
                        }
                    });
                }
            }, 1500);
        }

        
        function updateLastEditTime() {
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            document.getElementById('last-edit-time').textContent = timeString;
            document.getElementById('last-edit-user').textContent = username;
        }

       
        function getTextOffset() {
            const selection = window.getSelection();
            if (!selection || selection.rangeCount === 0) return 0;
            
            const range = selection.getRangeAt(0);
            const preCaretRange = range.cloneRange();
            preCaretRange.selectNodeContents(editor);
            preCaretRange.setEnd(range.endContainer, range.endOffset);
            
            return preCaretRange.toString().length;
        }
        function sendUpdate() {
            const currentContent = editor.innerHTML;
            const cursorPosition = getTextOffset();

            if (currentContent !== lastContent) {
                lastContent = currentContent;
                autoSave();
            }
            
            if (isConnected && socket && socket.readyState === WebSocket.OPEN) {
                isLocalChange = true;
                
               
                socket.send(JSON.stringify({
                    type: 'edit',
                    content: currentContent
                }));
                
             
                socket.send(JSON.stringify({
                    type: 'cursor',
                    username: username,
                    position: cursorPosition
                }));
                
                setTimeout(() => isLocalChange = false, 100);
                console.log(`Sent update: content length ${currentContent.length}, cursor at ${cursorPosition}`);
            }
        }

        
        function updateActiveUsers() {
            fetch(`/get-active-users/${roomId}/`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to fetch active users');
                    }
                    return response.json();
                })
                .then(data => {
                    const container = document.getElementById("active-users");
                    container.innerHTML = '';
                    
                    if (data.users && data.users.length > 0) {
                        data.users.forEach(user => {
                            const span = document.createElement("span");
                            span.className = "editor-badge";
                            span.textContent = user;
                            container.appendChild(span);
                        });
                    } else {
                        const span = document.createElement("span");
                        span.className = "no-users-message";
                        span.textContent = "Only you are editing";
                        container.appendChild(span);
                    }
                })
                .catch(error => {
                    console.error("Error updating active users:", error);
                    const container = document.getElementById("active-users");
                    container.innerHTML = '<span class="no-users-message">Unable to load active users</span>';
                });
        }

       
        function openShareModal() {
            document.getElementById("shareModal").style.display = "block";
        }

        function closeShareModal() {
            document.getElementById("shareModal").style.display = "none";
        }

        function sendShareInvite() {
            const emailsInput = document.getElementById("shareEmails");
            const messageInput = document.getElementById("shareMessage");
            const emails = emailsInput.value;
            const message = messageInput.value;
            
            if (!emails.trim()) {
                showToast("Please enter at least one email address", "error");
                emailsInput.focus();
                return;
            }
            
            
            const emailList = emails.split(',').map(email => email.trim());
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            const invalidEmails = emailList.filter(email => !emailRegex.test(email));
            
            if (invalidEmails.length > 0) {
                showToast(`Invalid email format: ${invalidEmails.join(', ')}`, "error");
                return;
            }
            
            const roomUrl = `${window.location.origin}/join-room/${roomId}/`;
            
            
            const sendButton = document.querySelector('#shareModal .btn-primary');
            const originalText = sendButton.textContent;
            sendButton.textContent = '📤 Sending...';
            sendButton.disabled = true;
            
            fetch(`/share-document/${roomId}/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": "{{ csrf_token }}"
                },
                body: JSON.stringify({ 
                    emails: emailList,
                    message: message,
                    room_name: "{{ room.name }}",
                    room_url: roomUrl
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === "success") {
                    showToast(`✅ Invitations sent successfully to ${emailList.length} recipient(s)!`, "success");
                    closeShareModal();
                    emailsInput.value = "";
                    messageInput.value = `I'd like to collaborate on "{{ room.name }}" with you. Join me for real-time editing!`;
                } else {
                    throw new Error(data.message || "Unknown error occurred");
                }
            })
            .catch(error => {
                console.error("Share error:", error);
                showToast(`❌ Failed to send invitations: ${error.message}`, "error");
            })
            .finally(() => {
                
                sendButton.textContent = originalText;
                sendButton.disabled = false;
            });
        }

   
        editor.addEventListener('input', sendUpdate);
        editor.addEventListener('keyup', sendUpdate);
        editor.addEventListener('mouseup', sendUpdate);
        editor.addEventListener('click', sendUpdate);
        editor.addEventListener('paste', () => {
            setTimeout(sendUpdate, 100);
        });

       
        window.onclick = function(event) {
            const shareModal = document.getElementById("shareModal");
            const videoModal = document.getElementById("videoModal");
            
            if (event.target === shareModal) {
                closeShareModal();
            }
            if (event.target === videoModal) {
                endVideoCall();
            }
        }

       
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'b':
                        e.preventDefault();
                        formatText('bold');
                        break;
                    case 'i':
                        e.preventDefault();
                        formatText('italic');
                        break;
                    case 'u':
                        e.preventDefault();
                        formatText('underline');
                        break;
                    case 's':
                        e.preventDefault();
                        autoSave(true);
                        showToast('Document saved!', 'success');
                        break;
                }
            }
        });

      
        console.log("Initializing document editor...");
        
      
        updateLastEditTime();
        connectWebSocket();
        updateActiveUsers();
        setInterval(updateActiveUsers, 5000);
        
        
        setInterval(() => {
            const now = Date.now();
            activeCursors.forEach((cursor, username) => {
                if (now - cursor.lastUpdate > 15000) {
                    if (cursor.element && cursor.element.parentNode) {
                        cursor.element.remove();
                    }
                    activeCursors.delete(username);
                }
            });
        }, 5000);
        function updateEditingStatus() {
            fetch(`/update-editing-status/${roomId}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': '{{ csrf_token }}' }
            });
        }

        function fetchEditingUsers() {
            fetch(`/get-editing-users/${roomId}/`)
                .then(response => response.json())
                .then(data => {
                    const usersDiv = document.getElementById("editing-users");
                    if (data.editing.length > 0) {
                        usersDiv.innerText = "Editing: " + data.editing.join(", ");
                    } else {
                        usersDiv.innerText = "No one is editing...";
                    }
                });
        }

        editor.addEventListener("input", updateEditingStatus);
        setInterval(fetchEditingUsers, 1000);
        setInterval(updateActiveUsers, 1000);

        setTimeout(() => {
            editor.focus();
        }, 100);
         setInterval(() => {
            autoSave();
        }, 30000);
        console.log("Document editor initialized successfully");