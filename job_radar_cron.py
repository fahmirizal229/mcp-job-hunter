#!/usr/bin/env python3
"""
Job Radar Morning Digest - Automated Daily Remote & Freelance Jobs for Fahmi.
Scans multiple global remote aggregators, separates Full-Time vs Freelance/Contract,
computes CV match scores (PHP > Go > Node.js priority),
and sends a clean, compact single-message summary to Telegram at 07:30 WIB.
"""

import sys
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

RADAR_DIR = Path(__file__).resolve().parent
if str(RADAR_DIR) not in sys.path:
    sys.path.insert(0, str(RADAR_DIR))

import job_engine
import user_cv_profile

# Helper to load .env variables
def load_env(env_path: str) -> Dict[str, str]:
    if not os.path.exists(env_path):
        return {}
    res = {}
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for l in f:
                l = l.strip()
                if not l or l.startswith('#') or '=' not in l:
                    continue
                k, v = l.split('=', 1)
                res[k.strip()] = v.strip().strip('"\'')
    except Exception:
        pass
    return res

hermes_env = load_env("/home/arusuka/.hermes/.env")
wa_env = load_env("/home/arusuka/whatsapp-secretary/.env")
env = {**hermes_env, **wa_env, **os.environ}

TELEGRAM_BOT_TOKEN = env.get("WA_TELEGRAM_BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN") or "8949770230:AAHzO9GvF5M4OGAPMcvvN7UH8XdyLgwXnXE"
TELEGRAM_CHAT_ID = env.get("WA_TELEGRAM_CHAT_ID") or env.get("TELEGRAM_HOME_CHANNEL") or "6463565617"

def fetch_and_categorize_jobs() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Fetches jobs and separates them into Full-Time vs Freelance/Contract lists."""
    queries = ["php", "laravel", "golang", "backend", "nodejs", "kubernetes", "freelance", "contract"]
    all_jobs = []
    seen_urls = set()

    for q in queries:
        try:
            results = job_engine.search_remote_jobs(query=q, limit=8)
            for j in results:
                url = j.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_jobs.append(j)
        except Exception as e:
            print(f"[Job Radar] Error searching for {q}: {e}", file=sys.stderr)

    fulltime_jobs = []
    freelance_jobs = []

    for j in all_jobs:
        role = j.get("role") or j.get("title", "Backend Developer")
        desc = j.get("description_snippet", "") + " " + " ".join(j.get("tags", []))
        tags_str = " ".join(j.get("tags", [])).lower()
        full_text = (role + " " + desc + " " + tags_str).lower()

        # Calculate CV Match
        match_res = job_engine.analyze_job_match(role=role, job_description=desc)
        match_score = match_res.get("match_percentage", 60)
        matched_skills = match_res.get("matched_skills", [])[:3]

        # Scoring boost based on user language preference: PHP > Go > Node.js
        boost = 0
        if any(k in full_text for k in ["php", "laravel", "lumen"]):
            boost += 18
        elif any(k in full_text for k in ["go", "golang"]):
            boost += 14
        elif any(k in full_text for k in ["node", "nodejs", "typescript", "express"]):
            boost += 9

        if any(k in role.lower() for k in ["backend", "engineer", "developer"]):
            boost += 6
        if any(k in role.lower() for k in ["kubernetes", "cloud", "platform", "s3"]):
            boost += 4

        final_score = min(99, match_score + boost)

        item = {
            "company": j.get("company", "Tech Company").strip(),
            "role": role.strip(),
            "salary": j.get("salary", "USD Kompetitif").strip(),
            "location": j.get("location", "Worldwide Remote").strip(),
            "url": j.get("url", ""),
            "score": final_score,
            "matched_skills": matched_skills,
            "platform": j.get("platform", "Remote")
        }

        # Classify as Freelance/Contract vs Full-Time
        is_freelance = any(k in full_text for k in ["contract", "freelance", "part-time", "hourly", "gigs", "project-based", "temporary"])
        if is_freelance:
            freelance_jobs.append(item)
        else:
            fulltime_jobs.append(item)

    # Sort descending by score
    fulltime_jobs.sort(key=lambda x: x["score"], reverse=True)
    freelance_jobs.sort(key=lambda x: x["score"], reverse=True)

    # If freelance list is too short, allocate top contractor/contract-friendly roles
    if len(freelance_jobs) < 3 and len(fulltime_jobs) > 4:
        freelance_jobs.extend(fulltime_jobs[4:7])

    return fulltime_jobs[:3], freelance_jobs[:3]

def format_telegram_message(fulltime: List[Dict[str, Any]], freelance: List[Dict[str, Any]]) -> str:
    """Formats separated Full-Time and Freelance jobs into a compact single message."""
    now = datetime.now()
    days_id = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    months_id = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    day_name = days_id[now.weekday()]
    month_name = months_id[now.month - 1]
    date_str = f"{day_name}, {now.day} {month_name} {now.year}"

    lines = [
        f"🎯 *RADAR LOKER & FREELANCE HARIAN*",
        f"📅 _{date_str} • Kurasi PHP ➔ Go ➔ Node.js_",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "💼 *[LOWONGAN FULL-TIME REMOTE]*"
    ]

    for idx, j in enumerate(fulltime, 1):
        comp = j["company"]
        role = j["role"]
        salary = j["salary"]
        score = j["score"]
        url = j["url"]
        skills = ", ".join(j["matched_skills"]) if j["matched_skills"] else "Backend"

        lines.append(f"{idx}. *{role}* — `{comp}`")
        lines.append(f"   💰 `{salary}` | 📊 *Match: {score}%* ({skills})")
        lines.append(f"   🔗 [Apply Full-Time]({url})")

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🛠️ *[PROJECT FREELANCE & KONTRAK USD]*")

    for idx, j in enumerate(freelance, 1):
        comp = j["company"]
        role = j["role"]
        salary = j["salary"]
        score = j["score"]
        url = j["url"]
        skills = ", ".join(j["matched_skills"]) if j["matched_skills"] else "Backend"

        lines.append(f"{idx}. *{role}* — `{comp}`")
        lines.append(f"   💰 `{salary}` | 📊 *Match: {score}%* ({skills})")
        lines.append(f"   🔗 [Ambil Project / Apply]({url})")

    lines.append("")
    lines.append("💡 _Kirim link ke chat untuk auto-generate Cover Letter atau Proposal Upwork!_")
    return "\n".join(lines).strip()

def send_telegram_alert(message: str) -> bool:
    """Sends the formatted message to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Job Radar] Telegram token or chat_id is missing.", file=sys.stderr)
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            if res_data.get("ok"):
                print("[Job Radar] ✅ Successfully delivered Dual-Pipeline Job Radar to Telegram!")
                return True
            else:
                print(f"[Job Radar] Telegram error: {res_data}", file=sys.stderr)
                return False
    except Exception as e:
        print(f"[Job Radar] Failed to send Telegram message: {e}", file=sys.stderr)
        return False

def main():
    send_flag = "--send" in sys.argv
    print("[Job Radar] Scanning and categorizing Full-Time & Freelance remote jobs...")
    fulltime, freelance = fetch_and_categorize_jobs()

    if not fulltime and not freelance:
        print("[Job Radar] No jobs found.")
        return

    msg = format_telegram_message(fulltime, freelance)
    print("\n" + msg + "\n")

    if send_flag:
        send_telegram_alert(msg)

if __name__ == "__main__":
    main()
