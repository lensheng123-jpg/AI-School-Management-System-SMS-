# AI-SMS: A Human-in-the-Loop Decision Support Prototype

**Final Year Project I**  
**Author:** Na Kuan Li (BIT_B2201F-2505002)  
**Live Prototype:** [https://Kuanli123.pythonanywhere.com](https://Kuanli123.pythonanywhere.com) 

## 📖 Project Overview
The AI-SMS is a web-based, human-in-the-loop decision-support prototype designed for international school leaders. It organises evidence, detects gaps, maps stakeholders, and generates unranked options using AI. 

**Core Rule:** AI advises only. The School Leader makes the final decision. The system enforces a mandatory Human Decision Gate before any action plan is created.

## 🚀 Key Features
- **Role-Based Login:** Separate access for `Leader` (can make decisions) and `Admin` (view-only).
- **Evidence & Policy Mapping:** Displays synthetic evidence, verification status, and policy clauses.
- **Three AI Features (Advisory Only):**
  1. Neutral Decision Summary (Groq/Gemini)
  2. Evidence Gap Detection
  3. Trade-off Analysis for options
- **Human Decision Gate:** The action plan remains locked until the Leader explicitly confirms a decision and rationale.
- **Audit Trail:** Automatically records the evidence used, human edits, and final rationale.

## 🛠️ Technology Stack
- **Backend:** Python 3, Flask
- **Database:** SQLite
- **Frontend:** HTML, CSS, Bootstrap 5
- **AI Integration:** Groq API (Primary), Google Gemini API (Fallback)

## 💻 How to Run Locally

**1. Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/ai-sms.git
cd ai-sms
