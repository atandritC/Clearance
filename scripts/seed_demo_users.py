import asyncio
from sqlalchemy import select

from clearance.database import SessionFactory, engine
from clearance.models import User

DEMO_USERS = [
    {
        "email": "daemon.targaryen@astervale.example",
        "display_name": "Daemon Targaryen",
        "role": "intern",
        "department": "IT Operations",
        "is_active": True,
    },
    {
        "email": "mikasa.ackerman@astervale.example",
        "display_name": "Mikasa Ackerman",
        "role": "engineer",
        "department": "IT Operations",
        "is_active": True,
    },
    {
        "email": "kakashi.hatake@astervale.example",
        "display_name": "Kakashi Hatake",
        "role": "hr_manager",
        "department": "People Operations",
        "is_active": True,
    },
    {
        "email": "patrick.jane@astervale.example",
        "display_name": "Patrick Jane",
        "role": "finance_analyst",
        "department": "Finance",
        "is_active": True,
    },
    {
        "email": "rukia.kuchki@astervale.example",
        "display_name": "Rukia Kuchki",
        "role": "project_lead",
        "department": "Product Strategy",
        "is_active": True,
    },
    {
        "email": "sofia.gigante@astervale.example",
        "display_name": "Sofia Gigante",
        "role": "executive",
        "department": "Executive Office",
        "is_active": True,
    },
]


async def main() -> None:
    async with SessionFactory() as session:
        result = await session.scalars(select(User.email))
        existing_emails = set(result.all())

        new_users = [
            User(**user) for user in DEMO_USERS if user["email"] not in existing_emails
        ]

        session.add_all(new_users)
        await session.commit()

        print(f"Added {len(new_users)} demo users.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
