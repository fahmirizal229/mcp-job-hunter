#!/usr/bin/env python3
"""
Fast MCP JSON-RPC Server for Career Intelligence & Job Hunting.
Provides multi-platform job aggregation, Kanban tracker lifecycle,
and tailored cover letter generation.
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List

SERVER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SERVER_DIR))

import job_db
import job_engine

job_db.init_db()

TOOLS = [
    {
        "name": "job_search_remote",
        "description": "Cari lowongan kerja remote global (Worldwide / Gaji USD & EUR / WFH) untuk posisi Backend Engineer, Golang, Node.js, PHP, Python, Software Engineer dari Remotive, Jobicy, RemoteOK, dan Arbeitnow.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Posisi/skill/bahasa pemrograman yang dicari (default: 'backend', 'golang', 'nodejs', 'php', 'python')."},
                "limit": {"type": "integer", "description": "Jumlah maksimal lowongan (default 6)."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "job_search_local",
        "description": "Cari lowongan kerja IT & Software Engineering di Indonesia (Glints, JobStreet, LinkedIn, Kalibrr, Dealls) dengan filter lokasi dan waktu.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Posisi/role yang dicari (misal: 'backend developer', 'golang developer', 'laravel developer')."},
                "location": {"type": "string", "description": "Kota/wilayah (default: 'Surabaya', 'Jakarta', 'Indonesia')."},
                "timelimit": {
                    "type": "string",
                    "enum": ["d", "w", "m", "y"],
                    "description": "Filter umur loker: 'd' (hari ini), 'w' (minggu ini), 'm' (bulan ini). Default: 'm'."
                },
                "limit": {"type": "integer", "description": "Jumlah maksimal lowongan (default 6)."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "job_analyze_match",
        "description": "Analisis kecocokan (Match Score %) antara requirement / deskripsi lowongan kerja dengan tech stack Backend Engineer kamu (PHP, Node.js, Go, Python, SQL, Redis, REST/gRPC API), lengkap dengan breakdown skill yang cocok, skill yang kurang, dan tips persiapan interview.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "role": {"type": "string", "description": "Nama posisi/jabatan yang dilamar."},
                "job_description": {"type": "string", "description": "Teks deskripsi pekerjaan, kualifikasi, atau requirements dari lowongan."}
            },
            "required": ["role", "job_description"]
        }
    },
    {
        "name": "job_add_application",
        "description": "Catat lowongan kerja baru yang diincar atau sudah dilamar ke dalam Papan Kanban Karir.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "company": {"type": "string", "description": "Nama perusahaan."},
                "role": {"type": "string", "description": "Posisi / nama jabatan."},
                "location": {"type": "string", "description": "Lokasi kerja ('Remote', 'Surabaya', 'Jakarta')."},
                "salary": {"type": "string", "description": "Rentang gaji jika diketahui."},
                "job_url": {"type": "string", "description": "Link lowongan kerja."},
                "status": {
                    "type": "string",
                    "enum": ["wishlist", "applied", "screening", "tech_test", "user_interview", "offering", "rejected"],
                    "description": "Status tahap lamaran (default: 'applied')."
                },
                "notes": {"type": "string", "description": "Catatan khusus (misal: jadwal tes, kontak HR, take home test)."}
            },
            "required": ["company", "role"]
        }
    },
    {
        "name": "job_update_status",
        "description": "Update tahap/status lamaran kerja di Papan Kanban (misal pindah ke tahap Interview, Tech Test, atau Offering).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "application_id": {"type": "integer", "description": "ID lamaran di database."},
                "new_status": {
                    "type": "string",
                    "enum": ["wishlist", "applied", "screening", "tech_test", "user_interview", "offering", "rejected", "withdrawn"],
                    "description": "Tahap baru lamaran."
                },
                "next_schedule": {"type": "string", "description": "Jadwal tahapan berikutnya (contoh: 'Besok 14:00 WIB via Google Meet')."},
                "notes": {"type": "string", "description": "Catatan tambahan."}
            },
            "required": ["application_id", "new_status"]
        }
    },
    {
        "name": "job_get_kanban",
        "description": "Dapatkan visualisasi status Papan Kanban lamaran kerja aktif dan pipeline karir saat ini.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "job_analyze_url",
        "description": "Ambil otomatis dan analisis lowongan kerja dari link/URL (Jobstreet, LinkedIn, Glints, Kalibrr, Dealls, dsb.) menggunakan Playwright stealth browser, lalu cocokkan langsung dengan profil CV Backend Engineer.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL link lowongan kerja (misal: https://id.jobstreet.com/id/job/...)"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "job_generate_upwork_proposal",
        "description": "Buat draf proposal penawaran (cover letter) Upwork yang ringkas, berkonversi tinggi, dan terpersonalisasi untuk proyek freelance backend/cloud/DevOps.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_title": {"type": "string", "description": "Judul postingan proyek di Upwork."},
                "job_description": {"type": "string", "description": "Deskripsi atau requirement proyek di Upwork."},
                "client_name": {"type": "string", "description": "Nama klien (jika tertera pada review/history, misal: 'John'). Default kosong."},
                "custom_focus": {"type": "string", "description": "Fokus khusus yang ingin ditonjolkan (misal: 'Kubernetes migration', 'FastAPI backend', 'API Optimization')."}
            },
            "required": ["job_title"]
        }
    },
    {
        "name": "job_generate_cover_letter",
        "description": "Buat draf Surat Lamaran / Cover Letter profesional yang disesuaikan dengan profil Backend Engineer (PHP/Laravel, Node.js, Go, Python, API Architecture, SQL/Redis Database).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "company": {"type": "string", "description": "Nama perusahaan target."},
                "role": {"type": "string", "description": "Posisi yang dilamar."},
                "language": {
                    "type": "string",
                    "enum": ["id", "en"],
                    "description": "Bahasa cover letter: 'id' (Bahasa Indonesia) atau 'en' (English). Default: 'id'."
                }
            },
            "required": ["company", "role"]
        }
    }
]

def handle_call_tool(name: str, args: Dict[str, Any]) -> str:
    if name == "job_search_remote":
        q = args.get("query", "backend")
        limit = args.get("limit", 6)
        jobs = job_engine.search_remote_jobs(q, limit=limit)
        if not jobs:
            return f"Tidak ditemukan lowongan remote untuk '{q}' saat ini."
            
        lines = [f"🌍 **LOWONGAN GLOBAL REMOTE (WFH) UNTUK '{q.upper()}':**\n"]
        for idx, j in enumerate(jobs, 1):
            tags_str = f" | 🏷️ {', '.join(j['tags'])}" if j.get('tags') else ""
            lines.append(f"{idx}. `[{j['platform']}]` **{j['role']}** @ **{j['company']}**")
            lines.append(f"   📍 Lokasi: {j['location']} | 💰 Gaji: {j['salary']}{tags_str}")
            lines.append(f"   🔗 [Apply Link]({j['url']})\n")
        return "\n".join(lines).strip()

    elif name == "job_search_local":
        q = args.get("query", "backend developer")
        loc = args.get("location", "Surabaya")
        t_limit = args.get("timelimit", "m")
        limit = args.get("limit", 6)
        jobs = job_engine.search_local_jobs(q, location=loc, timelimit=t_limit, limit=limit)
        if not jobs:
            return f"Tidak ditemukan lowongan untuk '{q}' di {loc}."
            
        lines = [f"🇮🇩 **LOWONGAN KERJA DI {loc.upper()} UNTUK '{q.upper()}':**\n"]
        for idx, j in enumerate(jobs, 1):
            lines.append(f"{idx}. `[{j['platform']}]` **[{j['title']}]({j['url']})**")
            lines.append(f"   {j['snippet'][:160]}...\n")
        return "\n".join(lines).strip()

    elif name == "job_analyze_match":
        role = args.get("role", "Backend Engineer")
        jd = args.get("job_description", "")
        analysis = job_engine.analyze_job_match(role, jd)
        
        matched = ", ".join(analysis["matched_skills"]) if analysis["matched_skills"] else "Tidak terdeteksi spesifik"
        missing = ", ".join(analysis["missing_skills"]) if analysis["missing_skills"] else "Tidak ada gap signifikan"
        
        proj_lines = []
        for p in analysis.get("relevant_projects", []):
            proj_lines.append(f"• **{p['title']}** (`{', '.join(p['tech'])}`)\n  ↳ {p['proof']}")
        proj_str = "\n".join(proj_lines) if proj_lines else "• Pengalaman Backend Cloud & Distributed Systems (Wowrack Cloudraya V2 & Energeek)"

        cv_pts = "\n".join(f"• {b}" for b in analysis.get("cv_bullet_points", []))
        tips = "\n".join(f"• {t}" for t in analysis["interview_tips"]) if analysis["interview_tips"] else "• Siapkan demo arsitektur dan portfolio API terbaikmu."
        
        return (
            f"🎯 **ANALISIS KESESUAIAN PROFIL ({role.upper()})**\n\n"
            f"📊 **Skor Kecocokan**: **{analysis['match_percentage']}%** Match\n\n"
            f"✅ **Tech Stack yang Sesuai**:\n`{matched}`\n\n"
            f"⚠️ **Skill Tambahan/Ekspektasi Lowongan**:\n`{missing}`\n\n"
            f"🏆 **Pengalaman & Proyek Nyata Relevan (CV Proof)**:\n{proj_str}\n\n"
            f"📝 **Poin CV yang Disarankan (Tailored Bullet Points)**:\n{cv_pts}\n\n"
            f"💡 **Tips Interview & Strategi Melamar**:\n{tips}"
        )

    elif name == "job_add_application":
        comp = args["company"]
        role = args["role"]
        loc = args.get("location", "Remote")
        sal = args.get("salary", "Kompetitif")
        url = args.get("job_url", "")
        status = args.get("status", "applied")
        notes = args.get("notes", "")
        
        app_id = job_db.add_application(
            company=comp, role=role, location=loc, salary=sal, job_url=url, status=status, notes=notes
        )
        job_engine.sync_kanban_to_second_brain()
        return (
            f"✅ **LAMARAN KERJA BERHASIL DICATAT!**\n"
            f"• 🆔 ID: `{app_id}`\n"
            f"• 🏢 Perusahaan: **{comp}**\n"
            f"• 💼 Posisi: **{role}** ({loc})\n"
            f"• 📌 Status Stage: **{status.upper()}**\n"
            f"📊 Papan Kanban Second Brain otomatis ter-update!"
        )

    elif name == "job_update_status":
        app_id = args["application_id"]
        new_status = args["new_status"]
        sch = args.get("next_schedule")
        notes = args.get("notes")
        
        success = job_db.update_application_status(app_id, new_status, next_schedule=sch, notes=notes)
        if success:
            job_engine.sync_kanban_to_second_brain()
            app = job_db.get_application_by_id(app_id)
            comp = app["company"] if app else ""
            return f"✅ **STATUS LAMARAN ID {app_id} ({comp}) BERHASIL DI-UPDATE!** ➔ Tahap: **{new_status.upper()}**."
        else:
            return f"❌ Gagal mengupdate lamaran ID {app_id}. Pastikan ID valid."

    elif name == "job_get_kanban":
        board_md = job_engine.generate_kanban_markdown()
        job_engine.sync_kanban_to_second_brain()
        return board_md

    elif name == "job_analyze_url":
        url = args.get("url", "")
        analysis = job_engine.analyze_job_url(url)
        if analysis.get("status") == "error":
            return f"❌ {analysis.get('message', 'Gagal memproses URL lowongan.')}"

        role = analysis.get("role", "Backend Engineer")
        comp = analysis.get("company", "Perusahaan")
        loc = analysis.get("location", "Indonesia")
        matched = ", ".join(analysis["matched_skills"]) if analysis["matched_skills"] else "Tidak terdeteksi spesifik"
        missing = ", ".join(analysis["missing_skills"]) if analysis["missing_skills"] else "Tidak ada gap signifikan"

        proj_lines = []
        for p in analysis.get("relevant_projects", []):
            proj_lines.append(f"• **{p['title']}** (`{', '.join(p['tech'])}`)\n  ↳ {p['proof']}")
        proj_str = "\n".join(proj_lines) if proj_lines else "• Pengalaman Backend Cloud & Distributed Systems (Wowrack Cloudraya V2 & Energeek)"

        cv_pts = "\n".join(f"• {b}" for b in analysis.get("cv_bullet_points", []))
        tips = "\n".join(f"• {t}" for t in analysis["interview_tips"]) if analysis["interview_tips"] else "• Siapkan demo arsitektur dan portfolio API terbaikmu."

        return (
            f"🎯 **ANALISIS LOWONGAN ({role.upper()} @ {comp})**\n\n"
            f"📍 **Lokasi**: {loc} | 🌐 **Platform**: {analysis.get('platform')}\n"
            f"📊 **Skor Kecocokan dengan CV**: **{analysis['match_percentage']}%** Match\n\n"
            f"✅ **Tech Stack yang Sesuai**:\n`{matched}`\n\n"
            f"⚠️ **Skill Tambahan/Ekspektasi Lowongan**:\n`{missing}`\n\n"
            f"🏆 **Pengalaman & Proyek Relevan di CV Mas Fahmi**:\n{proj_str}\n\n"
            f"📝 **Poin CV yang Direkomendasikan (Tailored Bullets)**:\n{cv_pts}\n\n"
            f"💡 **Tips Wawancara & Rekomendasi Jawaban**:\n{tips}"
        )

    elif name == "job_generate_upwork_proposal":
        title = args["job_title"]
        desc = args.get("job_description", "")
        c_name = args.get("client_name", "")
        focus = args.get("custom_focus", "")
        proposal = job_engine.generate_upwork_proposal(
            job_title=title,
            job_description=desc,
            client_name=c_name,
            custom_focus=focus
        )
        return f"💼 **DRAFT PROPOSAL UPWORK (TAILORED):**\n\n```text\n{proposal}\n```\n\n💡 *Tips: Sesuaikan 1-2 baris pertama jika klien menyertakan instruksi/pertanyaan khusus.*"

    elif name == "job_generate_cover_letter":
        comp = args["company"]
        role = args["role"]
        lang = args.get("language", "id")
        cl = job_engine.generate_cover_letter(comp, role, language=lang)
        return f"📄 **DRAFT SURAT LAMARAN / COVER LETTER ({comp} - {role}):**\n\n```text\n{cl}\n```"

    else:
        raise ValueError(f"Unknown tool: {name}")

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")

            if method == "initialize":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "job-hunter-engine", "version": "1.0.0"}
                    }
                }
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": TOOLS}
                }
            elif method == "tools/call":
                params = req.get("params", {})
                name = params.get("name")
                args = params.get("arguments", {})
                output = handle_call_tool(name, args)
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": output}]
                    }
                }
            else:
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method {method} not found"}
                }

            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_res = {
                "jsonrpc": "2.0",
                "id": req.get("id") if "req" in locals() else None,
                "error": {"code": -32603, "message": str(e)}
            }
            sys.stdout.write(json.dumps(err_res) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
