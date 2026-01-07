# Trust-Management-App

A full-stack web application featuring a React frontend and a FastAPI backend. This project is designed as a monorepo, keeping both the client and server code in a single repository.

## 🏗 Tech Stack

* **Frontend:** React (via Vite)
* **Backend:** FastAPI (Python)
* **Server:** Uvicorn

## 🚀 Getting Started

Follow these steps to set up the project locally.

### Prerequisites

* Node.js (v14 or higher)
* Python (v3.8 or higher)

---

### 1. Backend Setup (FastAPI)

Navigate to the backend directory, create a virtual environment, and install dependencies.

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn
