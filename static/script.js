// let myName = "";
// let myPort = "";

// // Hàm này tự động chạy khi trang Chat tải xong
// async function startChatApp(username) {
//     myName = username;
//     myPort = localStorage.getItem('chat_port') || "9000"; 
    
//     console.log(`Đang chat với tên: ${myName}`);

//     // 1. Báo danh với Server (Quan trọng để hiện tên trong danh sách)
//     await fetch('/submit-info', {
//         method: 'POST',
//         body: JSON.stringify({ name: myName, ip: "127.0.0.1", port: myPort })
//     });

//     // 2. Chạy vòng lặp cập nhật
//     refreshPeers();
//     fetchMessages();
//     setInterval(refreshPeers, 3000);   
//     setInterval(fetchMessages, 1000);  
// }

// // Lấy danh sách bạn bè
// async function refreshPeers() {
//     try {
//         const res = await fetch('/get-list');
//         const peers = await res.json();
//         const list = document.getElementById('peer-list');
//         if(list) {
//             list.innerHTML = "";
//             peers.forEach(p => {
//                 if (p.name !== myName) {
//                     const initial = p.name.charAt(0).toUpperCase();
//                     let li = document.createElement('li');
//                     li.innerHTML = `<div class="avatar">${initial}</div>
//                                     <div class="contact-info"><b>${p.name}</b><br><small>${p.port}</small></div>`;
//                     list.appendChild(li);
//                 }
//             });
//         }
//     } catch (e) { console.log(e); }
// }

// // Gửi tin nhắn
// async function sendMessage() {
//     const input = document.getElementById('msg-input');
//     const msg = input.value;
//     if (!msg) return;

//     await fetch('/send-msg', {
//         method: 'POST',
//         body: JSON.stringify({ sender: myName, message: msg })
//     });
    
//     input.value = "";
//     fetchMessages();
// }

// // Nhận tin nhắn
// let lastMsgCount = 0;
// async function fetchMessages() {
//     try {
//         const res = await fetch('/get-msgs');
//         const msgs = await res.json();

//         if (msgs.length > lastMsgCount) {
//             const window = document.getElementById('message-window');
//             if(window) {
//                 window.innerHTML = '<div class="system-msg">Lịch sử trò chuyện</div>';
//                 msgs.forEach(m => {
//                     const div = document.createElement('div');
//                     div.className = `message ${m.sender === myName ? 'sent' : 'received'}`;
//                     div.innerText = `${m.sender}: ${m.content}`;
//                     window.appendChild(div);
//                 });
//                 window.scrollTop = window.scrollHeight;
//                 lastMsgCount = msgs.length;
//             }
//         }
//     } catch (e) { console.log(e); }
// }






// let currentUser = null;
// let currentTarget = null; // Người mà bạn đang muốn gửi tin nhắn

// // Hàm khởi chạy (được gọi từ chat.html)
// function startChatApp(user) {
//     currentUser = user;
//     console.log("Logged in as:", currentUser);
    
//     // Bắt đầu cập nhật danh sách online mỗi 3 giây
//     fetchPeerList();
//     setInterval(fetchPeerList, 3000);
// }

// // 1. Lấy danh sách Peer đang online từ Server
// async function fetchPeerList() {
//     try {
//         // Backend start_sampleapp.py yêu cầu 'connect-peer' để lấy danh sách
//         // VÀ yêu cầu phải gửi peer_id lên để chứng thực
//         const response = await fetch('/connect-peer', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ 
//                 peer_id: currentUser 
//             })
//         });

//         if (response.ok) {
//             const data = await response.json();
//             renderPeerList(data.peers);
//         } else {
//             console.error("Lỗi lấy danh sách peer:", await response.text());
//         }
//     } catch (error) {
//         console.error("Lỗi kết nối:", error);
//     }
// }

// // 2. Hiển thị danh sách Peer lên giao diện
// function renderPeerList(peers) {
//     const listElement = document.getElementById('peer-list');
//     listElement.innerHTML = ''; // Xóa danh sách cũ

//     if (!peers || peers.length === 0) {
//         listElement.innerHTML = '<li style="color: gray; padding: 10px;">Chưa có ai online...</li>';
//         return;
//     }

//     peers.forEach(peer => {
//         const li = document.createElement('li');
//         li.className = 'peer-item';
//         li.innerText = `${peer.peer_id} (${peer.ip}:${peer.port})`;
        
//         // Highlight người đang được chọn
//         if (currentTarget === peer.peer_id) {
//             li.classList.add('active');
//         }

//         // Sự kiện click để chọn người chat
//         li.onclick = () => {
//             currentTarget = peer.peer_id;
//             document.querySelector('.system-msg').innerText = `Đang chat với: ${currentTarget}`;
//             renderPeerList(peers); // Render lại để highlight
//         };

//         listElement.appendChild(li);
//     });
// }

// // 3. Gửi tin nhắn
// async function sendMessage() {
//     const input = document.getElementById('msg-input');
//     const messageText = input.value.trim();

//     if (!messageText) return; // Không gửi tin rỗng

//     if (!currentTarget) {
//         alert("Vui lòng chọn một người trong danh sách bên trái để chat!");
//         return;
//     }

//     // Hiển thị tin nhắn của mình lên màn hình ngay lập tức (UI)
//     appendMessage(currentUser, messageText, 'sent');

//     try {
//         // Gửi request lên server theo đúng format start_sampleapp.py yêu cầu
//         // API: /send-peer
//         // Body cần: peer_id (người gửi), target (người nhận), message
//         const response = await fetch('/send-peer', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({
//                 peer_id: currentUser,
//                 target: currentTarget,
//                 message: messageText
//             })
//         });

//         if (response.ok) {
//             input.value = ''; // Xóa ô nhập sau khi gửi xong
//         } else {
//             const errData = await response.json();
//             alert("Lỗi gửi tin: " + (errData.message || response.status));
//         }

//     } catch (error) {
//         console.error("Lỗi gửi tin nhắn:", error);
//         alert("Không thể kết nối tới server.");
//     }
// }

// // Hàm phụ trợ: Thêm tin nhắn vào khung chat
// function appendMessage(sender, text, type) {
//     const msgWindow = document.getElementById('message-window');
//     const msgDiv = document.createElement('div');
//     msgDiv.className = `message ${type}`;
    
//     // Tạo nội dung tin nhắn
//     msgDiv.innerHTML = `
//         <div class="msg-sender">${sender}</div>
//         <div class="msg-content">${text}</div>
//     `;
    
//     msgWindow.appendChild(msgDiv);
//     // Tự động cuộn xuống dưới cùng
//     msgWindow.scrollTop = msgWindow.scrollHeight;
// }











// let currentUser = null;
// let currentTarget = null; 

// function startChatApp(user) {
//     currentUser = user;
//     console.log("Logged in as:", currentUser);
    
//     // Cập nhật danh sách người online (3 giây/lần)
//     fetchPeerList();
//     setInterval(fetchPeerList, 3000);

//     // Cập nhật tin nhắn mới (2 giây/lần) <--- MỚI THÊM
//     fetchMessages();
//     setInterval(fetchMessages, 2000);
// }

// // 1. Lấy danh sách Peer
// async function fetchPeerList() {
//     try {
//         const response = await fetch('/connect-peer', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ peer_id: currentUser })
//         });
//         if (response.ok) {
//             const data = await response.json();
//             renderPeerList(data.peers);
//         }
//     } catch (error) { console.error(error); }
// }

// // 2. Render danh sách
// function renderPeerList(peers) {
//     const listElement = document.getElementById('peer-list');
//     if (!listElement) return; // Bảo vệ nếu DOM chưa load
//     listElement.innerHTML = ''; 

//     if (!peers || peers.length === 0) {
//         listElement.innerHTML = '<li style="color: gray; padding: 10px;">Chưa có ai online...</li>';
//         return;
//     }

//     peers.forEach(peer => {
//         const li = document.createElement('li');
//         li.className = 'peer-item';
//         li.innerText = `${peer.peer_id} (${peer.ip}:${peer.port})`;
        
//         if (currentTarget === peer.peer_id) li.classList.add('active');

//         li.onclick = () => {
//             currentTarget = peer.peer_id;
//             document.querySelector('.system-msg').innerText = `Đang chat với: ${currentTarget}`;
//             renderPeerList(peers); 
//         };
//         listElement.appendChild(li);
//     });
// }

// // 3. Gửi tin nhắn
// async function sendMessage() {
//     const input = document.getElementById('msg-input');
//     const messageText = input.value.trim();

//     if (!messageText) return; 
//     if (!currentTarget) {
//         alert("Vui lòng chọn một người trong danh sách bên trái để chat!");
//         return;
//     }

//     // Hiển thị tin mình gửi (Màu xanh)
//     appendMessage(currentUser, messageText, 'sent');

//     try {
//         const response = await fetch('/send-peer', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({
//                 peer_id: currentUser,
//                 target: currentTarget,
//                 message: messageText
//             })
//         });

//         if (response.ok) {
//             input.value = ''; 
//         } else {
//             alert("Lỗi gửi tin!");
//         }
//     } catch (error) { console.error(error); }
// }

// // 4. NHẬN TIN NHẮN (Polling) <--- MỚI THÊM
// async function fetchMessages() {
//     try {
//         const response = await fetch('/get-messages', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ peer_id: currentUser })
//         });

//         if (response.ok) {
//             const data = await response.json();
//             // Nếu có tin nhắn mới
//             if (data.messages && data.messages.length > 0) {
//                 data.messages.forEach(msg => {
//                     // Hiển thị tin nhận được (Màu xám)
//                     // Chỉ hiển thị nếu đang không chat với ai HOẶC chat đúng người gửi
//                     // (Tùy logic bạn muốn, ở đây hiển thị hết cho dễ test)
//                     appendMessage(msg.sender, msg.message, 'received');
//                 });
//             }
//         }
//     } catch (error) { console.error("Lỗi nhận tin:", error); }
// }

// // Phụ trợ: Thêm tin nhắn vào khung UI
// function appendMessage(sender, text, type) {
//     const msgWindow = document.getElementById('message-window');
//     if (!msgWindow) return;

//     const msgDiv = document.createElement('div');
//     msgDiv.className = `message ${type}`;
    
//     msgDiv.innerHTML = `
//         <div class="msg-sender">${sender}</div>
//         <div class="msg-content">${text}</div>
//     `;
    
//     msgWindow.appendChild(msgDiv);
//     msgWindow.scrollTop = msgWindow.scrollHeight;
// }






let currentUser = null;
let currentTarget = null;
// Biến lưu trữ lịch sử chat của từng người
// Cấu trúc: { "dada": [ {sender: "dada", message: "hi"}, ... ], "hung": [...] }
let chatHistory = {}; 

function startChatApp(user) {
    currentUser = user;
    console.log("Logged in as:", currentUser);
    
    // Cập nhật danh sách online (3 giây/lần)
    fetchPeerList();
    setInterval(fetchPeerList, 3000);

    // Polling tin nhắn mới (2 giây/lần)
    fetchMessages();
    setInterval(fetchMessages, 2000);
}

// 1. Lấy danh sách Peer
async function fetchPeerList() {
    try {
        const response = await fetch('/connect-peer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ peer_id: currentUser })
        });
        if (response.ok) {
            const data = await response.json();
            renderPeerList(data.peers);
        }
    } catch (error) { console.error(error); }
}

// 2. Render danh sách Peer
function renderPeerList(peers) {
    const listElement = document.getElementById('peer-list');
    if (!listElement) return;

    // Lưu lại trạng thái user đang chọn để không bị mất focus khi re-render
    const savedTarget = currentTarget;

    listElement.innerHTML = ''; 

    if (!peers || peers.length === 0) {
        listElement.innerHTML = '<li style="color: gray; padding: 10px;">Chưa có ai online...</li>';
        return;
    }

    peers.forEach(peer => {
        const li = document.createElement('li');
        li.className = 'peer-item';
        li.innerText = `${peer.peer_id} (${peer.ip}:${peer.port})`;
        
        // Highlight người đang được chọn
        if (savedTarget === peer.peer_id) li.classList.add('active');

        // Kiểm tra xem người này có tin nhắn chưa đọc không (Optional UX)
        if (chatHistory[peer.peer_id] && peer.peer_id !== savedTarget) {
            // Logic hiển thị thông báo tin nhắn mới có thể thêm ở đây
            // li.style.fontWeight = "bold"; 
        }

        li.onclick = () => {
            // 1. Đổi người target
            currentTarget = peer.peer_id;
            
            // 2. Cập nhật UI Header
            document.querySelector('.system-msg').innerText = `Đang chat với: ${currentTarget}`;
            
            // 3. Highlight lại danh sách
            renderPeerList(peers); 

            // 4. QUAN TRỌNG: Load lại lịch sử chat của người này ra màn hình
            loadChatHistory(currentTarget);
        };
        listElement.appendChild(li);
    });
}

// 3. Hàm Load lịch sử chat ra màn hình (MỚI)
function loadChatHistory(peerId) {
    const msgWindow = document.getElementById('message-window');
    msgWindow.innerHTML = `<div class="system-msg">Đang chat với: ${peerId}</div>`;

    // Lấy tin nhắn từ bộ nhớ đệm
    const history = chatHistory[peerId] || [];
    
    history.forEach(msg => {
        // Xác định loại tin nhắn (của mình hay của họ)
        const type = (msg.sender === currentUser) ? 'sent' : 'received';
        appendMessageToUI(msg.sender, msg.message, type);
    });
}

// 4. Gửi tin nhắn
async function sendMessage() {
    const input = document.getElementById('msg-input');
    const messageText = input.value.trim();

    if (!messageText) return; 
    if (!currentTarget) {
        alert("Vui lòng chọn một người để chat!");
        return;
    }

    // 1. Lưu tin nhắn gửi đi vào lịch sử của mình
    if (!chatHistory[currentTarget]) chatHistory[currentTarget] = [];
    chatHistory[currentTarget].push({
        sender: currentUser,
        message: messageText
    });

    // 2. Hiển thị lên màn hình ngay
    appendMessageToUI(currentUser, messageText, 'sent');

    // 3. Gửi lên Server
    try {
        const response = await fetch('/send-peer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                peer_id: currentUser,
                target: currentTarget,
                message: messageText
            })
        });

        if (response.ok) {
            input.value = ''; 
        } else {
            alert("Lỗi gửi tin!");
        }
    } catch (error) { console.error(error); }
}

// 5. NHẬN TIN NHẮN (Đã nâng cấp logic phân loại)
async function fetchMessages() {
    try {
        const response = await fetch('/get-messages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ peer_id: currentUser })
        });

        if (response.ok) {
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(msg => {
                    const sender = msg.sender;
                    
                    // 1. Lưu tin nhắn vào lịch sử (dù đang chat hay không)
                    if (!chatHistory[sender]) chatHistory[sender] = [];
                    chatHistory[sender].push({
                        sender: sender,
                        message: msg.message
                    });

                    // 2. Chỉ hiển thị nếu ĐANG MỞ khung chat với người đó
                    if (currentTarget === sender) {
                        appendMessageToUI(sender, msg.message, 'received');
                    } else {
                        // Nếu không, có thể báo hiệu tin nhắn mới (console log hoặc UI effect)
                        console.log(`Có tin nhắn mới từ ${sender} nhưng đang ẩn.`);
                    }
                });
            }
        }
    } catch (error) { console.error("Lỗi nhận tin:", error); }
}

// Hàm UI thuần túy: Vẽ 1 tin nhắn lên màn hình
function appendMessageToUI(sender, text, type) {
    const msgWindow = document.getElementById('message-window');
    if (!msgWindow) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    
    msgDiv.innerHTML = `
        <div class="msg-sender">${sender}</div>
        <div class="msg-content">${text}</div>
    `;
    
    msgWindow.appendChild(msgDiv);
    msgWindow.scrollTop = msgWindow.scrollHeight;
}