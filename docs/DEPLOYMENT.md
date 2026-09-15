# Deployment & Infrastructure Guide

> **Note**: Full deployment scripts, Docker container definitions, and CI/CD pipelines will be completed in Phase 22.

---

## 1. Candidate Infrastructure Setup

- **Frontend**: Next.js 15 deployed on **Vercel** with automatic preview environments.
- **Backend API**: FastAPI containerized with Docker, deployed on **GCP Cloud Run** or **Render** (auto-scaling serverless container platform).
- **Database**: **MongoDB Atlas Dedicated Cluster** (Vector Search enabled).
- **Observability**: **LangSmith** cloud workspace.
