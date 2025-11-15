🌐 Network Troubleshooting Bot — README

An intelligent, automated network troubleshooting system with real-time monitoring, AI-assisted diagnostics, and an interactive web dashboard — built for network engineers and sysadmins.

🚀 Quick Overview

Web dashboard (UI): http://localhost:9000

REST API (FastAPI): http://localhost:8000 — API docs at /docs

Works cross-platform (Windows / Linux / macOS)

Recommended Python: 3.10+

🧰 Prerequisites

Git

Python 3.10+ (3.14 tested)

Optional: Docker & Docker Compose

For AI features: OpenAI API key (or alternate AI provider)

⚙️ Installation (virtual environment recommended)

Clone the repo

git clone https://github.com/Rutik176/network-troubleshooting-bot.git
cd network-troubleshooting-bot/network-bot


Create & activate virtual environment

python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows
.venv\Scripts\Activate.ps1


Install dependencies

pip install -r requirements.txt

▶️ Run Project Locally
Terminal 1 — Dashboard
python dashboard_server.py
# Opens at http://localhost:9000

Terminal 2 — API Server
python simple_main.py
# API docs at http://localhost:8000/docs

▶️ Docker Deployment
docker-compose up -d


Logs:

docker-compose logs -f


Stop:

docker-compose down

🔧 Configuration Files

config/config.yaml

config/devices.yaml

Includes:

DB settings

Email/Slack/Telegram alerts

AI configuration

Device list

Dashboard refresh interval

🔌 API Endpoints

Some useful endpoints:

POST /api/ping

POST /api/traceroute

POST /api/snmp

POST /api/ssh

POST /api/chat

GET /api/devices

Example:

import requests
resp = requests.post("http://localhost:8000/api/ping", json={"target":"8.8.8.8"})
print(resp.json())

🧪 Testing / Demo
python test_installation.py
python working_demo.py
python demo.py

⚠️ Troubleshooting

Ping issues on Windows → run as admin

SNMP errors → check device community string

AI not working → missing API key

Port conflicts → free ports 8000 & 9000

🔒 Security Best Practices

Use environment variables for secrets

Restrict SNMP/SSH access

Do not expose API publicly without auth

Rotate credentials periodically

📁 Project Structure
network-bot/
├── modules/
├── ai/
├── db/
├── integrations/
├── dashboard/
├── config/
├── simple_main.py
├── dashboard_server.py
├── demo.py
├── Dockerfile
└── docker-compose.yml

👨‍💻 Author

Rutik Bhojane
GitHub: https://github.com/Rutik176

Email: rutikbhojane176@gmail.com

📞 Support & Contact

If you need help or want to report a bug:

Email: rutikbhojane176@gmail.com

GitHub Issues: https://github.com/Rutik176

Developer: Rutik Bhojane
