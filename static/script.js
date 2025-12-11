let currentUser = null;
let currentTarget = null;
let currentType = null;
let chatHistory = {}; 
let unreadCounts = {}; 

function startChatApp(user) {
    currentUser = user;
    console.log("Logged in as:", currentUser);
    
    loadHistoryFromLocal();
    
    // Auto join channel list
    // fetchData();
    // setInterval(fetchData, 3000);

    // fetchMessages();
    // setInterval(fetchMessages, 2000);
    fetchLists();
    fetchMessages();

    setInterval(fetchLists, 3000);
    setInterval(fetchMessages, 2000);
}

// async function fetchData() {
//     fetchPeerList();
//     fetchChannelList();
// }
async function fetchLists() {
    fetchPeerList();
    fetchChannelList();
}

// --- XỬ LÝ PEER ---
async function fetchPeerList() {
    try {
        const res = await fetch("/get-list");
        if (!res.ok) return;
        const peers = await res.json();

        renderPeerList(peers);
    } catch (e) {}
}

function renderPeerList(list) {
    const ul = document.getElementById("peer-list");
    ul.innerHTML = "";

    list.forEach(peer => {
        if (peer.name === currentUser) return;

        const directKey = makeDirectKey(currentUser, peer.name);
        const unread = unreadCounts[directKey] || 0;

        const li = document.createElement("li");
        li.className = "item-list peer-icon";

        li.innerText = unread > 0 ? `${peer.name} (${unread})` : peer.name;

        const isActive =
            currentType === "direct" &&
            currentTarget === peer.name;
        if (isActive) li.classList.add("active");

        li.onclick = () => switchChat(peer.name, "direct");

        ul.appendChild(li);
    });
}

// async function fetchPeerList() {
//     try {
//         const response = await fetch('/get-list') 
//         //     { 
//         //     method: 'GET' 
//         //     // headers: { 'Content-Type': 'application/json' },
//         //     // body: JSON.stringify({}) 
//         // });
//         if (response.ok) {
//             const data = await response.json();
//             const peers = Array.isArray(data) ? data : (data.peers || []);
//             renderPeerList(peers);
//         }
//     } catch (e) {}
// }

// function renderPeerList(peers) {
//     const listElement = document.getElementById('peer-list');
//     listElement.innerHTML = ''; 
//     peers.forEach(peer => {
//         if(peer.name === currentUser) return;
//         const li = document.createElement('li');
//         li.className = 'item-list peer-icon';
        
//         const count = unreadCounts[peer.name] || 0;
//         if (count > 0) { li.classList.add('has-unread'); li.innerText = `${peer.name} (${count})`; }
//         else { li.innerText = peer.name; }

//         if (currentTarget === peer.name && currentType === 'direct') li.classList.add('active');

//         li.onclick = () => switchChat(peer.name, 'direct');
//         listElement.appendChild(li);
//     });
// }

// --- XỬ LÝ CHANNEL ---
// async function joinChannel() {
//     const name = document.getElementById('new-channel-name').value.trim();
//     if (!name) return;
//     try {
//         const response = await fetch('/add-list', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ channel: name, username: currentUser })
//         });
//         if (response.ok) {
//             document.getElementById('new-channel-name').value = '';
//             fetchChannelList();
//             alert(`Đã tham gia: ${name}`);
//         }
//     } catch (e) { console.error(e); }
// }
async function joinChannel() {
    const name = document.getElementById('new-channel-name').value.trim();
    if (!name) return;

    const peer = {
        name: currentUser,
        ip: localStorage.getItem("peer_ip"),
        port: localStorage.getItem("peer_port")
    };

    try {
        const response = await fetch('/add-list', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                channel: name, 
                peer: peer                // ✅ ĐÚNG CHUẨN BACKEND
            })
        });

        const data = await response.json();
        if (data.status === "ok") {
            document.getElementById('new-channel-name').value = "";
            fetchChannelList();
            alert("Đã tham gia kênh: " + name);
        }
    } catch (e) {
        console.error(e);
    }
}


async function fetchChannelList() {
    try {
        // const response = await fetch(`/get-channels?peer_id=${currentUser}`); 
        //     {
        //     // method: 'GET'
        //     // headers: { 'Content-Type': 'application/json' },
        //     // body: JSON.stringify({ peer_id: currentUser })
        // });
        const response = await fetch("/get-channels");

        if (response.ok) {
            const data = await response.json();
            const list = Object.keys(data)
            renderChannelList(list);
        }
    } catch (e) {}
}

// function renderChannelList(channels) {
//     const listElement = document.getElementById('channel-list');
//     listElement.innerHTML = '';
//     channels.forEach(ch => {
//         const li = document.createElement('li');
//         li.className = 'item-list channel-icon';
        
//         // Check unread cho channel (nếu muốn)
//         const count = unreadCounts[ch] || 0;
//         if (count > 0) li.innerText = `${ch} (${count})`;
//         else li.innerText = ch;

//         if (currentTarget === ch && currentType === 'channel') li.classList.add('active');
//         li.onclick = () => switchChat(ch, 'channel');
//         listElement.appendChild(li);
//     });
// }


function renderChannelList(channels) {
    const ul = document.getElementById("channel-list");
    ul.innerHTML = "";

    channels.forEach(ch => {
        const unread = unreadCounts[ch] || 0;

        const li = document.createElement("li");
        li.className = "item-list channel-icon";

        li.innerText = unread > 0 ? `${ch} (${unread})` : ch;

        if (currentType === "channel" && currentTarget === ch)
            li.classList.add("active");

        li.onclick = () => switchChat(ch, "channel");

        ul.appendChild(li);
    });
}
// function renderChannelList(channels) {
//     const listElement = document.getElementById('channel-list');
//     listElement.innerHTML = '';

//     channels.forEach(ch => {
//         const li = document.createElement('li');
//         li.className = 'item-list channel-icon';

//         const count = unreadCounts[ch] || 0;
//         li.innerText = count > 0 ? `${ch} (${count})` : ch;

//         if (currentTarget === ch && currentType === 'channel')
//             li.classList.add('active');

//         li.onclick = () => switchChat(ch, 'channel');
//         listElement.appendChild(li);
//     });
// }


// --- CHUYỂN ĐỔI ---
// function switchChat(target, type) {
//     currentTarget = target;
//     currentType = type;

//     const key = (type === "direct")
//         ? makeDirectKey(currentUser, target)
//         : target;

//     unreadCounts[key] = 0;

//     document.querySelector(".system-msg").innerText =
//         (type === "channel" ? "📢 " : "👤 ") + target;

//     loadChatHistory(key);
// }
function switchChat(target, type) {
    currentTarget = target;
    currentType = type;

    // Reset unread count
    const key = type === "direct"
        ? makeDirectKey(currentUser, target)
        : target;

    unreadCounts[key] = 0;

    renderLists();

    fetchMessages();
}


// function switchChat(target, type) {
//     currentTarget = target;
//     currentType = type;
//     unreadCounts[target] = 0; // Reset unread
    
//     // Update UI
//     fetchData(); 
//     document.querySelector('.system-msg').innerText = 
//         (type === 'channel' ? '📢 ' : '👤 ') + target;
//     loadChatHistory(target);
// }

// --- GỬI TIN NHẮN ---
async function sendMessage() {
    const input = document.getElementById("msg-input");
    const msg = input.value.trim();
    if (!msg || !currentTarget) return;

    const directKey = makeDirectKey(currentUser, currentTarget);
    const storageKey = currentType === "direct" ? directKey : currentTarget;

    appendMessageToUI(currentUser, msg, "sent");

    if (!chatHistory[storageKey]) chatHistory[storageKey] = [];
    chatHistory[storageKey].push({ sender: currentUser, msg });
    saveHistoryToLocal();

    const body = {
        sender: currentUser,
        msg
    };

    let url = "";

    if (currentType === "direct") {
        url = "/send-peer";
        body.target = currentTarget;
    } else {
        url = "/broadcast-peer";
        body.channel = currentTarget;
    }

    try {
        await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        input.value = "";
    } catch (e) {}
}
// async function sendMessage() {
//     const input = document.getElementById('msg-input');
//     const msg = input.value.trim();
//     if (!msg || !currentTarget) return;

//     // Lưu history
//     appendMessageToUI(currentUser, msg, 'sent');
//     if (!chatHistory[currentTarget]) chatHistory[currentTarget] = [];
//     chatHistory[currentTarget].push({ sender: currentUser, msg: msg });
//     saveHistoryToLocal();

//     const url = currentType === 'direct' ? '/send-peer' : '/broadcast-peer';
//     const body = {
//         sender: currentUser,
//         msg: msg,
//         target: currentType === 'direct' ? currentTarget : undefined,
//         channel: currentType === 'channel' ? currentTarget : undefined
//     };

//     try {
//         await fetch(url, {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify(body)
//         });
//         input.value = '';
//     } catch (e) {}
// }

// --- NHẬN TIN NHẮN ---
// async function fetchMessages() {
//     if (!currentUser) return;
//     try {
//         // const response = await fetch(`/get-messages?peer_id=${currentUser}`); 
//         //     {
//         //     method: 'GET'
//         //     // headers: { 'Content-Type': 'application/json' },
//         //     // body: JSON.stringify({ peer_id: currentUser })
//         // });
//         const response = await fetch("/get-messages");

//         if (response.ok) {
//             const data = await response.json();
//             if (data.messages && data.messages.length > 0) {
//                 data.messages.forEach(m => {
//                     const senderID = m.sender; // Tên người gửi hoặc tên Kênh
                    
//                     if (!chatHistory[senderID]) chatHistory[senderID] = [];
//                     chatHistory[senderID].push({ sender: senderID, msg: m.message });
//                     saveHistoryToLocal();

//                     if (currentTarget === senderID) {
//                         appendMessageToUI(senderID, m.message, 'received');
//                     } else {
//                         if (!unreadCounts[senderID]) unreadCounts[senderID] = 0;
//                         unreadCounts[senderID]++;
//                         fetchData();
//                         showToast(`📩 ${senderID}: ${m.message}`);
//                     }
//                 });
//             }
//         }
//     } catch (e) {}
// }


// async function fetchMessages() {
//     if (!currentUser || !currentTarget || currentType !== 'channel') return;

//     try {
//         const response = await fetch(`/get-messages?channel=${currentTarget}`);

//         if (response.ok) {
//             const data = await response.json();

//             data.forEach(m => {
//                 if (!chatHistory[currentTarget])
//                     chatHistory[currentTarget] = [];

//                 chatHistory[currentTarget].push({
//                     sender: m.sender,
//                     msg: m.msg
//                 });

//                 saveHistoryToLocal();

//                 appendMessageToUI(m.sender, m.msg, 'received');
//             });
//         }
//     } catch (e) {}
// }

// async function fetchMessages() {
//     if (!currentUser) return;

//     try {
//         const response = await fetch(`/get-messages?peer_id=${currentUser}`);

//         if (!response.ok) return;

//         const data = await response.json();
//         if (!data.messages) return;

//         data.messages.forEach(m => {
//             const sender = m.sender;       // tên người gửi hoặc tên kênh
//             const message = m.message;

//             if (!chatHistory[sender]) chatHistory[sender] = [];
//             chatHistory[sender].push({ sender, msg: message });
//             saveHistoryToLocal();

//             if (currentTarget === sender) {
//                 appendMessageToUI(sender, message, 'received');
//             } else {
//                 if (!unreadCounts[sender]) unreadCounts[sender] = 0;
//                 unreadCounts[sender]++;
//                 fetchData();
//                 showToast(`📩 ${sender}: ${message}`);
//             }
//         });

//     } catch (e) {
//         console.error("fetchMessages error:", e);
//     }
// }

// async function fetchMessages() {
//     if (!currentUser) return;

//     try {
//         const response = await fetch(`/get-messages?peer_id=${currentUser}`);
//         if (!response.ok) return;

//         const data = await response.json();
//         if (!data.messages) return;

//         data.messages.forEach(m => {
//             const sender = m.sender;
//             const message = m.message;

//             if (!chatHistory[sender]) chatHistory[sender] = [];

//             // Check duplicate
//             const exists = chatHistory[sender].some(msgObj => msgObj.msg === message);
//             if (exists) return;

//             chatHistory[sender].push({ sender, msg: message });
//             saveHistoryToLocal();

//             if (currentTarget === sender) {
//                 appendMessageToUI(sender, message, 'received');
//             } else {
//                 if (!unreadCounts[sender]) unreadCounts[sender] = 0;
//                 unreadCounts[sender]++;
//                 fetchData();
//                 showToast(`📩 ${sender}: ${message}`);
//             }
//         });

//     } catch (e) {
//         console.error("fetchMessages error:", e);
//     }
// }

// async function fetchMessages() {
//     if (!currentUser) return;

//     try {
//         const res = await fetch(`/get-messages?peer_id=${currentUser}`);
//         if (!res.ok) return;

//         const data = await res.json();
//         if (!data.messages) return;

//         data.messages.forEach(m => {
//             const sender = m.sender;
//             const message = m.message;
//             const channel = m.channel;     // tracker format

//             let key;

//             const isDirect = channel.includes("__");

//             if (isDirect) {
//                 key = channel;
//             } else {
//                 key = channel;  // channel name
//             }

//             if (!chatHistory[key]) chatHistory[key] = [];

//             const isDuplicate = chatHistory[key].some(x => x.msg === message);
//             if (isDuplicate) return;

//             chatHistory[key].push({ sender, msg: message });
//             saveHistoryToLocal();

//             // UI display
//             const shouldShow =
//                 (currentType === "direct" && key === makeDirectKey(currentUser, currentTarget)) ||
//                 (currentType === "channel" && key === currentTarget);

//             if (shouldShow) {
//                 appendMessageToUI(sender, message, "received");
//             } else {
//                 unreadCounts[key] = (unreadCounts[key] || 0) + 1;
//                 fetchLists();
//                 showToast(`📩 ${sender}: ${message}`);
//             }
//         });

//     } catch (e) {}
// }

async function fetchMessages() {
    if (!currentTarget || !currentType) return;

    let url = "/get-messages";

    if (currentType === "channel") {
        url += `?channel=${currentTarget}`;
    } else if (currentType === "direct") {
        url += `?peer_id=${currentUser}`;
    }

    const res = await fetch(url);
    const data = await res.json();

    renderMessages(data.messages);
}



// --- HELPER UI & STORAGE ---
// function loadChatHistory(target) {
//     const msgWindow = document.getElementById('message-window');
//     msgWindow.innerHTML = `<div class="system-msg">${currentType === 'channel' ? '📢' : '👤'} ${target}</div>`;
//     const list = chatHistory[target] || [];
//     list.forEach(item => {
//         const type = item.sender === currentUser ? 'sent' : 'received';
//         appendMessageToUI(item.sender, item.msg, type);
//     });
// }
function loadChatHistory(key) {
    const msgWindow = document.getElementById("message-window");
    msgWindow.innerHTML = "";

    const list = chatHistory[key] || [];
    list.forEach(item => {
        const type = item.sender === currentUser ? "sent" : "received";
        appendMessageToUI(item.sender, item.msg, type);
    });
}

// function appendMessageToUI(sender, text, type) {
//     const msgWindow = document.getElementById('message-window');
//     const div = document.createElement('div');
//     div.className = `message ${type}`;
    
//     let html = `<div class="msg-content">${text}</div>`;
//     // Nếu là tin nhận được và là chat riêng, hiện tên người gửi
//     // Nếu chat kênh, sender chính là tên kênh -> trong content text đã có "Hung: hello"
//     if (type === 'received' && currentType === 'direct') {
//         html = `<div class="msg-sender">${sender}</div>` + html;
//     }
//     div.innerHTML = html;
//     msgWindow.appendChild(div);
//     msgWindow.scrollTop = msgWindow.scrollHeight;
// }

function appendMessageToUI(sender, text, type) {
    const msgWindow = document.getElementById("message-window");

    const div = document.createElement("div");
    div.className = `message ${type}`;

    if (type === "received" && currentType === "direct") {
        div.innerHTML = `<div class="msg-sender">${sender}</div><div class="msg-content">${text}</div>`;
    } else {
        div.innerHTML = `<div class="msg-content">${text}</div>`;
    }

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

/* ========================
      HELPER
======================== */

function makeDirectKey(a, b) {
    return [a, b].sort().join("__");
}