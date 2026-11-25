# AI-SMS: A Human-in-the-Loop Decision Support System for Educational Leaders

**Final Year Project I (Academic Session 2026/2027)**  
**Author:** Na Kuan Li (`BIT_B2201F-2505002`) — Bachelor of Information Technology (Honours)  
**Supervisor:** Dr. Pong  
**Live Prototype:** [https://Kuanli123.pythonanywhere.com](https://Kuanli123.pythonanywhere.com)

---

## 📖 Project Overview
**AI-SMS** is a web-based, Human-in-the-Loop (HITL) decision-support prototype designed for educational leaders. It organises source-tagged evidence, detects missing information gaps, maps stakeholders, presents three unranked options with AI trade-off analysis, and enforces a mandatory Human Decision Gate.

* **Core Rule (`BR1` & `BR2`):** *AI advises only. The Educational Leader makes 100% of final decisions. The system enforces a mandatory Human Decision Gate before any action plan is unlocked.*

---

## 🔑 Demo Login Credentials
* **School Leader (Full 7-Stage Workflow & Decision Authority):** `leader` / `leader123`
* **Administrator (View-Only Access — Blocked from Confirming Decisions):** `admin` / `admin123`

---

## 🚀 Key Features
* **Role-Based Access Control:** Separate access for School Leader (can confirm decisions) and Administrator (strictly view-only).
* **Evidence & Policy Mapping:** Displays 28 synthetic PDPA-safe cases (24 Development cases + 4 Current intake cases) with exact source IDs (`DEV-001-E1`), verification statuses, and school policy clauses (`POL-01` to `POL-12`).
* **Three AI Helper Features (`Advisory only`):**
  1. **Neutral Decision Summary** (3–4 factual sentences without recommendations)
  2. **Evidence Gap Detection** (identifies 3–5 missing or unverified facts)
  3. **Trade-Off Analysis** (compares Potential Benefits and Risks across all 3 unranked options)
* **Mandatory Human Decision Gate (`/decide`):** The Action Plan (`/action-plan`) remains locked in SQLite until the Leader selects, edits, or writes a decision and records their rationale.
* **Audit & Privacy Note (`/audit`):** Permanently separates system evidence and options from the human decision record, rationale, timestamp, and PDPA retention note.

---

## 🛠️ Technology Stack
* **Backend:** Python 3, Flask
* **Database:** SQLite (`database/ai_sms.db`, initialized from Excel via `init_db.py`)
* **Frontend:** HTML5, CSS3, Bootstrap 5, Vanilla JavaScript (`fetch`)
* **AI Integration:** Groq API (`openai/gpt-oss-20b` — Primary), Google Gemini API (`gemini-3.8-flash` — Fallback)

---

## 📂 Submission Deliverables in This Repository
* **Final Report:** `KuanLi_AI-SMS_Project_I_Report_v6_Final_Polished.pdf` (and `.docx`)
* **Presentation Slides:** `aisms_2.html` (Open in browser and press `F11` for full-screen; use `←` `→` arrow keys)
* **Demonstration Video:** *(Upload your `.mp4` file here or paste your unlisted YouTube demo link here)*
* **Source Code:** `app.py`, `ai_service.py`, `init_db.py`, `templates/`, `static/`, and `data/`

---

## 💻 How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/lensheng123-jpg/](https://github.com/lensheng123-jpg/)<your-repository-name>.git
   cd <your-repository-name>
