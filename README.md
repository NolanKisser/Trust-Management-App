# Trust Management System (TMS)

A full-stack web application designed to track device trust scores and network health. This project features a **React** dashboard (styled with Tailwind CSS) and a **FastAPI** backend.

## 🏗 Tech Stack

* **Frontend:** React, Vite, Tailwind CSS (v3)
* **Backend:** FastAPI, Python, Uvicorn
* **Architecture:** Monorepo (Client and Server in one repository)

## 🚀 Getting Started

Follow these steps to set up the project locally. You will need **two terminal windows** open to run the full application.

### Prerequisites

* Node.js (v18 or higher)
* Python (v3.8 or higher)

---

### 1. Backend Setup (Terminal 1)

Navigate to the backend directory, set up the Python environment, and start the API server.

```bash
cd backend

# Create virtual environment (only needed once)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn

# Run the Server
uvicorn main:app --reload

```
### 2. Frontend Setup (Terminal 2)

Open a **new** terminal window, navigate to the frontend directory, and install the dependencies (forcing Tailwind CSS v3 for compatibility).

```bash
cd frontend

# Install dependencies (ensure Tailwind v3 is used)
npm install
npm install -D tailwindcss@3 postcss autoprefixer

# Initialize Tailwind Configuration
npx tailwindcss init -p

# Run the Development Server
npm run dev
