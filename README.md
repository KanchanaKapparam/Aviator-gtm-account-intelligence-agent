# 🚀 Aviator GTM Account Intelligence & Outreach Agent

An AI-powered Go-To-Market (GTM) account intelligence agent built to automate technical prospect research for developer tooling companies.

This project analyzes public GitHub organization signals, engineering blogs, and DevEx/Platform Engineering hiring activity to identify companies that could benefit from Aviator's developer workflow products. It then uses AI to evaluate product fit, generate personalized outreach emails, and produce an interactive HTML dashboard.

> **Why I built this:** After reading Aviator's GTM Engineering Internship description, I wanted to build a project that demonstrates the combination of software engineering, APIs, automation, AI, and GTM workflows described in the role.

---

# 📸 Demo

## Dashboard

<img width="1242" height="830" alt="image" src="https://github.com/user-attachments/assets/427f630d-f60b-4b16-869a-9cb69ac5b884" />


---

## Generated Outreach Email

![Uploading image.png…]()

---
# ✨ Features

- 🔍 Collects engineering signals from GitHub organizations using the GitHub REST API
- 🌐 Searches public engineering blogs and DevEx/Platform Engineering hiring pages
- 🤖 Uses Gemini to analyze company fit for Aviator's products
- ✉️ Generates personalized outreach emails based on technical context
- 📊 Exports structured CSV reports
- 📈 Generates an interactive HTML dashboard using Jinja2
- ⚡ Modular Python architecture with reusable components

---

# 🏗️ Architecture


<img width="1265" height="672" alt="image" src="https://github.com/user-attachments/assets/3080a4f7-817f-4392-a9e9-f17254ddef4f" />


# 🛠️ Tech Stack

- Python 3.10+
- GitHub REST API
- Gemini API
- DuckDuckGo Search
- Jinja2
- Requests
- python-dotenv
- HTML/CSS

---

# 📂 Project Structure

```
aviator-gtm-agent/

│── main.py
│── companies.json
│── requirements.txt
│── .env.example
│── README.md
│── assets/
│   ├── dashboard-preview.png
│   ├── email-preview.png
│   └── terminal-preview.png
│── templates/
│── report.html
│── outreach_leads.csv
```

---

# ⚙️ Installation

## Clone the repository

```bash
git clone https://github.com/your-username/Aviator-gtm-account-intelligence-agent.git

cd Aviator-gtm-account-intelligence-agent
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Configure environment variables

Create a `.env` file.

```env
GEMINI_API_KEY=your_api_key

GITHUB_TOKEN=your_github_token
```

> GitHub token is optional but recommended to avoid API rate limits.

---

# 📝 Input

Define target companies inside `companies.json`.

```json
[
  {
    "name": "Vercel",
    "domain": "vercel.com",
    "github_org": "vercel"
  }
]
```

---

# ▶️ Run

```bash
python main.py
```

---

# 📊 Output

The application generates:

- `outreach_leads.csv` — structured prospect data
- `report.html` — interactive dashboard
- AI-generated personalized outreach emails

---

# 💡 Example Output

For every company, the pipeline produces:

- Company information
- GitHub activity
- Programming language distribution
- Engineering signals
- AI-generated fit score
- Fit reasoning
- Personalized outreach email

---

# 🎯 Why This Project

Modern engineering organizations generate thousands of pull requests every month. Understanding whether a company experiences CI/CD bottlenecks, merge conflicts, or developer productivity challenges usually requires significant manual research.

This project automates that workflow by combining public engineering signals with AI-generated analysis, enabling faster, more relevant technical outreach.

---

# 🚀 Future Improvements

- Clay integration
- HubSpot/Salesforce integration
- Playwright-based engineering site scraping
- n8n workflow automation
- Parallel processing
- Account scoring dashboard
- Unit tests
- Docker support

---

# 📄 License

This project is licensed under the MIT License.
