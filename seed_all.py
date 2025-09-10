#!/usr/bin/env python3
"""
Seed all tables with 20 records each: user, job, cv, settings

Run:  python seed_all.py
"""

import random
import string
from datetime import datetime, timedelta, timezone

from app import app, db, User, CV, Job, Settings


def rand_str(prefix: str, n: int = 6) -> str:
    return f"{prefix}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=n))}"


def seed_users(n: int = 20):
    users = []
    for i in range(n):
        username = rand_str("user")
        email = f"{username}@example.com"
        u = User(username=username, email=email, is_admin=True if i == 0 else False)
        u.set_password("password123")
        u.created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 60))
        users.append(u)
        db.session.add(u)
    db.session.commit()
    return users


def seed_jobs(users, n: int = 20):
    titles = [
        "Backend Engineer", "Frontend Engineer", "Fullstack Developer", "Data Scientist",
        "DevOps Engineer", "Mobile Developer", "QA Engineer", "Product Manager",
        "UI/UX Designer", "Solutions Architect",
    ]
    companies = [
        "TechCorp", "InnoSoft", "DataWorks", "CloudNine", "PixelLabs", "GreenAI",
        "NextGen", "BrightApps", "AlphaStack", "NovaDigital",
    ]
    locations = ["Ho Chi Minh City", "Hanoi", "Da Nang"]
    emp_types = ["Full-time", "Part-time", "Contract"]
    work_modes = ["Remote", "On-site", "Hybrid"]

    for i in range(n):
        title = random.choice(titles)
        company = random.choice(companies)
        location = random.choice(locations)
        salary_min = random.choice([900, 1200, 1500, 1800, 2000])
        salary_max = salary_min + random.choice([400, 600, 800, 1200])
        user = random.choice(users)

        job = Job(
            title=title,
            description=f"We are hiring a {title} to join {company}.",
            company=company,
            location=location,
            salary_min=salary_min,
            salary_max=salary_max,
            employment_type=random.choice(emp_types),
            requirements=f"Strong experience in {title} related skills.",
            benefits="Health insurance; Annual bonus; Remote-friendly",
            application_deadline=datetime.now(timezone.utc) + timedelta(days=random.randint(10, 60)),
            hiring_quantity=random.randint(1, 3),
            experience_level=random.choice(["Entry", "Mid", "Senior", "Lead"]),
            work_mode=random.choice(work_modes),
            industry=random.choice(["Technology", "Finance", "E-commerce", "Healthcare"]),
            skills_required="Python, React, SQL, Docker",
            education_required=random.choice(["Bachelor", "Master", "High School"]),
            is_active=True,
            user_id=user.id,
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
            updated_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 10)),

            # Matching criteria (JD-side)
            criteria_seniority=random.choice(["Entry", "Mid", "Senior", None]),
            criteria_core_skills="Python, React, Docker",
            criteria_language=random.choice(["English B2", "Japanese N3", None]),
            criteria_work_model=random.choice(work_modes + [None]),
            criteria_visa_required=random.choice([None, 0, 1]),
            criteria_secondary_skills="GraphQL, AWS",
            criteria_years_experience=random.choice([None, 1, 2, 3, 5, 7]),
            criteria_recency_years=random.choice([None, 1, 2, 3, 4, 5]),
            criteria_domain=random.choice(["Fintech", "E-commerce", None]),
            criteria_kpi_required=random.choice([None, 0, 1]),
            criteria_stack_versions="React 18, Node 18, AWS SDK v3",
            criteria_soft_skills="Communication, Teamwork",
            criteria_culture_process=random.choice(["Agile", "Scrum", None]),
        )
        db.session.add(job)
    db.session.commit()


def seed_cvs(users, n: int = 20):
    names = [
        "Nguyen Van A", "Tran Thi B", "Le Van C", "Pham Thi D", "Hoang Van E",
        "Do Thi F", "Phan Van G", "Bui Thi H", "Vu Van I", "Dang Thi K",
    ]
    skills_pool = ["Python", "React", "Node", "SQL", "Docker", "AWS", "GCP", "Kubernetes"]

    for i in range(n):
        user = random.choice(users)
        name = random.choice(names) + f" {i}"
        email = f"{rand_str('cv', 5)}@mail.com"
        cv = CV(
            name=name,
            email=email,
            phone=f"09{random.randint(10000000, 99999999)}",
            address=random.choice(["HCMC", "Hanoi", "Da Nang", "Remote"]),
            education=random.choice(["Bachelor of IT", "Master of CS", "High School"]),
            experience="Worked on multiple projects using modern stacks.",
            skills=", ".join(random.sample(skills_pool, k=random.randint(3, 6))),
            file_path=None,
            avatar=None,
            user_id=user.id,
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
            updated_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 10)),

            # Matching criteria (CV-side)
            cv_seniority=random.choice(["Entry", "Mid", "Senior", None]),
            cv_core_skills=", ".join(random.sample(skills_pool, k=random.randint(2, 5))),
            cv_languages=random.choice(["English B2", "Japanese N3", "", None]),
            cv_work_model=random.choice(["Remote", "On-site", "Hybrid", None]),
            cv_visa_status=random.choice(["Eligible", "Not Eligible", None]),
            cv_secondary_skills="GraphQL, Redis",
            cv_years_experience=random.choice([0, 1, 2, 3, 5, 7]),
            cv_recency_years=random.choice([1, 2, 3, 4, 5]),
            cv_domain=random.choice(["Fintech", "E-commerce", "Healthcare", None]),
            cv_kpi="Improved performance by 30%",
            cv_stack_versions="React 18, Node 18",
            cv_soft_skills="Teamwork, Leadership",
            cv_culture_process=random.choice(["Agile", "Scrum", None]),
        )
        db.session.add(cv)
    db.session.commit()


def seed_settings(n: int = 20):
    for i in range(n):
        s = Settings(
            auto_extract=random.choice([True, False]),
            email_notifications=random.choice([True, False]),
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
            updated_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 10)),
        )
        db.session.add(s)
    db.session.commit()


def main():
    with app.app_context():
        print("Clearing existing data...")
        # Order for FK safety
        CV.query.delete()
        Job.query.delete()
        Settings.query.delete()
        User.query.delete()
        db.session.commit()

        print("Seeding users...")
        users = seed_users(20)
        print("Seeding jobs...")
        seed_jobs(users, 20)
        print("Seeding CVs...")
        seed_cvs(users, 20)
        print("Seeding settings...")
        seed_settings(20)
        print("Done. Seeded 20 records for each table.")


if __name__ == "__main__":
    main()


