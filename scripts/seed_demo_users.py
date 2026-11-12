import asyncio
from getpass import getpass
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from clearance.config import settings
from clearance.database import SessionFactory, engine
from clearance.models import EmployeeLeaveBalance, User
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
        "is_admin": True,
    },
]

DEMO_LEAVE_BALANCES = {
    "daemon.targaryen@astervale.example": (Decimal("8.5"), Decimal("4.0")),
    "mikasa.ackerman@astervale.example": (Decimal("12.0"), Decimal("6.0")),
    "kakashi.hatake@astervale.example": (Decimal("15.5"), Decimal("7.0")),
    "patrick.jane@astervale.example": (Decimal("6.0"), Decimal("3.0")),
    "rukia.kuchki@astervale.example": (Decimal("9.5"), Decimal("5.0")),
    "sofia.gigante@astervale.example": (Decimal("18.0"), Decimal("8.0")),
}


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
            account_data = {
                **demo_user,
                "email": email,
                "hashed_password": hashed_password,
            }
            if existing_user is None:
                session.add(User(**account_data))
                added += 1
            else:
                existing_user.hashed_password = hashed_password
                existing_user.display_name = str(account_data["display_name"])
                existing_user.role = str(account_data["role"])
                existing_user.department = str(account_data["department"])
                existing_user.is_active = bool(account_data["is_active"])
                existing_user.is_admin = bool(account_data.get("is_admin", False))
        await session.flush()

        seeded_users = await session.scalars(select(User))
        existing_balance_user_ids = set(
            await session.scalars(select(EmployeeLeaveBalance.user_id))
        )
        for user in seeded_users.all():
            if user.email in DEMO_LEAVE_BALANCES and user.id not in existing_balance_user_ids:
                annual_days, sick_days = DEMO_LEAVE_BALANCES[user.email]
                session.add(
                    EmployeeLeaveBalance(
                        user_id=user.id,
                        annual_days_remaining=annual_days,
                        sick_days_remaining=sick_days,
                        as_of=date.today(),
                    )
                )
        await session.commit()

        print(f"Added {added} demo users and set passwords for {len(DEMO_USERS)} accounts.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
