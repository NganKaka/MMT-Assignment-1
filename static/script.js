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