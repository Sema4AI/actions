import uuid
from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel

from sema4ai.mcp import prompt, resource, tool


class Ticket(BaseModel):
    id: str
    title: str
    description: str
    priority: str
    status: str
    created_at: str
    assigned_to: Optional[str]


# Global storage for tickets
TICKETS: Dict[str, Ticket] = {}


def _generate_ticket_id() -> str:
    """Generate a unique ticket ID."""
    return f"TICKET-{uuid.uuid4().hex[:8].upper()}"


# Tool example for ticket management
@tool
def create_ticket(title: str, description: str, priority: str = "medium") -> Ticket:
    """
    Create a new ticket in the system.

    Args:
        title: The title of the ticket
        description: Detailed description of the ticket
        priority: Priority level (low, medium, high)

    Returns:
        Dictionary containing the created ticket information
    """
    ticket_id = _generate_ticket_id()
    ticket: Ticket = Ticket(
        id=ticket_id,
        title=title,
        description=description,
        priority=priority,
        status="open",
        created_at=datetime.utcnow().isoformat(),
        assigned_to=None,
    )
    TICKETS[ticket_id] = ticket
    return ticket


# Resource example for ticket management
@resource(display_name="tickets://{ticket_id}")
def get_ticket_details(ticket_id: str) -> Ticket:
    """
    Get detailed information about a specific ticket.

    Args:
        ticket_id: The ID of the ticket to retrieve

    Returns:
        Dictionary containing the ticket details
    """
    if ticket_id not in TICKETS:
        raise ValueError(f"Ticket {ticket_id} not found")
    return TICKETS[ticket_id]


# Prompt example for ticket management
@prompt
def generate_ticket_summary(ticket_data: Ticket) -> str:
    """
    Generate a human-readable summary of a ticket.

    Args:
        ticket_data: Dictionary containing ticket information

    Returns:
        A formatted string containing the ticket summary
    """
    return f"""
    Please provide a concise summary of the following ticket:
    
    Ticket ID: {ticket_data.id}
    Title: {ticket_data.title}
    Priority: {ticket_data.priority}
    Status: {ticket_data.status}
    Created At: {ticket_data.created_at}
    Assigned To: {ticket_data.assigned_to or 'Unassigned'}
    
    Description:
    {ticket_data.description}
    
    Please summarize the key points and suggest next steps.
    """
