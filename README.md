<div align="center">

# 🎯 AI Career Intelligence & Job Hunter MCP Engine

<p align="center">
  <strong>Multi-aggregator developer job scraper, AI tech stack compatibility match analyzer, and Kanban lifecycle manager.</strong>
</p>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.0-blue?style=flat-square)](https://github.com/jlowin/fastmcp)
[![SQLite](https://img.shields.io/badge/SQLite-WAL_Mode-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-emerald?style=flat-square)](LICENSE)

</div>

---

## ✨ Features

1. **🌐 Multi-Portal Remote Scraper**:
   - Aggregates live developer jobs from top global portals: **We Work Remotely**, **Himalayas**, **Jobicy**, **RemoteOK**, **Remotive**, and **Arbeitnow**.
   - Local Indonesian portal search (LinkedIn, Glints, JobStreet).

2. **🧠 Tech Stack Match Scoring Algorithm**:
   - Parses job descriptions and calculates compatibility percentage (0-100%) against candidate skill profiles (Go, Laravel, Node.js, Python, PostgreSQL, Redis, Cloud).

3. **📋 Kanban Application Tracker**:
   - Complete application lifecycle stages: `Wishlist` ➔ `Applied` ➔ `Screening` ➔ `Technical Test` ➔ `Interview` ➔ `Offer` ➔ `Rejected`.

4. **📡 Radar CLI**:
   - Bundled with `job-radar` CLI for automated daily digests and Telegram alerts.

---

## 🛠️ Usage

```bash
# Run standalone radar scan
python3 job_engine.py

# Run MCP Server
python3 job_server.py
```
