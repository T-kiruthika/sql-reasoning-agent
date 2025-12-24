# SQLReasoning Agent (Agentic NL2SQL Database Assistant)

**DatabaseBot** is a sophisticated, interactive **Desktop AI Agent** that bridges the gap between natural language and complex relational databases. It allows users to query any SQL database through plain English—autonomously generating, validating, and executing SQL code without requiring technical expertise.

Originally developed during my **AI Internship (August 2025)** and later refined into a high-performance **Desktop Interface (October 2025)**, this project serves as a practical exploration of **Autonomous Agentic Workflows** and human–AI hybrid system design.

---

### 💡 Core Agentic Features

* 💬 **Natural Language Reasoning** – Interprets user intent to navigate complex database schemas autonomously.
* 🛠️ **Autonomous SQL Tool-Use** – Dynamically generates optimized SQL queries based on real-time schema inspection.
* ⚙️ **Multi-Dialect Support** – Seamlessly interfaces with **MySQL**, **PostgreSQL**, and **SQLite** using SQLAlchemy.
* 🪄 **Conversational State Management** – Features a reasoning memory that remembers session history for multi-turn follow-up queries.
* 💻 **Hybrid Desktop Architecture** – A robust local application built with **Flask + PyWebView**, combining web flexibility with desktop performance.
* 🤖 **AI-Assisted Engineering** – Developed using an **advanced AI-assisted workflow**, accelerating complex logic design and error-handling while maintaining manual architectural integrity.

---

### 🛠️ Tech Stack

| Layer                     | Tools / Technologies                            |
| ------------------------- | ----------------------------------------------- |
| **Interface**             | PyWebView, HTML5, CSS3, JavaScript              |
| **Backend Engine**        | Flask, SQLAlchemy, Flask-Session                |
| **Reasoning Model**       | Cohere Command-R (Optimized for RAG & Tool-Use) |
| **Database Connectivity** | MySQL, PostgreSQL, SQLite                       |
| **Runtime Environment**   | Python 3.x (Modular Desktop Execution)          |

---

### ⚙️ How It Works

1. **Initialize** – Launch via `python main.py` to open the secure desktop environment.
2. **Authenticate** – Securely connect to your local or remote database instance.
3. **Query** – Ask questions in plain English:

   * *“Show the top 10 customers by total purchase value this year.”*
   * *“What is the average employee salary grouped by department?”*
4. **Execute** – The Agent generates the SQL, performs the transaction, and renders a formatted data visualization instantly.

---

### 🗂️ Project Structure

```
databasebot-app/
│
├── main.py            # Desktop UI Controller (PyWebView + Flask Bridge)
├── server.py          # Core Reasoning Engine & AI Tool Integration
├── templates/         # Reactive Frontend Components
├── static/            # Styling & Client-side Logic
├── assets/            # Branding & Desktop Resources
├── requirements.txt   # Dependency Manifest
└── .env               # Secure Environment Configuration (API Keys)
```

---

### 🖼️ System Interface

| **Database Connection**                             | **Agentic Query Execution**                      |
| --------------------------------------------------- | ------------------------------------------------ |
| ![Database Connected](screenshots/db_connected.png) | ![AI Query Result](screenshots/query_result.png) |

---

### ⚙️ Installation & Deployment

```bash
# 1. Initialize Virtual Environment
python -m venv venv
source venv/bin/activate # (Use venv\Scripts\activate on Windows)

# 2. Install High-Performance Dependencies
pip install -r requirements.txt

# 3. Launch the Assistant
python main.py
```

For production deployment, the app can be compiled into a standalone executable:

```bash
pyinstaller --onefile --noconsole --name "DatabaseBot" main.py
```

---

### 🔒 Research Notes & Constraints

✅ **Efficiency:** Highly optimized for structured queries and real-time schema mapping.

⚙️ **Scalability:** For deep analytical reasoning or massive multi-join operations, the architecture is designed to scale with larger LLMs (e.g., Mistral/GPT-4) given sufficient hardware.

⚡ **Performance:** Currently optimized for low-latency interactions on mid-range hardware, making AI-driven data analysis accessible without enterprise-grade servers.

---

### 👩‍💻 Author

**Kiruthika T**
🎓 B.Tech in Artificial Intelligence & Data Science — Anna University
📍 Developed: August 2025 (Internship) → Refined: October 2025
🌐 Focus: AI-Driven Automation & Intelligent Relational Systems

---

### 🌟 Developer Note

This project was engineered using an AI-assisted workflow, utilizing AI as a "Co-Pilot" to accelerate testing, debugging, and boilerplate generation. However, the architectural design, security protocols, and model orchestration were manually directed. This project stands as a testament to the synergy between human design thinking and AI computational precision.
