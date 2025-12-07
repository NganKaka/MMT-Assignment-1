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








// juan 100%

// let currentUser = null;
// let currentTarget = null;
// // Biến lưu trữ lịch sử chat của từng người
// let chatHistory = {}; 

// function startChatApp(user) {
//     currentUser = user;
//     console.log("Logged in as:", currentUser);
    
//     // Cập nhật danh sách online (3 giây/lần)
//     fetchPeerList();
//     setInterval(fetchPeerList, 3000);

//     // Polling tin nhắn mới (2 giây/lần)
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

// // 2. Render danh sách Peer
// function renderPeerList(peers) {
//     const listElement = document.getElementById('peer-list');
//     if (!listElement) return;

//     // Lưu lại trạng thái user đang chọn để không bị mất focus khi re-render
//     const savedTarget = currentTarget;

//     listElement.innerHTML = ''; 

//     if (!peers || peers.length === 0) {
//         listElement.innerHTML = '<li style="color: gray; padding: 10px;">Chưa có ai online...</li>';
//         return;
//     }

//     peers.forEach(peer => {
//         const li = document.createElement('li');
//         li.className = 'peer-item';
//         li.innerText = `${peer.peer_id} (${peer.ip}:${peer.port})`;
        
//         // Highlight người đang được chọn
//         if (savedTarget === peer.peer_id) li.classList.add('active');

//         // Kiểm tra xem người này có tin nhắn chưa đọc không (Optional UX)
//         if (chatHistory[peer.peer_id] && peer.peer_id !== savedTarget) {
//             // Logic hiển thị thông báo tin nhắn mới có thể thêm ở đây
//             // li.style.fontWeight = "bold"; 
//         }

//         li.onclick = () => {
//             // 1. Đổi người target
//             currentTarget = peer.peer_id;
            
//             // 2. Cập nhật UI Header
//             document.querySelector('.system-msg').innerText = `Đang chat với: ${currentTarget}`;
            
//             // 3. Highlight lại danh sách
//             renderPeerList(peers); 

//             // 4. QUAN TRỌNG: Load lại lịch sử chat của người này ra màn hình
//             loadChatHistory(currentTarget);
//         };
//         listElement.appendChild(li);
//     });
// }

// // 3. Hàm Load lịch sử chat ra màn hình (MỚI)
// function loadChatHistory(peerId) {
//     const msgWindow = document.getElementById('message-window');
//     msgWindow.innerHTML = `<div class="system-msg">Đang chat với: ${peerId}</div>`;

//     // Lấy tin nhắn từ bộ nhớ đệm
//     const history = chatHistory[peerId] || [];
    
//     history.forEach(msg => {
//         // Xác định loại tin nhắn (của mình hay của họ)
//         const type = (msg.sender === currentUser) ? 'sent' : 'received';
//         appendMessageToUI(msg.sender, msg.message, type);
//     });
// }

// // 4. Gửi tin nhắn
// async function sendMessage() {
//     const input = document.getElementById('msg-input');
//     const messageText = input.value.trim();

//     if (!messageText) return; 
//     if (!currentTarget) {
//         alert("Vui lòng chọn một người để chat!");
//         return;
//     }

//     // 1. Lưu tin nhắn gửi đi vào lịch sử của mình
//     if (!chatHistory[currentTarget]) chatHistory[currentTarget] = [];
//     chatHistory[currentTarget].push({
//         sender: currentUser,
//         message: messageText
//     });

//     // 2. Hiển thị lên màn hình ngay
//     appendMessageToUI(currentUser, messageText, 'sent');

//     // 3. Gửi lên Server
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

// // 5. NHẬN TIN NHẮN (Đã nâng cấp logic phân loại)
// async function fetchMessages() {
//     try {
//         const response = await fetch('/get-messages', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ peer_id: currentUser })
//         });

//         if (response.ok) {
//             const data = await response.json();
            
//             if (data.messages && data.messages.length > 0) {
//                 data.messages.forEach(msg => {
//                     const sender = msg.sender;
                    
//                     // 1. Lưu tin nhắn vào lịch sử (dù đang chat hay không)
//                     if (!chatHistory[sender]) chatHistory[sender] = [];
//                     chatHistory[sender].push({
//                         sender: sender,
//                         message: msg.message
//                     });

//                     // 2. Chỉ hiển thị nếu ĐANG MỞ khung chat với người đó
//                     if (currentTarget === sender) {
//                         appendMessageToUI(sender, msg.message, 'received');
//                     } else {
//                         // Nếu không, có thể báo hiệu tin nhắn mới (console log hoặc UI effect)
//                         console.log(`Có tin nhắn mới từ ${sender} nhưng đang ẩn.`);
//                     }
//                 });
//             }
//         }
//     } catch (error) { console.error("Lỗi nhận tin:", error); }
// }

// // Hàm UI thuần túy: Vẽ 1 tin nhắn lên màn hình
// function appendMessageToUI(sender, text, type) {
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


















































// let currentUser = null;
// let currentTarget = null;
// let chatHistory = {}; 
// // --- NEW: Biến lưu số lượng tin nhắn chưa đọc ---
// let unreadCounts = {}; 

// function startChatApp(user) {
//     currentUser = user;
//     console.log("Logged in as:", currentUser);
    
//     fetchPeerList();
//     setInterval(fetchPeerList, 3000);

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

// // 2. Render danh sách Peer
// function renderPeerList(peers) {
//     const listElement = document.getElementById('peer-list');
//     if (!listElement) return;

//     const savedTarget = currentTarget;
//     listElement.innerHTML = ''; 

//     if (!peers || peers.length === 0) {
//         listElement.innerHTML = '<li style="color: gray; padding: 10px;">Chưa có ai online...</li>';
//         return;
//     }

//     peers.forEach(peer => {
//         const li = document.createElement('li');
//         li.className = 'peer-item';
        
//         // --- NEW: Hiển thị tên kèm số lượng tin chưa đọc (nếu có) ---
//         const count = unreadCounts[peer.peer_id] || 0;
//         if (count > 0) {
//             li.classList.add('has-unread'); // Thêm class CSS đỏ
//             li.innerText = `${peer.peer_id} (${count})`; // Hiển thị số lượng
//         } else {
//             li.innerText = `${peer.peer_id}`; // Hiển thị bình thường
//         }
        
//         // Highlight người đang chọn
//         if (savedTarget === peer.peer_id) li.classList.add('active');

//         li.onclick = () => {
//             currentTarget = peer.peer_id;
            
//             // --- NEW: Reset tin chưa đọc về 0 khi bấm vào xem ---
//             unreadCounts[currentTarget] = 0; 
            
//             document.querySelector('.system-msg').innerText = `Đang chat với: ${currentTarget}`;
//             renderPeerList(peers); // Render lại để mất dấu đỏ
//             loadChatHistory(currentTarget);
//         };
//         listElement.appendChild(li);
//     });
// }

// // 3. Hàm Load lịch sử
// function loadChatHistory(peerId) {
//     const msgWindow = document.getElementById('message-window');
//     msgWindow.innerHTML = `<div class="system-msg">Đang chat với: ${peerId}</div>`;

//     const history = chatHistory[peerId] || [];
//     history.forEach(msg => {
//         const type = (msg.sender === currentUser) ? 'sent' : 'received';
//         appendMessageToUI(msg.sender, msg.message, type);
//     });
// }

// // 4. Gửi tin nhắn
// async function sendMessage() {
//     const input = document.getElementById('msg-input');
//     const messageText = input.value.trim();

//     if (!messageText) return; 
//     if (!currentTarget) {
//         alert("Vui lòng chọn một người để chat!");
//         return;
//     }

//     if (!chatHistory[currentTarget]) chatHistory[currentTarget] = [];
//     chatHistory[currentTarget].push({
//         sender: currentUser,
//         message: messageText
//     });

//     appendMessageToUI(currentUser, messageText, 'sent');

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

// // 5. NHẬN TIN NHẮN
// async function fetchMessages() {
//     try {
//         const response = await fetch('/get-messages', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ peer_id: currentUser })
//         });

//         if (response.ok) {
//             const data = await response.json();
            
//             if (data.messages && data.messages.length > 0) {
//                 // Có tin nhắn mới! Play âm thanh nếu muốn (optional)
//                 // const audio = new Audio('notification.mp3'); audio.play();

//                 data.messages.forEach(msg => {
//                     const sender = msg.sender;
                    
//                     if (!chatHistory[sender]) chatHistory[sender] = [];
//                     chatHistory[sender].push({
//                         sender: sender,
//                         message: msg.message
//                     });

//                     // Nếu đang mở chat với người này -> Hiện lên
//                     if (currentTarget === sender) {
//                         appendMessageToUI(sender, msg.message, 'received');
//                     } else {
//                         // --- NEW: Nếu đang không xem -> Tăng biến đếm chưa đọc ---
//                         if (!unreadCounts[sender]) unreadCounts[sender] = 0;
//                         unreadCounts[sender]++;
//                         // Gọi render để hiện dấu đỏ ngay lập tức
//                         // (Hoặc đợi 3s sau nó tự cập nhật theo setInterval)
//                         showToast(`📩 ${sender}: ${msg.message}`);
//                     }
//                 });
//             }
//         }
//     } catch (error) { console.error("Lỗi nhận tin:", error); }
// }

// function appendMessageToUI(sender, text, type) {
//     const msgWindow = document.getElementById('message-window');
//     if (!msgWindow) return;

//     const msgDiv = document.createElement('div');
//     msgDiv.className = `message ${type}`;
//     msgDiv.innerHTML = `<div class="msg-sender">${sender}</div><div class="msg-content">${text}</div>`;
//     msgWindow.appendChild(msgDiv);
//     msgWindow.scrollTop = msgWindow.scrollHeight;
// }


// function showToast(message) {
//     // Tạo thẻ div cho thông báo
//     const toast = document.createElement("div");
//     toast.innerText = message;
//     toast.style.position = "fixed";
//     toast.style.top = "20px";
//     toast.style.right = "20px";
//     toast.style.background = "#333";
//     toast.style.color = "#fff";
//     toast.style.padding = "10px 20px";
//     toast.style.borderRadius = "5px";
//     toast.style.boxShadow = "0 2px 5px rgba(0,0,0,0.3)";
//     toast.style.zIndex = "1000";
//     toast.style.transition = "opacity 0.5s";

//     document.body.appendChild(toast);

//     // Tự động tắt sau 3 giây
//     setTimeout(() => {
//         toast.style.opacity = "0";
//         setTimeout(() => document.body.removeChild(toast), 500);
//     }, 3000);
// }

















// let currentUser = null;
// let currentTarget = null;
// let currentType = null; // 'direct' hoặc 'channel'
// let chatHistory = {}; 
// let unreadCounts = {}; 

// function startChatApp(user) {
//     currentUser = user;
//     console.log("Logged in as:", currentUser);
    
//     loadHistoryFromLocal();
//     // Mặc định vào kênh General
//     switchChat('General', 'channel');

//     fetchPeerList();
//     setInterval(fetchPeerList, 3000);

//     fetchMessages();
//     setInterval(fetchMessages, 2000);
// }

// // 1. LẤY DANH SÁCH USER
// async function fetchPeerList() {
//     try {
//         // Dùng POST để tương thích code backend mới
//         const response = await fetch('/get-list', { 
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({}) 
//         });

//         if (response.ok) {
//             const data = await response.json();
//             // Backend trả về {status: "ok", peers: [...]}
//             if (data.peers) {
//                 renderPeerList(data.peers);
//             }
//         }
//     } catch (error) { console.error("Lỗi lấy peer:", error); }
// }

// function renderPeerList(peers) {
//     const listElement = document.getElementById('peer-list');
//     listElement.innerHTML = ''; 

//     peers.forEach(peer => {
//         // Không hiện bản thân
//         if(peer.name === currentUser) return;

//         const li = document.createElement('li');
//         li.className = 'peer-item';
        
//         // Notification
//         const count = unreadCounts[peer.name] || 0;
//         if (count > 0) {
//             li.classList.add('has-unread');
//             li.innerText = `${peer.name} (${count})`;
//         } else {
//             li.innerText = `${peer.name}`;
//         }

//         // Active state
//         if (currentTarget === peer.name && currentType === 'direct') {
//             li.classList.add('active');
//         }

//         li.onclick = () => {
//             switchChat(peer.name, 'direct');
//         };
//         listElement.appendChild(li);
//     });
// }

// // 2. CHUYỂN ĐỔI CHAT
// function switchChat(target, type) {
//     currentTarget = target;
//     currentType = type;
    
//     // Reset unread
//     unreadCounts[target] = 0;

//     // Highlight UI
//     // Reset active class
//     document.querySelectorAll('.peer-item, .channel-item').forEach(el => el.classList.remove('active'));
    
//     // Tìm element để add active (Chỉ là visual)
//     if (type === 'channel') {
//         const el = document.querySelector('.channel-item'); // General là cái đầu tiên
//         if(el) el.classList.add('active');
//     } else {
//         // Render lại peer list để cập nhật active class
//         // (Hoặc đợi 3s sau nó tự cập nhật)
//     }

//     const prefix = type === 'channel' ? '📢 Kênh: ' : '👤 Chat với: ';
//     document.querySelector('.system-msg').innerText = prefix + target;
    
//     loadChatHistory(target);
// }

// // 3. GỬI TIN NHẮN
// async function sendMessage() {
//     const input = document.getElementById('msg-input');
//     const messageText = input.value.trim();
//     if (!messageText || !currentTarget) return;

//     // Lưu vào lịch sử hiển thị
//     appendMessageToUI(currentUser, messageText, 'sent');
//     if (!chatHistory[currentTarget]) chatHistory[currentTarget] = [];
//     chatHistory[currentTarget].push({ sender: currentUser, msg: messageText });

//     saveHistoryToLocal(); 

//     const url = currentType === 'direct' ? '/send-peer' : '/broadcast-peer';
//     const body = {
//         sender: currentUser,
//         msg: messageText,
//         target: currentType === 'direct' ? currentTarget : undefined
//     };

//     try {
//         await fetch(url, {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify(body)
//         });
//         input.value = '';
//     } catch (error) { console.error(error); }
// }

// // 4. NHẬN TIN NHẮN
// async function fetchMessages() {
//     if (!currentUser) return;

//     try {
//         const response = await fetch('/get-messages', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ peer_id: currentUser }) 
//         });

//         if (response.ok) {
//             const data = await response.json();
            
//             if (data.messages && data.messages.length > 0) {
//                 data.messages.forEach(msg => {
//                     // Logic xử lý người gửi
//                     // Nếu là tin broadcast, server gửi: sender="General", msg="Hung: hello"
//                     // Nếu là tin direct, server gửi: sender="Hung", msg="hello"
                    
//                     const senderID = msg.sender; // "General" hoặc tên User
                    
//                     // Lưu lịch sử
//                     if (!chatHistory[senderID]) chatHistory[senderID] = [];
//                     chatHistory[senderID].push({
//                         sender: senderID, 
//                         msg: msg.message // Nội dung tin
//                     });

//                     saveHistoryToLocal();

//                     // Nếu đang xem đúng người đó -> Hiện lên
//                     if (currentTarget === senderID) {
//                         appendMessageToUI(senderID, msg.message, 'received');
//                     } else {
//                         // Thông báo
//                         if (!unreadCounts[senderID]) unreadCounts[senderID] = 0;
//                         unreadCounts[senderID]++;
                        
//                         // Nếu là tin nhắn từ Peer, cần update list để hiện dấu đỏ
//                         if (senderID !== 'General') fetchPeerList();
                        
//                         // Toast
//                         showToast(`📩 Tin mới từ ${senderID}`);
//                     }
//                 });
//             }
//         }
//     } catch (error) { console.error("Lỗi polling:", error); }
// }

// function loadChatHistory(target) {
//     const msgWindow = document.getElementById('message-window');
//     msgWindow.innerHTML = `<div class="system-msg">${currentType === 'channel' ? '📢' : '👤'} ${target}</div>`;
    
//     const history = chatHistory[target] || [];
//     history.forEach(m => {
//         const type = m.sender === currentUser ? 'sent' : 'received';
//         appendMessageToUI(m.sender, m.msg, type);
//     });
// }

// function appendMessageToUI(sender, text, type) {
//     const msgWindow = document.getElementById('message-window');
//     const msgDiv = document.createElement('div');
//     msgDiv.className = `message ${type}`;
    
//     // Nếu là 'sent' (mình gửi), không cần hiện tên
//     // Nếu là 'received' (nhận):
//     // - Nếu đang chat kênh General: sender là "General", text là "Hung: hello" -> Hiện text là đủ
//     // - Nếu chat riêng: sender là "Hung" -> Hiện tên người gửi
    
//     let contentHTML = `<div class="msg-content">${text}</div>`;
//     if (type === 'received' && currentType === 'direct') {
//         contentHTML = `<div class="msg-sender">${sender}</div>` + contentHTML;
//     }
    
//     msgDiv.innerHTML = contentHTML;
//     msgWindow.appendChild(msgDiv);
//     msgWindow.scrollTop = msgWindow.scrollHeight;
// }

// function showToast(message) {
//     const toast = document.createElement("div");
//     toast.innerText = message;
//     toast.style.position = "fixed"; top = "20px"; right = "20px";
//     toast.style.cssText = "position:fixed; top:20px; right:20px; background:#333; color:#fff; padding:10px 20px; border-radius:5px; z-index:9999;";
//     document.body.appendChild(toast);
//     setTimeout(() => { document.body.removeChild(toast); }, 3000);
// }



// function saveHistoryToLocal() {
//     if (!currentUser) return;
//     // Lưu lịch sử chat gắn liền với tên người dùng hiện tại
//     // Để tránh việc đăng nhập nick khác lại thấy tin nhắn của nick cũ
//     localStorage.setItem(`history_${currentUser}`, JSON.stringify(chatHistory));
// }

// function loadHistoryFromLocal() {
//     if (!currentUser) return;
//     const saved = localStorage.getItem(`history_${currentUser}`);
//     if (saved) {
//         chatHistory = JSON.parse(saved);
//     }
// }







let currentUser = null;
let currentTarget = null;
let currentType = null; // 'direct' hoặc 'channel'
let chatHistory = {}; 
let unreadCounts = {}; 

function startChatApp(user) {
    currentUser = user;
    console.log("Logged in as:", currentUser);
    
    loadHistoryFromLocal();
    
    // Auto join channel list
    fetchData();
    setInterval(fetchData, 3000);

    fetchMessages();
    setInterval(fetchMessages, 2000);
}

async function fetchData() {
    fetchPeerList();
    fetchChannelList();
}

// --- XỬ LÝ PEER ---
async function fetchPeerList() {
    try {
        const response = await fetch('/get-list', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}) 
        });
        if (response.ok) {
            const data = await response.json();
            renderPeerList(data.peers);
        }
    } catch (e) {}
}

function renderPeerList(peers) {
    const listElement = document.getElementById('peer-list');
    listElement.innerHTML = ''; 
    peers.forEach(peer => {
        if(peer.name === currentUser) return;
        const li = document.createElement('li');
        li.className = 'item-list peer-icon';
        
        const count = unreadCounts[peer.name] || 0;
        if (count > 0) { li.classList.add('has-unread'); li.innerText = `${peer.name} (${count})`; }
        else { li.innerText = peer.name; }

        if (currentTarget === peer.name && currentType === 'direct') li.classList.add('active');

        li.onclick = () => switchChat(peer.name, 'direct');
        listElement.appendChild(li);
    });
}

// --- XỬ LÝ CHANNEL ---
async function joinChannel() {
    const name = document.getElementById('new-channel-name').value.trim();
    if (!name) return;
    try {
        const response = await fetch('/add-list', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ channel: name, username: currentUser })
        });
        if (response.ok) {
            document.getElementById('new-channel-name').value = '';
            fetchChannelList();
            alert(`Đã tham gia: ${name}`);
        }
    } catch (e) { console.error(e); }
}

async function fetchChannelList() {
    try {
        const response = await fetch('/get-channels', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ peer_id: currentUser })
        });
        if (response.ok) {
            const data = await response.json();
            renderChannelList(data.channels);
        }
    } catch (e) {}
}

function renderChannelList(channels) {
    const listElement = document.getElementById('channel-list');
    listElement.innerHTML = '';
    channels.forEach(ch => {
        const li = document.createElement('li');
        li.className = 'item-list channel-icon';
        
        // Check unread cho channel (nếu muốn)
        const count = unreadCounts[ch] || 0;
        if (count > 0) li.innerText = `${ch} (${count})`;
        else li.innerText = ch;

        if (currentTarget === ch && currentType === 'channel') li.classList.add('active');
        li.onclick = () => switchChat(ch, 'channel');
        listElement.appendChild(li);
    });
}

// --- CHUYỂN ĐỔI ---
function switchChat(target, type) {
    currentTarget = target;
    currentType = type;
    unreadCounts[target] = 0; // Reset unread
    
    // Update UI
    fetchData(); 
    document.querySelector('.system-msg').innerText = 
        (type === 'channel' ? '📢 ' : '👤 ') + target;
    loadChatHistory(target);
}

// --- GỬI TIN NHẮN ---
async function sendMessage() {
    const input = document.getElementById('msg-input');
    const msg = input.value.trim();
    if (!msg || !currentTarget) return;

    // Lưu history
    appendMessageToUI(currentUser, msg, 'sent');
    if (!chatHistory[currentTarget]) chatHistory[currentTarget] = [];
    chatHistory[currentTarget].push({ sender: currentUser, msg: msg });
    saveHistoryToLocal();

    const url = currentType === 'direct' ? '/send-peer' : '/broadcast-peer';
    const body = {
        sender: currentUser,
        msg: msg,
        target: currentType === 'direct' ? currentTarget : undefined,
        channel: currentType === 'channel' ? currentTarget : undefined
    };

    try {
        await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        input.value = '';
    } catch (e) {}
}

// --- NHẬN TIN NHẮN ---
async function fetchMessages() {
    if (!currentUser) return;
    try {
        const response = await fetch('/get-messages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ peer_id: currentUser })
        });
        if (response.ok) {
            const data = await response.json();
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(m => {
                    const senderID = m.sender; // Tên người gửi hoặc tên Kênh
                    
                    if (!chatHistory[senderID]) chatHistory[senderID] = [];
                    chatHistory[senderID].push({ sender: senderID, msg: m.message });
                    saveHistoryToLocal();

                    if (currentTarget === senderID) {
                        appendMessageToUI(senderID, m.message, 'received');
                    } else {
                        if (!unreadCounts[senderID]) unreadCounts[senderID] = 0;
                        unreadCounts[senderID]++;
                        fetchData();
                        showToast(`📩 ${senderID}: ${m.message}`);
                    }
                });
            }
        }
    } catch (e) {}
}

// --- HELPER UI & STORAGE ---
function loadChatHistory(target) {
    const msgWindow = document.getElementById('message-window');
    msgWindow.innerHTML = `<div class="system-msg">${currentType === 'channel' ? '📢' : '👤'} ${target}</div>`;
    const list = chatHistory[target] || [];
    list.forEach(item => {
        const type = item.sender === currentUser ? 'sent' : 'received';
        appendMessageToUI(item.sender, item.msg, type);
    });
}

function appendMessageToUI(sender, text, type) {
    const msgWindow = document.getElementById('message-window');
    const div = document.createElement('div');
    div.className = `message ${type}`;
    
    let html = `<div class="msg-content">${text}</div>`;
    // Nếu là tin nhận được và là chat riêng, hiện tên người gửi
    // Nếu chat kênh, sender chính là tên kênh -> trong content text đã có "Hung: hello"
    if (type === 'received' && currentType === 'direct') {
        html = `<div class="msg-sender">${sender}</div>` + html;
    }
    div.innerHTML = html;
    msgWindow.appendChild(div);
    msgWindow.scrollTop = msgWindow.scrollHeight;
}

function saveHistoryToLocal() {
    if (currentUser) localStorage.setItem(`hist_${currentUser}`, JSON.stringify(chatHistory));
}
function loadHistoryFromLocal() {
    if (currentUser) {
        const s = localStorage.getItem(`hist_${currentUser}`);
        if (s) chatHistory = JSON.parse(s);
    }
}
function showToast(msg) {
    const d = document.createElement("div");
    d.innerText = msg;
    d.style.cssText = "position:fixed;top:20px;right:20px;background:#333;color:#fff;padding:10px;border-radius:5px;z-index:999";
    document.body.appendChild(d);
    setTimeout(() => document.body.removeChild(d), 3000);
}