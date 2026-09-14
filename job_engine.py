#!/usr/bin/env python3
"""
Career Intelligence & Job Hunting Engine.
Fetches live jobs (Multi-Source Global Remote USD + Local Indonesia / Surabaya),
analyzes tech stack compatibility, manages Kanban application lifecycle,
and syncs with Obsidian Second Brain.
"""

import sys
import os
import re
import json
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

# Link duckduckgo search engine
DDG_DIR = Path("/home/arusuka/mcp-duckduckgo")
if str(DDG_DIR) not in sys.path:
    sys.path.insert(0, str(DDG_DIR))

import job_db
try:
    import search_engine
except ImportError:
    search_engine = None

job_db.init_db()

SECOND_BRAIN_TRACKER = Path("/home/arusuka/second-brain/Projects/career_job_tracker.md")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*"
}

DEFAULT_USER_SKILLS = [
    "PHP", "Laravel", "Node.js", "TypeScript", "JavaScript", "Go", "Golang",
    "Python", "FastAPI", "Express", "REST API", "gRPC", "MySQL", "PostgreSQL",
    "SQLite", "Redis", "Docker", "Linux", "Microservices", "Nginx", "Git"
]

import xml.etree.ElementTree as ET

def search_remote_jobs(query: str = "backend", limit: int = 12, page: int = 1) -> List[Dict[str, Any]]:
    """Search live global remote jobs via 6 top global aggregators."""
    offset = max(0, (page - 1) * limit)
    needed = offset + limit
    jobs = []
    q_low = query.lower()
    seen_urls = set()

    # 1. We Work Remotely (WWR) RSS Feed
    try:
        url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            root = ET.fromstring(resp.read())
            for item in root.findall('./channel/item'):
                title_node = item.find('title')
                link_node = item.find('link')
                pub_node = item.find('pubDate')
                desc_node = item.find('description')
                
                raw_title = title_node.text if title_node is not None else ""
                j_url = link_node.text if link_node is not None else ""
                pub_date = pub_node.text[:16] if pub_node is not None and pub_node.text else ""
                desc = desc_node.text if desc_node is not None else ""

                if not j_url or j_url in seen_urls:
                    continue

                company = "Tech Company"
                role = raw_title
                if ":" in raw_title:
                    parts = raw_title.split(":", 1)
                    company = parts[0].strip()
                    role = parts[1].strip()

                if q_low in raw_title.lower() or q_low in desc.lower() or any(k in raw_title.lower() for k in ["backend", "engineer", "developer", "go", "golang", "php", "laravel", "node", "python"]):
                    seen_urls.add(j_url)
                    jobs.append({
                        "platform": "We Work Remotely (USD)",
                        "source": "We Work Remotely",
                        "company": company,
                        "title": role,
                        "role": role,
                        "location": "Worldwide / Remote",
                        "salary": "USD Kompetitif",
                        "url": j_url,
                        "tags": ["Remote", "Engineering", "WWR"],
                        "published_at": pub_date,
                        "description_snippet": desc[:200] if desc else f"{role} at {company}"
                    })
                if len(jobs) >= needed:
                    break
    except Exception:
        pass

    # 2. Himalayas Remote API
    if len(jobs) < needed:
        try:
            url = f"https://himalayas.app/jobs/api?limit=50"
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for j in data.get("jobs", []):
                    title = j.get("title", "")
                    company = j.get("companyName", "Tech Startup")
                    j_url = j.get("applicationLink") or f"https://himalayas.app/companies/{j.get('companySlug')}/jobs/{j.get('slug')}"
                    tags = j.get("categories", []) or []
                    
                    if not j_url or j_url in seen_urls:
                        continue

                    min_sal = j.get("minSalary")
                    max_sal = j.get("maxSalary")
                    salary_text = "USD Kompetitif"
                    if min_sal and max_sal:
                        salary_text = f"${min_sal:,} - ${max_sal:,} / yr"
                    elif min_sal:
                        salary_text = f"${min_sal:,}+ / yr"

                    if (q_low in title.lower() or any(q_low in str(t).lower() for t in tags) or any(k in title.lower() for k in ["backend", "engineer", "developer", "go", "php", "node", "python"])):
                        seen_urls.add(j_url)
                        jobs.append({
                            "platform": "Himalayas (USD)",
                            "source": "Himalayas",
                            "company": company,
                            "title": title,
                            "role": title,
                            "location": j.get("locationRestrictions", ["Worldwide"])[0] if j.get("locationRestrictions") else "Worldwide Remote",
                            "salary": salary_text,
                            "url": j_url,
                            "tags": tags[:3] or ["Remote", "USD"],
                            "published_at": j.get("pubDate", "")[:10],
                            "description_snippet": f"{title} at {company}. High-paying global remote tech position."
                        })
                    if len(jobs) >= needed:
                        break
        except Exception:
            pass

    # 3. Remotive API
    if len(jobs) < needed:
        try:
            encoded_q = urllib.parse.quote(query)
            url = f"https://remotive.com/api/remote-jobs?search={encoded_q}&limit={needed}"
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for j in data.get("jobs", []):
                    j_url = j.get("url", "")
                    if j_url and j_url not in seen_urls:
                        seen_urls.add(j_url)
                        salary_text = j.get("salary", "") or "USD Kompetitif"
                        r_title = j.get("title", "Software Engineer")
                        jobs.append({
                            "platform": "Remotive (Global WFH)",
                            "source": "Remotive",
                            "company": j.get("company_name", "Unknown Company"),
                            "title": r_title,
                            "role": r_title,
                            "location": j.get("candidate_required_location", "Worldwide Remote"),
                            "salary": salary_text,
                            "url": j_url,
                            "tags": j.get("tags", [])[:4],
                            "published_at": j.get("publication_date", "")[:10],
                            "description_snippet": f"{r_title} at {j.get('company_name')}. Global remote role."
                        })
                    if len(jobs) >= needed:
                        break
        except Exception:
            pass

    # 4. Jobicy API
    if len(jobs) < needed:
        try:
            encoded_q = urllib.parse.quote(query)
            url = f"https://jobicy.com/api/v2/remote-jobs?count=25&tag={encoded_q}"
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for j in data.get("jobs", []):
                    j_url = j.get("url", "")
                    if j_url and j_url not in seen_urls:
                        seen_urls.add(j_url)
                        min_sal = j.get("annualSalaryMin")
                        max_sal = j.get("annualSalaryMax")
                        sal_cur = j.get("salaryCurrency", "USD")
                        if min_sal and max_sal:
                            salary_text = f"{sal_cur} {min_sal:,} - {max_sal:,} / yr"
                        elif min_sal:
                            salary_text = f"{sal_cur} {min_sal:,}+ / yr"
                        else:
                            salary_text = "Kompetitif (USD)"

                        j_role = j.get("jobTitle", "Backend Engineer")
                        jobs.append({
                            "platform": "Jobicy (Global Remote)",
                            "source": "Jobicy",
                            "company": j.get("companyName", "Tech Company"),
                            "title": j_role,
                            "role": j_role,
                            "location": j.get("jobGeo", "Anywhere"),
                            "salary": salary_text,
                            "url": j_url,
                            "tags": [j.get("jobLevel", "Mid-Senior"), j.get("jobType", "Full-Time")],
                            "published_at": j.get("pubDate", "")[:10],
                            "description_snippet": f"{j_role} at {j.get('companyName')}. Global remote vacancy."
                        })
                    if len(jobs) >= needed:
                        break
        except Exception:
            pass

    # 5. RemoteOK API
    if len(jobs) < needed:
        try:
            url = "https://remoteok.com/api"
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for j in data[1:]:
                    title = j.get("position", "")
                    tags = j.get("tags", [])
                    company = j.get("company", "")
                    j_url = j.get("url", "")
                    if (q_low in title.lower() or any(q_low in str(t).lower() for t in tags)) and j_url not in seen_urls:
                        seen_urls.add(j_url)
                        jobs.append({
                            "platform": "RemoteOK (USD)",
                            "source": "RemoteOK",
                            "company": company,
                            "title": title,
                            "role": title,
                            "location": j.get("location", "Global Remote"),
                            "salary": f"${j.get('salary_min', 0):,} - ${j.get('salary_max', 0):,} / yr" if j.get("salary_min") else "USD Standar",
                            "url": j_url,
                            "tags": tags[:4],
                            "published_at": j.get("date", "")[:10],
                            "description_snippet": f"{title} at {company} via RemoteOK."
                        })
                    if len(jobs) >= needed:
                        break
        except Exception:
            pass

    # 6. Arbeitnow API
    if len(jobs) < needed:
        try:
            url = "https://www.arbeitnow.com/api/job-board-api"
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for j in data.get("data", []):
                    if not j.get("remote", False):
                        continue
                    title = j.get("title", "")
                    tags = j.get("tags", [])
                    j_url = j.get("url", "")
                    if (q_low in title.lower() or any(q_low in str(t).lower() for t in tags)) and j_url not in seen_urls:
                        seen_urls.add(j_url)
                        jobs.append({
                            "platform": "Arbeitnow (Remote EU/Global)",
                            "source": "Arbeitnow",
                            "company": j.get("company_name", "Tech Startup"),
                            "title": title,
                            "role": title,
                            "location": j.get("location", "Remote"),
                            "salary": "Kompetitif",
                            "url": j_url,
                            "tags": tags[:4],
                            "published_at": datetime.fromtimestamp(j.get("created_at", 0)).strftime("%Y-%m-%d") if j.get("created_at") else "",
                            "description_snippet": f"{title} at {j.get('company_name')} via Arbeitnow."
                        })
                    if len(jobs) >= needed:
                        break
        except Exception:
            pass

    return jobs[offset:offset+limit]

def search_local_jobs(
    query: str = "backend developer",
    location: str = "Jawa / Indonesia",
    timelimit: str = "m",
    limit: int = 12,
    page: int = 1
) -> List[Dict[str, Any]]:
    """Search Indonesian tech jobs across Java & Indonesia with time filtering and pagination."""
    if search_engine:
        return search_engine.search_jobs_web(query, location=location, timelimit=timelimit, max_results=limit, page=page)
    return []

try:
    import user_cv_profile
    USER_CV = user_cv_profile.USER_PROFILE
except ImportError:
    USER_CV = {}

def analyze_job_match(
    role: str,
    job_description: str,
    user_skills: Optional[List[str]] = None,
    tech_stack: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Analyze job description against user actual CV & portfolio to give match score, project mappings, and CV bullet points."""
    skills_pool = user_skills or tech_stack or DEFAULT_USER_SKILLS
    text_lower = (job_description or "").lower() + " " + (role or "").lower()

    matched_skills = []
    for skill in skills_pool:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            matched_skills.append(skill)

    common_industry_skills = [
        "Kubernetes", "AWS", "GCP", "GraphQL", "Kafka", "RabbitMQ", "CI/CD",
        "TDD", "Unit Test", "Elasticsearch", "Clean Architecture", "SOLID",
        "Event Driven", "Redis", "PostgreSQL", "MySQL", "Go", "Golang", "PHP",
        "Laravel", "Node.js", "TypeScript", "Python", "S3", "Microservices"
    ]
    
    missing_skills = []
    for req in common_industry_skills:
        pattern = r'\b' + re.escape(req.lower()) + r'\b'
        if re.search(pattern, text_lower):
            if not any(req.lower() == s.lower() for s in skills_pool):
                missing_skills.append(req)

    total_relevant = len(set(matched_skills + missing_skills))
    if total_relevant == 0:
        match_percentage = 88
    else:
        match_percentage = int((len(matched_skills) / total_relevant) * 100)
        match_percentage = max(55, min(99, match_percentage))

    relevant_projects = []
    if USER_CV and "projects" in USER_CV:
        for p in USER_CV["projects"]:
            p_tech = [t.lower() for t in p.get("tech", [])]
            if any(t in text_lower for t in p_tech) or any(s.lower() in p_tech for s in matched_skills):
                title_str = p.get("title", "Project")
                desc_str = p.get("desc", "")
                relevant_projects.append({
                    "title": title_str,
                    "company_project": title_str,
                    "category": p.get("category", "Backend"),
                    "tech": p.get("tech", []),
                    "proof": desc_str,
                    "evidence": desc_str
                })

    if not relevant_projects and USER_CV and "projects" in USER_CV:
        for p in USER_CV["projects"][:2]:
            title_str = p.get("title", "Project")
            desc_str = p.get("desc", "")
            relevant_projects.append({
                "title": title_str,
                "company_project": title_str,
                "category": p.get("category", "Backend"),
                "tech": p.get("tech", []),
                "proof": desc_str,
                "evidence": desc_str
            })

    cv_bullet_points = []
    if any(k in text_lower for k in ["cloud", "infrastructure", "kubernetes", "k8s", "s3", "storage", "billing", "vm", "virtualization"]):
        cv_bullet_points.append("Engineered core backend microservices for Cloudraya V2 multi-region IaaS/PaaS cloud platform, managing VM compute lifecycles, S3-compatible storage, and managed Kubernetes.")
    if any(k in text_lower for k in ["api", "rest", "grpc", "high throughput", "concurrency", "performance", "scalable"]):
        cv_bullet_points.append("Architected high-throughput RESTful/gRPC APIs with low latency, ACID-compliant database transactions, and multi-tier Redis caching.")
    if any(k in text_lower for k in ["iot", "realtime", "websocket", "telemetry", "streaming"]):
        cv_bullet_points.append("Developed high-frequency telemetry ingestion pipelines for Suramadu Bridge IoT structural monitoring and real-time WebSocket event streaming.")
    if any(k in text_lower for k in ["laravel", "php", "clean architecture", "testing", "phpunit"]):
        cv_bullet_points.append("Enforced Clean Architecture & SOLID principles with comprehensive automated PHPUnit test suites and zero-downtime CI/CD deployment pipelines.")

    if not cv_bullet_points:
        cv_bullet_points.append("6+ years specializing in scalable backend systems (Go, PHP/Laravel, Node.js, Python), database query tuning, and distributed cloud services.")

    tips = []
    if any(s in ["Go", "Golang", "Node.js"] for s in matched_skills):
        tips.append("Jelaskan pengalaman handling concurrency, goroutines/async I/O, dan optimasi API throughput.")
    if any(s in ["PHP", "Laravel"] for s in matched_skills):
        tips.append("Tonjolkan pengalaman arsitektur Cloudraya V2, background queue processing, dan Laravel Reverb WebSockets.")
    if any(s in ["PostgreSQL", "MySQL", "Redis"] for s in matched_skills):
        tips.append("Diskusikan strategi indexing PostgreSQL, replikasi database, dan caching multi-tier Redis.")
    if missing_skills:
        tips.append(f"Pelajari konsep dasar / pelengkap yang disebutkan dalam lowongan: {', '.join(missing_skills[:3])}.")

    return {
        "role": role,
        "match_percentage": match_percentage,
        "match_score": match_percentage,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "relevant_projects": relevant_projects[:3],
        "cv_bullet_points": cv_bullet_points,
        "tailored_cv_bullets": cv_bullet_points,
        "interview_tips": tips,
        "interview_talking_points": tips
    }

def scrape_job_posting(url: str) -> Dict[str, Any]:
    """Scrapes a job posting using Playwright stealth engine."""
    scraper_path = "/home/arusuka/mcp-job-hunter/playwright_scraper.py"
    py_bin = "/home/arusuka/.crawl4ai-env/bin/python"
    try:
        import subprocess
        out = subprocess.check_output([py_bin, scraper_path, url], timeout=30, text=True)
        data = json.loads(out)
        return data
    except Exception as e:
        return {
            "status": "error",
            "url": url,
            "message": f"Gagal mengekstrak lowongan via Playwright: {e}"
        }

def analyze_job_url(url: str) -> Dict[str, Any]:
    """Scrapes any job URL (Jobstreet, LinkedIn, Glints, etc.) and performs automatic CV matching analysis."""
    scraped = scrape_job_posting(url)
    if scraped.get("status") != "success":
        return {
            "status": "error",
            "url": url,
            "message": scraped.get("message", "Gagal membaca lowongan.")
        }

    title = scraped.get("title") or "Backend Engineer"
    company = scraped.get("company") or "Perusahaan"
    loc = scraped.get("location") or "Indonesia"
    desc = scraped.get("description") or ""

    analysis = analyze_job_match(title, desc)
    analysis["company"] = company
    analysis["location"] = loc
    analysis["url"] = url
    analysis["platform"] = scraped.get("platform", "Web")
    analysis["raw_description"] = desc[:500]
    return analysis

def get_kanban_board_data() -> Dict[str, Any]:
    """Retrieve all applications organized by Kanban stages."""
    all_apps = job_db.get_all_applications()
    stages = {st: [] for st in job_db.KANBAN_STAGES}
    
    for app in all_apps:
        st = app["status"]
        if st in stages:
            stages[st].append(app)
        else:
            stages["wishlist"].append(app)
            
    return {
        "total_applications": len(all_apps),
        "stages": stages,
        "active_pipeline_count": sum(len(stages[s]) for s in ["applied", "screening", "tech_test", "user_interview", "offering"])
    }

def generate_kanban_markdown() -> str:
    """Generate interactive markdown representation of the Kanban board."""
    data = get_kanban_board_data()
    stages = data["stages"]
    
    lines = [
        "📊 **PAPAN KANBAN LAMARAN KERJA (CAREER PIPELINE)**",
        f"Total Terdaftar: **{data['total_applications']}** | Aktif dalam Proses: **{data['active_pipeline_count']}**\n"
    ]
    
    for st in job_db.KANBAN_STAGES:
        emoji = job_db.STAGE_EMOJIS.get(st, "📌")
        label = job_db.STAGE_LABELS.get(st, st.title())
        apps = stages.get(st, [])
        
        lines.append(f"### {emoji} {label} ({len(apps)})")
        if not apps:
            lines.append("  _(Kosong)_\n")
            continue
            
        for a in apps:
            sch_text = f" | 🗓️ *Jadwal*: `{a['next_schedule']}`" if a["next_schedule"] else ""
            date_text = f" | 📅 Dilamar: `{a['applied_date']}`" if a["applied_date"] else ""
            lines.append(f"• `[ID: {a['id']}]` **{a['role']}** @ **{a['company']}** ({a['location']}){date_text}{sch_text}")
            if a["notes"]:
                lines.append(f"  ↳ _Notes_: {a['notes']}")
        lines.append("")
        
    return "\n".join(lines)

def sync_kanban_to_second_brain():
    """Write updated Kanban status to Obsidian Second Brain note."""
    board_md = generate_kanban_markdown()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    note_content = f"""---
title: Career & Job Application Kanban Tracker
tags: ["career", "job-hunting", "kanban", "tracker", "projects"]
updated: {today_str}
---

# 💼 Career & Job Application Kanban Tracker

Dokumen ini melacak seluruh proses pencarian kerja, pipeline lamaran, jadwal interview, dan offering dari berbagai platform.

---

{board_md}

---

## 🛠️ CLI Quick Commands
- `job-hunter search "backend developer"` : Cari lowongan remote / lokal.
- `job-hunter match-url <URL>` : Ekstrak URL loker via Playwright dan cocokan dengan CV.
- `job-hunter add "PT ABC" "Senior Backend Engineer" --location "Surabaya" --status "applied"` : Tambah lamaran.
- `job-hunter update <ID> "tech_test" --schedule "Besok 14:00"` : Pindahkan status stage.
- `job-hunter kanban` : Tampilkan papan kanban.

Links: [[Rules/core_rules]], [[Preferences/workflow]], [[Preferences/tech_stack]], [[Entities/second_brain]]
"""
    SECOND_BRAIN_TRACKER.parent.mkdir(parents=True, exist_ok=True)
    SECOND_BRAIN_TRACKER.write_text(note_content.strip() + "\n", encoding="utf-8")

def generate_cover_letter(
    company: str,
    role: str,
    job_description: str = "",
    language: str = "id"
) -> str:
    """Generate high-converting cover letter tailored for Backend Engineer profile."""
    if language.lower() == "en":
        return f"""Dear Hiring Team at {company},

I am writing to express my strong interest in the {role} position at {company}. As a Backend Engineer with extensive hands-on experience in architecting high-performance APIs, database optimization, and scalable server-side systems using PHP/Laravel, Node.js (TypeScript), Go (Golang), and Python, I am confident in my ability to make an immediate, meaningful impact on your engineering team.

Key Highlights of My Experience:
- **Backend Architecture & Robust APIs**: Deep experience in designing and building resilient RESTful & gRPC APIs, event-driven architectures, and high-throughput backend services.
- **Database Performance & Optimization**: Proven track record in schema design, query optimization, indexing strategies, and multi-tier caching (Redis, PostgreSQL, MySQL, SQLite).
- **Clean Code & Reliability**: Committed to clean, maintainable, modular codebase, thorough automated testing, and secure API hardening standards.

I have been following {company}'s growth and greatly admire your focus on technical excellence. I would welcome the opportunity to discuss how my backend engineering background and proactive problem-solving mindset can contribute to your product goals.

Thank you for your time and consideration.

Best regards,
Fahmi Rizal
Surabaya, Indonesia
"""
    else:
        return f"""Yth. Tim Rekrutmen & Hiring Manager {company},

Melalui surat lamaran ini, saya bermaksud menyampaikan ketertarikan saya untuk bergabung pada posisi **{role}** di **{company}**. Berbekal pengalaman profesional sebagai **Backend Engineer** dalam merancang arsitektur API berkinerja tinggi, manajemen basis data, serta pengembangan sistem server-side yang skalabel menggunakan **PHP (Laravel), Node.js (TypeScript/JavaScript), Go (Golang), dan Python**, saya yakin dapat memberikan kontribusi nyata bagi pengembangan produk {company}.

Ringkasan Keahlian & Nilai Tambah Saya:
1. **Arsitektur Backend & Desain API**: Berpengalaman dalam merancang dan mengimplementasikan RESTful & gRPC API yang efisien, aman, dan siap menangani beban traffic tinggi.
2. **Manajemen & Optimasi Database**: Terbiasa dengan perancangan skema relasional, optimasi query & indexing (PostgreSQL, MySQL, SQLite), serta strategi caching menggunakan Redis untuk meminimalkan response time.
3. **Standar Kode & Reliabilitas**: Menjunjung tinggi prinsip Clean Architecture, kode yang modular, teruji (unit testing), serta penerapan standar keamanan API yang ketat.

Saya sangat antusias dengan kesempatan untuk berkembang dan berkolaborasi bersama tim engineering {company}. Terlampir portofolio dan riwayat pengalaman saya, dan saya siap untuk berdiskusi lebih mendalam pada tahapan wawancara selanjutnya.

Terima kasih atas waktu dan perhatian yang diberikan.

Salam hormat,
**Fahmi Rizal**
Surabaya, Jawa Timur
"""

def main():
    if len(sys.argv) < 2:
        print("Penggunaan Job Hunter CLI:")
        print("  job-hunter search <role> [--remote | --local <kota>]")
        print("  job-hunter match-url <URL>")
        print("  job-hunter scrape <URL>")
        print("  job-hunter add <company> <role> [--location 'Remote'] [--status 'applied'] [--notes 'catatan']")
        print("  job-hunter update <app_id> <status> [--schedule 'Jadwal'] [--notes 'Catatan baru']")
        print("  job-hunter kanban")
        print("  job-hunter cover-letter <company> <role> [--lang id|en]")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "search":
        q = sys.argv[2] if len(sys.argv) > 2 else "backend"
        if "--local" in sys.argv:
            loc_idx = sys.argv.index("--local")
            loc = sys.argv[loc_idx + 1] if loc_idx + 1 < len(sys.argv) else "Surabaya"
            print(f"\n🔍 Mencari Lowongan Kerja: '{q}' di {loc}...")
            jobs = search_local_jobs(q, location=loc)
            for idx, j in enumerate(jobs, 1):
                print(f"{idx}. [{j['platform']}] {j['title']}\n   🔗 {j['url']}\n   📄 {j['snippet'][:120]}...\n")
        else:
            print(f"\n🔍 Mencari Lowongan Global Remote: '{q}'...")
            jobs = search_remote_jobs(q)
            for idx, j in enumerate(jobs, 1):
                print(f"{idx}. [{j['platform']}] {j['role']} @ {j['company']} ({j['location']})")
                print(f"   💰 Gaji: {j['salary']} | 🔗 Apply: {j['url']}\n")

    elif cmd in ("match-url", "match"):
        if len(sys.argv) < 3:
            print("Error: Harap masukkan URL lowongan.")
            sys.exit(1)
        url = sys.argv[2]
        print(f"\n🌐 Mengambil & Menganalisis Loker via Playwright Stealth: {url} ...")
        res = analyze_job_url(url)
        if res.get("status") == "error":
            print(f"❌ {res.get('message')}")
            sys.exit(1)

        print(f"\n🎯 HASIL ANALISIS LOKER:")
        print(f"🏢 Perusahaan: {res.get('company')} | Posisi: {res.get('role')} ({res.get('location')})")
        print(f"📊 Skor Kecocokan CV: {res.get('match_percentage')}% Match\n")
        print(f"✅ Tech Stack Cocok: {', '.join(res.get('matched_skills', []))}")
        print(f"⚠️ Skill Tambahan: {', '.join(res.get('missing_skills', [])) or '-'}\n")
        print("🏆 Proyek Relevan di CV:")
        for p in res.get("relevant_projects", []):
            print(f"  • {p['title']} ({', '.join(p['tech'])})")
            print(f"    ↳ {p['proof']}")

    elif cmd == "scrape":
        if len(sys.argv) < 3:
            print("Error: Harap masukkan URL lowongan.")
            sys.exit(1)
        url = sys.argv[2]
        res = scrape_job_posting(url)
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif cmd == "kanban":
        print("\n" + generate_kanban_markdown())
        sync_kanban_to_second_brain()

    elif cmd == "add":
        if len(sys.argv) < 4:
            print("Error: Harap masukkan nama perusahaan dan role.")
            sys.exit(1)
        company = sys.argv[2]
        role = sys.argv[3]
        loc = "Remote"
        status = "applied"
        notes = ""
        
        if "--location" in sys.argv:
            loc = sys.argv[sys.argv.index("--location") + 1]
        if "--status" in sys.argv:
            status = sys.argv[sys.argv.index("--status") + 1]
        if "--notes" in sys.argv:
            notes = sys.argv[sys.argv.index("--notes") + 1]
            
        app_id = job_db.add_application(company=company, role=role, location=loc, status=status, notes=notes)
        sync_kanban_to_second_brain()
        print(f"✅ Berhasil mencatat lamaran [ID: {app_id}] {role} @ {company} (Status: {status}). Papan Kanban Second Brain ter-update!")

    elif cmd == "update":
        if len(sys.argv) < 4:
            print("Error: Harap masukkan ID lamaran dan status baru.")
            sys.exit(1)
        app_id = int(sys.argv[2])
        new_status = sys.argv[3]
        sch = None
        notes = None
        if "--schedule" in sys.argv:
            sch = sys.argv[sys.argv.index("--schedule") + 1]
        if "--notes" in sys.argv:
            notes = sys.argv[sys.argv.index("--notes") + 1]
            
        if job_db.update_application_status(app_id, new_status, next_schedule=sch, notes=notes):
            sync_kanban_to_second_brain()
            print(f"✅ Berhasil update lamaran [ID: {app_id}] ➔ Status: {new_status}. Papan Kanban ter-update!")
        else:
            print(f"❌ Gagal update lamaran ID {app_id}.")

    elif cmd in ("cover-letter", "cl"):
        if len(sys.argv) < 4:
            print("Error: Harap masukkan nama perusahaan dan role.")
            sys.exit(1)
        comp = sys.argv[2]
        role = sys.argv[3]
        lang = "id"
        if "--lang" in sys.argv:
            lang = sys.argv[sys.argv.index("--lang") + 1]
        print(f"\n📄 === DRAFT SURAT LAMARAN / COVER LETTER ({comp} - {role}) ===\n")
        print(generate_cover_letter(comp, role, language=lang))

if __name__ == "__main__":
    main()
