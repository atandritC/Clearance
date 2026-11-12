import asyncio
from getpass import getpass

from sqlalchemy import select

from clearance.config import settings
from clearance.database import SessionFactory, engine
from clearance.models import User
from clearance.security import hash_password

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
    if not settings.demo_mode:
        raise RuntimeError("Demo user setup is only available when DEMO_MODE=true.")

    if settings.demo_user_password is None:
        password = getpass("Password to use for all local demo users: ")
        confirmation = getpass("Enter the same password again: ")
    else:
        password = settings.demo_user_password.get_secret_value()
        confirmation = password

    if len(password) < 12:
        raise ValueError("The demo password must contain at least 12 characters.")
    if password != confirmation:
        raise ValueError("The passwords did not match.")

    hashed_password = hash_password(password)
    async with SessionFactory() as session:
        result = await session.scalars(select(User))
        existing_users = {user.email.lower(): user for user in result.all()}
        added = 0
        for demo_user in DEMO_USERS:
            email = str(demo_user["email"]).lower()
            existing_user = existing_users.get(email)
            if existing_user is None:
                session.add(
                    User(
                        **{
                            **demo_user,
                            "email": email,
                            "hashed_password": hashed_password,
                        }
                    )
                )
                added += 1
            else:
                existing_user.hashed_password = hashed_password
        await session.commit()

        print(f"Added {added} demo users and set passwords for {len(DEMO_USERS)} accounts.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
