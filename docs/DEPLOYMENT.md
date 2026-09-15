# Production Deployment Guide

Refer to [deployment.md](file:///c:/Users/ASUS/Documents/capstone2/docs/deployment.md) for full deployment specifications, environment secrets, and monitoring architecture.

## Quick Summary
- **Frontend Target:** Vercel
- **Backend Target:** Render / Railway (FastAPI)
- **Database:** MongoDB Atlas (Persistent Storage + Vector Search)
- **Tracing:** LangSmith (`LANGCHAIN_TRACING_V2=true`)
- **Health Check:** `GET /health`
