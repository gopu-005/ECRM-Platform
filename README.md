# 🏢 ECRM Platform — Multi-Tenant Enterprise CRM

> A production-grade, asynchronous, multi-tenant Enterprise Customer Relationship Management (CRM) platform built with **FastAPI**, **React**, **PostgreSQL**, **Redis**, and **Celery**.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)
![React](https://img.shields.io/badge/React-18-61DAFB.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.2+-3178C6.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1.svg)
![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)

---

## 📌 Executive Summary

**ECRM Platform** is a full-stack, enterprise-class CRM software engineered for modern B2B/B2C organizations that require strict multi-tenant isolation, real-time sales pipeline management, scalable background job execution, and deep analytics.

Built from the ground up to solve complex enterprise requirements, ECRM features row-level multi-tenancy (`organization_id` bound), algorithmic lead scoring (0–100 score matrix), an interactive drag-and-drop Kanban pipeline for deal management, automated task/meeting tracking, and a comprehensive BI dashboard with 20+ real-time KPIs.

---

## ✨ Key Platform Features

### 🛡️ 1. Multi-Tenant Architecture & RBAC
- **Strict Row-Level Isolation:** Every query passes through a generic `BaseRepository` that automatically enforces `organization_id` scoping to prevent cross-tenant data leaks.
- **JWT & Redis Security:** Dual-token JWT system (short-lived Access Tokens, long-lived Refresh Tokens) with Redis-backed token revocation and blacklisting for secure logout.
- **Role-Based Access Control (RBAC):** Granular permission checks supporting `ORG_ADMIN`, `SALES_MANAGER`, `SALES_REP`, and `VIEWER` roles.

### ⚡ 2. Core CRM Modules
- **Lead Intelligence & Scoring:** Rule-based algorithmic scoring engine (0–100) factoring in contact completeness, revenue tiers, employee count, lead sources, and conversion readiness. Supports 1-click lead-to-contact conversion.
- **Accounts & Contacts:** Centralized account management linking domain names, employee counts, revenue figures, and associated contact profiles.
- **Kanban Sales Pipeline & Forecasting:** Visual Kanban board for deals across 6 pipeline stages (*Prospecting, Qualification, Proposal, Negotiation, Closed Won, Closed Lost*) with revenue probability weighting and close date forecasting.
- **Tasks & Productivity Management:** Integrated task queue with status filtering (*Todo, In Progress, Completed*), priority flags, due-date alerts, and completion tracking.
- **Meeting Scheduling & Calendar:** Manage client meetings, location details, Google Meet/Zoom URLs, organizer tracking, and attendee lists.

### 📊 3. Analytics & BI Reporting Engine
- **Dashboard KPIs:** 12+ real-time metric cards covering Win Rate, Weighted Pipeline Value, Average Deal Size, Lead Conversion Rate, and Activity Velocity.
- **Interactive Recharts Visualizations:** 6-month area revenue trends, status pie charts, deal stage bar charts, and sales team leaderboards.
- **Audit Logging:** System-wide audit trail recording user actions, resource modifications, and IP addresses.

### 🔄 4. Background Job Processing
- **Celery & Redis Task Engine:** Asynchronous task queue handling batch lead re-scoring, background CSV import jobs, SMTP email delivery, and nightly analytics rollups.
- **Celery Beat Scheduler & Flower Monitor:** Automated scheduled jobs and live web interface for worker monitoring.

---

## 🛠️ Technology Stack

| Domain | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend API** | Python 3.11, FastAPI | Asynchronous Web Framework & REST APIs |
| **Database** | PostgreSQL 15, Async SQLAlchemy 2.0 | Relational Database & ORM |
| **Caching & Auth** | Redis 7 | JWT Token Revocation & Caching |
| **Background Tasks** | Celery 5, Celery Beat, Flower | Asynchronous Task Processing & Job Scheduling |
| **Frontend UI** | React 18, TypeScript, Vite | Modern Single Page Application (SPA) |
| **State & Data Fetching** | TanStack Query v5, Zustand | Server State Caching & Client Auth Store |
| **Styling & Icons** | Vanilla CSS, Tailwind CSS, Lucide Icons | Glassmorphism Dark Mode Design System |
| **Charts & Pipeline** | Recharts, @dnd-kit | Analytics Visualizations & Kanban Drag-and-Drop |
| **Orchestration** | Docker, Docker Compose | 8-Service Microservices Containerization |

---

## 📁 Repository Structure

```
ECRM-Platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # REST API Routers (Auth, Leads, Deals, Analytics, Admin)
│   │   ├── core/           # Config, DB Connection, Security, Dependencies, Redis
│   │   ├── models/         # SQLAlchemy ORM Models (14 Multi-Tenant Entities)
│   │   ├── repositories/   # BaseRepository with Row-Level Isolation
│   │   ├── schemas/        # Pydantic Schemas for Validation
│   │   ├── tasks/          # Celery Worker Tasks (Scoring, CSV, Email)
│   │   └── main.py         # FastAPI Entry Point & Lifespan Handler
│   ├── scripts/
│   │   └── seed.py         # Massive Data Seeder (Generates 10K+ Realistic Records)
│   ├── Dockerfile
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # Layout, Sidebar, TopBar
│   │   ├── pages/          # 20+ Full CRM & Analytics Views
│   │   ├── lib/            # Axios API Client & Utility Functions
│   │   ├── stores/         # Zustand Auth & UI Stores
│   │   ├── App.tsx         # React Router v6 Configuration
│   │   └── index.css       # Design Tokens & Utility Classes
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── docker-compose.yml      # Development Docker Orchestration (8 Services)
├── docker-compose.prod.yml # Production Multi-Stage Deployment Config
├── .env.example            # Environment Configuration Template
└── README.md
```

---

## 🚀 Quick Start & Local Setup

### Option 1: Docker Compose (Recommended)

Run the entire platform (Postgres, Redis, FastAPI, Celery, Beat, Flower, React, PgAdmin) with a single command:

```bash
# 1. Clone the repository
git clone https://github.com/gopu-005/ECRM-Platform.git
cd ECRM-Platform

# 2. Copy environment configuration
cp .env.example .env

# 3. Launch all 8 services
docker-compose up --build
```

Access services at:
- **Frontend App:** `http://localhost:3000`
- **FastAPI Swagger Docs:** `http://localhost:8000/docs`
- **Celery Flower Dashboard:** `http://localhost:5555`
- **PgAdmin Database Manager:** `http://localhost:5050`

---

### Option 2: Local Development Setup

#### 1. Backend Setup (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed Database with 10,000+ realistic records across 3 organizations
python -m scripts.seed

# Run Development Server
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup (React + Vite)

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

---

## 🔑 Demo Access Credentials

The database seeder (`scripts/seed.py`) pre-populates 3 active enterprise organizations with 10,000+ leads, contacts, deals, and tasks. You can log in using any of the following credentials:

| Tenant / Organization | Admin Email | Password | Role |
| :--- | :--- | :--- | :--- |
| **Acme Corp CRM** | `user1@acmecorp.com` | `Password123!` | `ORG_ADMIN` |
| **Global Sales Co** | `user1@globalsales.com` | `Password123!` | `ORG_ADMIN` |
| **StartupXYZ** | `user1@startupxyz.com` | `Password123!` | `ORG_ADMIN` |

*Additional roles (`user2` through `user5`) are available per organization representing Sales Managers, Sales Reps, and Viewers.*

---

## 📡 API Documentation & Endpoints

FastAPI automatically generates interactive OpenAPI documentation available at runtime:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Key Endpoint Routes:
- `POST /api/v1/auth/login` — Authenticate & receive JWT pair
- `POST /api/v1/auth/register` — Provision new organization tenant & admin
- `GET /api/v1/leads` — Filtered, paginated leads with algorithmic score
- `POST /api/v1/leads/{id}/convert` — Convert qualified lead to contact
- `GET /api/v1/deals/pipeline` — Grouped deals by stage for Kanban view
- `GET /api/v1/analytics/dashboard` — Aggregated KPIs & revenue trend dataset
- `GET /api/v1/admin/audit-logs` — Tenant audit log history

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.