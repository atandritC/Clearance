from datetime import date
from typing import Literal
from uuid import uuid4

from mcp.server import MCPServer
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from clearance.database import SessionFactory
from clearance.models import EmployeeLeaveBalance, ITTicket, User


class LeaveBalanceResult(BaseModel):
    user_id: int
    annual_days_remaining: str
    sick_days_remaining: str
    as_of: date


class TicketResult(BaseModel):
    ticket_number: str
    title: str
    priority: str
    status: str


class TicketListResult(BaseModel):
    tickets: list[TicketResult]


def can_view_leave_balance(requesting_user: User, target_user_id: int) -> bool:
    return (
        target_user_id == requesting_user.id
        or requesting_user.role == "hr_manager"
        or requesting_user.is_admin is True
    )


def create_clearance_mcp_server(
    user: User,
    allow_ticket_creation: bool = False,
    session_factory: async_sessionmaker = SessionFactory,
) -> MCPServer:
    server = MCPServer(
        "Clearance HR and IT",
        instructions=(
            "Tools for the signed-in employee's synthetic HR and IT records. "
            "The application supplies the employee identity; never ask for a password."
        ),
    )

    @server.tool(
        description=(
            "Read the signed-in employee's remaining annual and sick leave. "
            "An HR manager or administrator may provide another active employee ID."
        )
    )
    async def get_leave_balance(employee_id: int | None = None) -> LeaveBalanceResult:
        target_user_id = user.id if employee_id is None else employee_id
        if not can_view_leave_balance(user, target_user_id):
            raise ValueError("That leave balance cannot be accessed.")

        async with session_factory() as session:
            target_user = await session.get(User, target_user_id)
            balance = await session.get(EmployeeLeaveBalance, target_user_id)
            if target_user is None or not target_user.is_active or balance is None:
                raise ValueError("That leave balance cannot be accessed.")
            return LeaveBalanceResult(
                user_id=target_user.id,
                annual_days_remaining=str(balance.annual_days_remaining),
                sick_days_remaining=str(balance.sick_days_remaining),
                as_of=balance.as_of,
            )

    if allow_ticket_creation:

        @server.tool(
            description=(
                "Create an IT support ticket for the signed-in employee. "
                "Use a short title, explain the problem, and choose low, normal, or high priority."
            )
        )
        async def create_it_ticket(
            title: str,
            description: str,
            priority: Literal["low", "normal", "high"] = "normal",
        ) -> TicketResult:
            clean_title = title.strip()
            clean_description = description.strip()
            if not 5 <= len(clean_title) <= 120:
                raise ValueError("The ticket title must be between 5 and 120 characters.")
            if not 10 <= len(clean_description) <= 2000:
                raise ValueError(
                    "The ticket description must be between 10 and 2000 characters."
                )

            ticket_number = f"IT-{date.today().year}-{uuid4().hex[:8].upper()}"
            async with session_factory() as session:
                ticket = ITTicket(
                    ticket_number=ticket_number,
                    user_id=user.id,
                    title=clean_title,
                    description=clean_description,
                    priority=priority,
                    status="open",
                )
                session.add(ticket)
                await session.commit()
                return TicketResult(
                    ticket_number=ticket.ticket_number,
                    title=ticket.title,
                    priority=ticket.priority,
                    status=ticket.status,
                )

    @server.tool(
        description="List recent IT support tickets created by the signed-in employee."
    )
    async def list_my_it_tickets(limit: int = 5) -> TicketListResult:
        if not 1 <= limit <= 20:
            raise ValueError("The ticket list limit must be between 1 and 20.")
        async with session_factory() as session:
            tickets = await session.scalars(
                select(ITTicket)
                .where(ITTicket.user_id == user.id)
                .order_by(desc(ITTicket.created_at))
                .limit(limit)
            )
            return TicketListResult(
                tickets=[
                    TicketResult(
                        ticket_number=ticket.ticket_number,
                        title=ticket.title,
                        priority=ticket.priority,
                        status=ticket.status,
                    )
                    for ticket in tickets.all()
                ]
            )

    return server
