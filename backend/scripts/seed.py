"""
Data Seeder — Generates 10K+ realistic records for the ECRM Platform.
Run: python -m scripts.seed

Creates:
  - 3 organizations (tenants)
  - 5 users per org (different roles)
  - 10K leads total (~3.3K per org)
  - 5K contacts
  - 2K accounts
  - 1K deals
  - 5K tasks & activities
  - 500 meetings
"""
import sys
import os
import random
import uuid
from datetime import datetime, timezone, timedelta

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import hash_password
from app.models.models import (
    Organization, User, Lead, Contact, Account, Deal, Task, Meeting,
    Activity, Notification,
    UserRole, LeadStatus, LeadSource, DealStage, TaskStatus, TaskPriority,
    ActivityType, MeetingStatus,
)
from app.tasks.lead_scoring import calculate_lead_score

fake = Faker()
Faker.seed(42)
random.seed(42)

# ── Config ────────────────────────────────────────────────────────────────────
NUM_ORGS = 3
USERS_PER_ORG = 5
LEADS_PER_ORG = 3334
ACCOUNTS_PER_ORG = 666
CONTACTS_PER_ORG = 1667
DEALS_PER_ORG = 333
TASKS_PER_ORG = 1667
MEETINGS_PER_ORG = 167
ACTIVITIES_PER_ORG = 1000


def random_date(days_back=365):
    return datetime.now(timezone.utc) - timedelta(days=random.randint(0, days_back))


def create_organizations(session: Session) -> list[Organization]:
    orgs = []
    org_data = [
        ("Acme Corp CRM", "acme-corp", "Technology", "201-500"),
        ("Global Sales Co", "global-sales", "Sales", "51-200"),
        ("StartupXYZ", "startup-xyz", "SaaS", "1-50"),
    ]
    for name, slug, industry, size in org_data:
        org = Organization(
            id=str(uuid.uuid4()),
            name=name,
            slug=slug,
            industry=industry,
            size=size,
            domain=f"{slug.replace('-', '')}.com",
            is_active=True,
            subscription_plan="enterprise",
            max_users=50,
        )
        session.add(org)
        orgs.append(org)
    session.flush()
    print(f"✓ Created {len(orgs)} organizations")
    return orgs


def create_users(session: Session, orgs: list[Organization]) -> dict[str, list[User]]:
    org_users: dict[str, list[User]] = {}
    roles = [UserRole.ORG_ADMIN, UserRole.SALES_MANAGER, UserRole.SALES_REP, UserRole.SALES_REP, UserRole.VIEWER]

    for org in orgs:
        users = []
        for i, role in enumerate(roles):
            user = User(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                email=f"user{i+1}@{org.slug.replace('-', '')}.com",
                hashed_password=hash_password("Password123!"),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role=role,
                is_active=True,
                is_verified=True,
                phone=fake.phone_number()[:30],
                timezone="UTC",
                last_login_at=random_date(30),
            )
            session.add(user)
            users.append(user)
        org_users[org.id] = users

    session.flush()
    total = sum(len(v) for v in org_users.values())
    print(f"✓ Created {total} users")
    return org_users


def create_accounts(session: Session, orgs: list[Organization], org_users: dict) -> dict[str, list[Account]]:
    org_accounts: dict[str, list[Account]] = {}
    industries = ["Technology", "Finance", "Healthcare", "Retail", "Manufacturing", "Education", "Real Estate"]
    sizes = ["1-10", "11-50", "51-200", "201-500", "500+"]

    for org in orgs:
        accounts = []
        users = org_users[org.id]
        for _ in range(ACCOUNTS_PER_ORG):
            account = Account(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                name=fake.company(),
                domain=fake.domain_name(),
                industry=random.choice(industries),
                size=random.choice(sizes),
                annual_revenue=round(random.uniform(100_000, 50_000_000), 2),
                employee_count=random.randint(5, 5000),
                phone=fake.phone_number()[:30],
                website=f"https://{fake.domain_name()}",
                city=fake.city(),
                country=fake.country(),
                description=fake.text(max_nb_chars=200),
                owner_id=random.choice(users).id,
            )
            session.add(account)
            accounts.append(account)
        org_accounts[org.id] = accounts

    session.flush()
    total = sum(len(v) for v in org_accounts.values())
    print(f"✓ Created {total} accounts")
    return org_accounts


def create_leads(session: Session, orgs: list[Organization], org_users: dict) -> dict[str, list[Lead]]:
    org_leads: dict[str, list[Lead]] = {}
    statuses = list(LeadStatus)
    sources = list(LeadSource)
    industries = ["Technology", "Finance", "Healthcare", "Retail", "Manufacturing", "Education"]

    for org in orgs:
        leads = []
        users = org_users[org.id]
        for _ in range(LEADS_PER_ORG):
            source = random.choice(sources)
            status = random.choices(statuses, weights=[30, 20, 20, 10, 15, 5])[0]
            lead_data = {
                "email": fake.email() if random.random() > 0.1 else None,
                "phone": fake.phone_number()[:30] if random.random() > 0.2 else None,
                "company": fake.company() if random.random() > 0.15 else None,
                "annual_revenue": round(random.uniform(0, 10_000_000), 2) if random.random() > 0.4 else None,
                "employee_count": random.randint(1, 1000) if random.random() > 0.5 else None,
                "source": source.value,
                "status": status.value,
            }
            lead = Lead(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=lead_data["email"],
                phone=lead_data["phone"],
                company=lead_data["company"],
                title=fake.job()[:150] if random.random() > 0.3 else None,
                status=status,
                source=source,
                annual_revenue=lead_data["annual_revenue"],
                employee_count=lead_data["employee_count"],
                industry=random.choice(industries) if random.random() > 0.3 else None,
                city=fake.city() if random.random() > 0.3 else None,
                country=fake.country() if random.random() > 0.3 else None,
                description=fake.text(max_nb_chars=200) if random.random() > 0.5 else None,
                assigned_to_id=random.choice(users).id if random.random() > 0.2 else None,
                score=calculate_lead_score(lead_data),
                converted_at=random_date(180) if status == LeadStatus.CONVERTED else None,
                last_contacted_at=random_date(30) if random.random() > 0.5 else None,
                created_at=random_date(365),
                updated_at=random_date(30),
            )
            session.add(lead)
            leads.append(lead)
        org_leads[org.id] = leads

    session.flush()
    total = sum(len(v) for v in org_leads.values())
    print(f"✓ Created {total} leads")
    return org_leads


def create_contacts(session: Session, orgs: list[Organization], org_users: dict, org_accounts: dict) -> dict[str, list[Contact]]:
    org_contacts: dict[str, list[Contact]] = {}

    for org in orgs:
        contacts = []
        users = org_users[org.id]
        accounts = org_accounts[org.id]
        for _ in range(CONTACTS_PER_ORG):
            contact = Contact(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email() if random.random() > 0.05 else None,
                phone=fake.phone_number()[:30] if random.random() > 0.2 else None,
                title=fake.job()[:150] if random.random() > 0.3 else None,
                department=random.choice(["Sales", "Marketing", "Engineering", "Finance", "HR", "Operations"]) if random.random() > 0.3 else None,
                account_id=random.choice(accounts).id if random.random() > 0.3 else None,
                city=fake.city() if random.random() > 0.3 else None,
                country=fake.country() if random.random() > 0.3 else None,
                description=fake.text(max_nb_chars=200) if random.random() > 0.6 else None,
                owner_id=random.choice(users).id if random.random() > 0.2 else None,
                linkedin_url=f"https://linkedin.com/in/{fake.user_name()}" if random.random() > 0.5 else None,
                created_at=random_date(365),
            )
            session.add(contact)
            contacts.append(contact)
        org_contacts[org.id] = contacts

    session.flush()
    total = sum(len(v) for v in org_contacts.values())
    print(f"✓ Created {total} contacts")
    return org_contacts


def create_deals(session: Session, orgs: list[Organization], org_users: dict, org_accounts: dict, org_contacts: dict) -> dict[str, list[Deal]]:
    org_deals: dict[str, list[Deal]] = {}
    stages = list(DealStage)
    stage_weights = [15, 20, 20, 15, 15, 15]

    for org in orgs:
        deals = []
        users = org_users[org.id]
        accounts = org_accounts[org.id]
        contacts = org_contacts[org.id]
        for _ in range(DEALS_PER_ORG):
            stage = random.choices(stages, weights=stage_weights)[0]
            value = round(random.uniform(1000, 500_000), 2)
            probability = {
                DealStage.PROSPECTING: 10,
                DealStage.QUALIFICATION: 25,
                DealStage.PROPOSAL: 50,
                DealStage.NEGOTIATION: 75,
                DealStage.CLOSED_WON: 100,
                DealStage.CLOSED_LOST: 0,
            }[stage]

            deal = Deal(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                name=f"Deal: {fake.company()} - {fake.bs().title()[:50]}",
                stage=stage,
                value=value,
                probability=probability,
                currency="USD",
                expected_close_date=random_date(-90) if random.random() > 0.3 else None,  # future
                actual_close_date=random_date(180) if stage in [DealStage.CLOSED_WON, DealStage.CLOSED_LOST] else None,
                contact_id=random.choice(contacts).id if random.random() > 0.3 else None,
                account_id=random.choice(accounts).id if random.random() > 0.3 else None,
                assigned_to_id=random.choice(users).id if random.random() > 0.2 else None,
                description=fake.text(max_nb_chars=300) if random.random() > 0.5 else None,
                lost_reason=random.choice(["Price", "Competitor", "No budget", "Timing"]) if stage == DealStage.CLOSED_LOST else None,
                created_at=random_date(365),
            )
            session.add(deal)
            deals.append(deal)
        org_deals[org.id] = deals

    session.flush()
    total = sum(len(v) for v in org_deals.values())
    print(f"✓ Created {total} deals")
    return org_deals


def create_tasks(session: Session, orgs: list[Organization], org_users: dict, org_deals: dict) -> None:
    statuses = list(TaskStatus)
    priorities = list(TaskPriority)

    for org in orgs:
        users = org_users[org.id]
        deals = org_deals[org.id]
        for _ in range(TASKS_PER_ORG):
            status = random.choice(statuses)
            task = Task(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                title=fake.bs().title()[:255],
                description=fake.text(max_nb_chars=200) if random.random() > 0.5 else None,
                status=status,
                priority=random.choice(priorities),
                due_date=datetime.now(timezone.utc) + timedelta(days=random.randint(-30, 60)) if random.random() > 0.3 else None,
                completed_at=random_date(30) if status == TaskStatus.COMPLETED else None,
                assigned_to_id=random.choice(users).id if random.random() > 0.2 else None,
                created_by_id=random.choice(users).id,
                deal_id=random.choice(deals).id if random.random() > 0.5 else None,
                created_at=random_date(180),
            )
            session.add(task)

    session.flush()
    print(f"✓ Created ~{NUM_ORGS * TASKS_PER_ORG} tasks")


def create_meetings(session: Session, orgs: list[Organization], org_users: dict) -> None:
    statuses = list(MeetingStatus)

    for org in orgs:
        users = org_users[org.id]
        for _ in range(MEETINGS_PER_ORG):
            start = datetime.now(timezone.utc) + timedelta(days=random.randint(-60, 60), hours=random.randint(8, 17))
            end = start + timedelta(hours=random.choice([0.5, 1, 1.5, 2]))
            meeting = Meeting(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                title=f"Meeting: {fake.bs().title()[:200]}",
                description=fake.text(max_nb_chars=200) if random.random() > 0.5 else None,
                status=random.choice(statuses),
                start_time=start,
                end_time=end,
                location=fake.city() if random.random() > 0.5 else None,
                meeting_url=f"https://meet.google.com/{fake.uuid4()[:10]}" if random.random() > 0.5 else None,
                organizer_id=random.choice(users).id,
                attendees=[random.choice(users).id for _ in range(random.randint(1, 3))],
                created_at=random_date(90),
            )
            session.add(meeting)

    session.flush()
    print(f"✓ Created ~{NUM_ORGS * MEETINGS_PER_ORG} meetings")


def create_activities(session: Session, orgs: list[Organization], org_users: dict, org_leads: dict, org_deals: dict) -> None:
    act_types = list(ActivityType)

    for org in orgs:
        users = org_users[org.id]
        leads = org_leads[org.id]
        deals = org_deals[org.id]
        for _ in range(ACTIVITIES_PER_ORG):
            act_type = random.choice(act_types)
            activity = Activity(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                user_id=random.choice(users).id,
                type=act_type,
                title=f"{act_type.value.replace('_', ' ').title()}: {fake.bs()[:200]}",
                description=fake.text(max_nb_chars=200) if random.random() > 0.5 else None,
                lead_id=random.choice(leads).id if random.random() > 0.6 else None,
                deal_id=random.choice(deals).id if random.random() > 0.6 else None,
                created_at=random_date(180),
            )
            session.add(activity)

    session.flush()
    print(f"✓ Created ~{NUM_ORGS * ACTIVITIES_PER_ORG} activities")


def create_notifications(session: Session, orgs: list[Organization], org_users: dict) -> None:
    types = ["info", "success", "warning", "error"]
    messages = [
        "A new lead has been assigned to you.",
        "Deal stage updated to Negotiation.",
        "Task is due tomorrow.",
        "New meeting scheduled.",
        "Lead score updated.",
        "Monthly revenue report is ready.",
    ]

    for org in orgs:
        for user in org_users[org.id]:
            for _ in range(random.randint(3, 10)):
                notif = Notification(
                    id=str(uuid.uuid4()),
                    organization_id=org.id,
                    user_id=user.id,
                    title=random.choice(["New Assignment", "Deal Update", "Task Reminder", "Meeting Alert"]),
                    message=random.choice(messages),
                    type=random.choice(types),
                    is_read=random.random() > 0.3,
                    created_at=random_date(30),
                )
                session.add(notif)

    session.flush()
    print("✓ Created notifications")


def main():
    print("=" * 60)
    print("ECRM Platform — Data Seeder")
    print("=" * 60)

    engine = create_engine(settings.DATABASE_URL_SYNC, echo=False)

    # Import all models to ensure tables exist
    from app.core.database import Base
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        try:
            print("\nSeeding data...")
            orgs = create_organizations(session)
            org_users = create_users(session, orgs)
            org_accounts = create_accounts(session, orgs, org_users)
            org_leads = create_leads(session, orgs, org_users)
            org_contacts = create_contacts(session, orgs, org_users, org_accounts)
            org_deals = create_deals(session, orgs, org_users, org_accounts, org_contacts)
            create_tasks(session, orgs, org_users, org_deals)
            create_meetings(session, orgs, org_users)
            create_activities(session, orgs, org_users, org_leads, org_deals)
            create_notifications(session, orgs, org_users)

            session.commit()
            print("\n" + "=" * 60)
            print("✅ Seeding complete!")
            print(f"   Organizations: {NUM_ORGS}")
            print(f"   Users: {NUM_ORGS * USERS_PER_ORG}")
            print(f"   Leads: ~{NUM_ORGS * LEADS_PER_ORG}")
            print(f"   Contacts: ~{NUM_ORGS * CONTACTS_PER_ORG}")
            print(f"   Accounts: ~{NUM_ORGS * ACCOUNTS_PER_ORG}")
            print(f"   Deals: ~{NUM_ORGS * DEALS_PER_ORG}")
            print(f"   Tasks: ~{NUM_ORGS * TASKS_PER_ORG}")
            print(f"   Meetings: ~{NUM_ORGS * MEETINGS_PER_ORG}")
            print(f"   Activities: ~{NUM_ORGS * ACTIVITIES_PER_ORG}")
            print("=" * 60)
            print("\nAdmin credentials (per org):")
            for org in orgs:
                print(f"  [{org.name}] user1@{org.slug.replace('-', '')}.com / Password123!")

        except Exception as e:
            session.rollback()
            print(f"\n❌ Seeding failed: {e}")
            raise


if __name__ == "__main__":
    main()
