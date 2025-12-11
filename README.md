# Computer Networks - Assignment 1
## Implement HTTP Server and Hybrid Chat Application

**Course:** CO3094 - Computer Networks  
**Lecturer:** Mr. Nguyễn Phương Duy  
**Class:** CC05  

---

## 👥 Team Members

| No. | Full Name | Student ID | Class | Email |
| :-: | :--- | :--- | :-: | :--- |
| 1 | Nguyễn Minh Hưng | 2352436 | CC05 | hung.nguyen565@hcmut.edu.vn |
| 2 | Nguyễn Hữu Minh Khôi | 2352614 | CC05 | khoi.nguyenhuuminh@hcmut.edu.vn |
| 3 | Đàm Hoài An | 2352002 | CC05 | an.damdha0623@hcmut.edu.vn |
| 4 | Võ Hoàng Ngân | 2353373 | CC05 | ngan.vo08052005@hcmut.edu.vn |

---

## 📝 Project Overview

This project is a comprehensive implementation of core networking concepts using Python. It demonstrates the understanding of:
* **Client-Server Paradigm:** Building a custom HTTP server from scratch using TCP sockets.
* **Peer-to-Peer (P2P) Paradigm:** Developing a chat application where clients communicate directly.
* **Protocol Design:** Handling HTTP Request/Response parsing, Header management, and Session Cookies.

### Key Features
* **Multi-threaded Server:** Handles multiple concurrent client connections.
* **Cookie-based Authentication:** Custom logic to issue and verify `auth=true` cookies.
* **Static File Serving:** Serves HTML, CSS, and Images correctly.
* **Custom Framework (WeApRous):** A Flask-like routing system using decorators (`@app.route`).

---

## 📁 Project Structure

The project is organized as follows:

```text
MMT-Assignment-1/
├── apps/                   # Directory for custom web applications
│   └── sampleApp.py        # Example usage of the framework
├── config/                 # Configuration files
│   └── proxy.conf          # Routing configuration for the Proxy server
├── daemon/                 # CORE LOGIC MODULES
│   ├── __init__.py         # Package initialization
│   ├── backend.py          # TCP Socket Server implementation (Multi-threading)
│   ├── httpadapter.py      # HTTP Logic Coordinator (Middleware)
│   ├── request.py          # HTTP Request Parser (Headers, Cookies, Body)
│   ├── response.py         # HTTP Response Builder (Content-Type, Status Codes)
│   ├── weaprous.py         # Mini-framework for Routing (@app.route)
│   ├── dictionary.py       # Case-Insensitive Dictionary helper
│   └── proxy.py            # Logic for the Proxy Server
├── static/                 # Static assets
│   ├── css/                # Stylesheets (styles.css)
│   ├── images/             # Images (favicon, etc.)
│   └── js/                 # Javascript files
├── www/                    # Web pages served by the backend
│   ├── index.html          # Protected Homepage
│   └── login.html          # Login Form
├── start_backend.py        # Script to start a simple Backend Server
├── start_proxy.py          # Script to start the Proxy Server
├── start_sampleapp.py      # MAIN ENTRY POINT (Runs Task 1 & 2 Logic)
└── README.md               # Project Documentation
```
## 🚀 How to Run & Test

### Prerequisites
* **Python 3.x** must be installed on your system.
* No external web frameworks (Flask, Django) are required.
* Ensure port `8000`, `8080`, `9001`, `9002` are free.

---

### 1️⃣ Run Task 1: HTTP Server & Authentication
This starts the central server which handles Admin Login (Cookie Session) and acts as the Tracker for the Chat App.

**Step 1: Start the Server**
Open a terminal and run:
```bash
python3 start_sampleapp.py --server-port 8000
```
**Step 2: Test Login (Cookie)**
Open a browser and navigate to **http://localhost:8000/login.html**

Login with Admin credentials: (Username: admin, Password: password)

You should be redirected to index.html. Check Developer Tools -> Application -> Cookies to see auth=true.
