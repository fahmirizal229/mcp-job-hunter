#!/usr/bin/env python3
"""
Structured User CV & Professional Profile.
Synchronized with landing page profileData & Second Brain.
"""

from typing import Dict, Any, List

USER_PROFILE: Dict[str, Any] = {
    "name": "Muhammad Fahmi Rizal",
    "alias": "arusuka",
    "title": "Backend Engineer & Cloud Infrastructure",
    "experience_years": "6+ years",
    "location": "Surabaya, Jawa Timur, Indonesia",
    "email": "fahmirizal96@gmail.com",
    "linkedin": "https://www.linkedin.com/in/fahmi-rizal",
    "github": "https://github.com/fahmirizal229",
    "website": "https://arusuka.my.id",
    "summary": (
        "Backend & Cloud Infrastructure Engineer dengan pengalaman 6+ tahun dalam membangun dan "
        "memelihara sistem terdistribusi, platform cloud (IaaS/PaaS), dan API skala produksi. "
        "Terlibat langsung dalam pengembangan core engine Cloudraya V2 di Wowrack—mulai dari manajemen "
        "VM compute & bare-metal, storage kompatibel S3, provisioning cluster Kubernetes, hingga automated metering & billing."
    ),
    "skills": {
        "preferred_languages": ["PHP (Laravel)", "Go (Golang)", "Node.js"],
        "languages": ["PHP", "Laravel", "Go (Golang)", "Node.js", "TypeScript", "JavaScript", "Python (FastAPI)"],
        "databases": ["PostgreSQL", "MySQL", "MariaDB", "Redis", "MongoDB", "SQLite", "S3 Object Storage"],
        "cloud_infra": ["Kubernetes (K8s)", "Docker", "Apache CloudStack", "Linux Server Administration", "Bitbucket CI/CD", "GitHub Actions", "Nginx"],
        "architecture_testing": [
            "Clean Architecture", "Microservices", "Event-Driven", "Laravel Reverb WebSockets",
            "PHPUnit Automated Testing", "RESTful API", "gRPC", "Rate Limiting & JWT Auth", "Root Cause Analysis (L3 Support)"
        ]
    },
    "experiences": [
        {
            "company": "Wowrack Indonesia (Cloudraya V2)",
            "role": "Backend Developer",
            "period": "Des 2021 – Sekarang (4+ tahun)",
            "location": "Surabaya, Indonesia",
            "highlights": [
                "Mengembangkan core microservices untuk provisioning Virtual Machine, orkestrasi CloudStack hypervisor, dan siklus server Bare-Metal.",
                "Mengembangkan layanan Object Storage kompatibel S3, dynamic DNS bucket routing, dan pengelolaan block storage berkecepatan tinggi.",
                "Membangun automasi provisioning kluster Kubernetes (K8s) terkelola dan konfigurasi VPC networking.",
                "Merancang pipeline kalkulasi billing berbasis pemakaian riil (metering engine) dan otomasi invoice.",
                "Menjaga keandalan sistem dengan automated testing PHPUnit menyeluruh dan menangani eskalasi teknis level L3 produksi."
            ],
            "tech_stack": ["PHP", "Laravel", "Go", "PostgreSQL", "MySQL", "MongoDB", "Redis", "WebSockets (Reverb)", "Kubernetes", "Docker", "CloudStack", "S3 API", "PHPUnit"]
        },
        {
            "company": "Energeek",
            "role": "Backend Developer",
            "period": "Mar 2019 – Des 2021 (2 tahun 10 bulan)",
            "location": "Surabaya, Indonesia",
            "highlights": [
                "Membangun backend data ingestion untuk proyek sensor telemetri IoT Jembatan Suramadu guna memantau getaran struktural dan cuaca real-time.",
                "Mengembangkan portal manajemen aset dan approval proposal infrastruktur untuk Pemerintah Kota Surabaya & Dishub.",
                "Membangun modul ERP enterprise untuk Petrokimia Gresik (NISA) dan sistem manajemen proyek PT Wijaya Karya (WIKA SIP).",
                "Mengelola deployment VM server dan optimasi performa database PostgreSQL."
            ],
            "tech_stack": ["PHP", "Laravel", "PostgreSQL", "MySQL", "JavaScript", "REST APIs", "Virtual Machines", "Git"]
        }
    ],
    "projects": [
        {
            "title": "Cloudraya V2 Cloud Platform",
            "category": "Cloud IaaS & PaaS Engine",
            "tech": ["PHP", "Laravel", "Go", "PostgreSQL", "Redis", "Kubernetes", "CloudStack", "WebSockets"],
            "desc": "Platform multi-region cloud yang mengorkestrasi VM, Bare-metal, S3 Storage, K8s, dan billing real-time."
        },
        {
            "title": "Suramadu Bridge IoT Telemetry",
            "category": "High-Throughput IoT Data Ingestion",
            "tech": ["PHP", "Laravel", "PostgreSQL", "REST APIs", "Time-Series"],
            "desc": "Data ingestion dan monitoring getaran struktural serta sensor cuaca Jembatan Suramadu real-time."
        },
        {
            "title": "Surabaya Municipal Water Pump & Heavy Equipment Asset Management",
            "category": "Government Portal & Flood Control",
            "tech": ["PHP", "Lumen", "PostgreSQL", "REST APIs", "Mobile Integration"],
            "desc": "Monitoring rumah pompa pengendali banjir dan armada alat berat Pemkot Surabaya."
        },
        {
            "title": "WIKA SIP - Construction Project Resource & Finance Engine",
            "category": "Enterprise ERP",
            "tech": ["PHP", "Laravel", "PostgreSQL", "REST APIs"],
            "desc": "Backend core Sistem Informasi Proyek PT Wijaya Karya Tbk untuk logistik alat/material dan pembayaran vendor."
        },
        {
            "title": "Petrokimia Gresik NISA",
            "category": "Market Intelligence & Competitor Analytics",
            "tech": ["PHP", "Laravel", "PostgreSQL", "JavaScript"],
            "desc": "Sistem monitoring pasar pupuk dan dinamika kompetitor regional PT Petrokimia Gresik."
        }
    ],
    "education": {
        "institution": "Universitas Pembangunan Nasional 'Veteran' Jawa Timur",
        "degree": "Sarjana Komputer (S.Kom) - Teknik Informatika",
        "period": "2014 – 2018"
    }
}
