
"""
Appointment Manager

Provides a core AppointmentManager class that handles creating, cancelling,
looking up, and rescheduling appointments, including conflict detection and
basic business-hours validation.

Business rules (defaults, all overridable via constructor):
  - Business hours: 10:00 – 18:00 (local time)
  - Appointments must not overlap with existing ones
  - Appointment duration must be at least 1 minute
"""

from __future__ import annotations

import uuid
from datetime import datetime, time
from typing import List, Optional


class Appointment:
    """Represents a single appointment."""

    def __init__(
        self,
        appointment_id: str,
        name: str,
        phone: str,
        email: str,
        service_type: str,
        start: datetime,
        end: datetime,
    ) -> None:
        self.id = appointment_id
        self.name = name
        self.phone = phone
        self.email = email
        self.service_type = service_type
        self.start = start
        self.end = end

    def overlaps(self, other: "Appointment") -> bool:
        """Return True if this appointment overlaps with *other*."""
        return self.start < other.end and other.start < self.end

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Appointment(id={self.id!r}, name={self.name!r}, "
            f"start={self.start.isoformat()}, end={self.end.isoformat()})"
        )


class AppointmentManager:
    """
    In-memory appointment manager.

    Parameters
    ----------
    business_hours_start:
        Earliest time (inclusive) at which appointments may begin.
    business_hours_end:
        Latest time (exclusive) by which all appointments must finish.
    """

    def __init__(
        self,
        business_hours_start: time = time(10, 0),
        business_hours_end: time = time(18, 0),
    ) -> None:
        self._appointments: List[Appointment] = []
        self.business_hours_start = business_hours_start
        self.business_hours_end = business_hours_end

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def book_appointment(
        self,
        name: str,
        phone: str,
        email: str,
        service_type: str,
        start: datetime,
        end: datetime,
    ) -> Appointment:
        """
        Book a new appointment.

        Raises
        ------
        ValueError
            If the time slot is outside business hours, the duration is
            invalid, or the slot conflicts with an existing appointment.
        """
        self._validate_slot(start, end)
        candidate = Appointment(
            appointment_id=str(uuid.uuid4()),
            name=name,
            phone=phone,
            email=email,
            service_type=service_type,
            start=start,
            end=end,
        )
        for existing in self._appointments:
            if candidate.overlaps(existing):
                raise ValueError(
                    f"Slot conflicts with existing appointment '{existing.id}' "
                    f"({existing.start.isoformat()} – {existing.end.isoformat()})"
                )
        self._appointments.append(candidate)
        return candidate

    def cancel_appointment(self, appointment_id: str) -> bool:
        """
        Cancel an appointment by ID.

        Returns
        -------
        bool
            True if an appointment was found and removed, False otherwise.
        """
        initial_length = len(self._appointments)
        self._appointments = [a for a in self._appointments if a.id != appointment_id]
        return len(self._appointments) < initial_length

    def lookup_appointment(
        self,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> List[Appointment]:
        """
        Find appointments by phone number and/or email address.

        At least one of *phone* or *email* must be supplied.

        Returns
        -------
        list[Appointment]
            All appointments that match the given criteria (case-insensitive
            for email).
        """
        if phone is None and email is None:
            raise ValueError("At least one of 'phone' or 'email' must be provided.")
        results = []
        for appt in self._appointments:
            phone_match = phone is not None and appt.phone == phone
            email_match = (
                email is not None and appt.email.lower() == email.lower()
            )
            if phone_match or email_match:
                results.append(appt)
        return results

    def reschedule_appointment(
        self,
        appointment_id: str,
        new_start: datetime,
        new_end: datetime,
    ) -> Appointment:
        """
        Move an existing appointment to a new time slot.

        Raises
        ------
        ValueError
            If the appointment is not found, the new slot is outside business
            hours, the duration is invalid, or the new slot conflicts with
            another appointment.
        """
        appointment = self._get_by_id(appointment_id)
        if appointment is None:
            raise ValueError(f"Appointment '{appointment_id}' not found.")
        self._validate_slot(new_start, new_end)
        for existing in self._appointments:
            if existing.id == appointment_id:
                continue
            placeholder = Appointment(
                appointment_id=appointment_id,
                name=appointment.name,
                phone=appointment.phone,
                email=appointment.email,
                service_type=appointment.service_type,
                start=new_start,
                end=new_end,
            )
            if placeholder.overlaps(existing):
                raise ValueError(
                    f"New slot conflicts with existing appointment '{existing.id}' "
                    f"({existing.start.isoformat()} – {existing.end.isoformat()})"
                )
        appointment.start = new_start
        appointment.end = new_end
        return appointment

    def list_appointments(self) -> List[Appointment]:
        """Return all appointments sorted by start time."""
        return sorted(self._appointments, key=lambda a: a.start)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_slot(self, start: datetime, end: datetime) -> None:
        """Raise ValueError if the slot is invalid."""
        if end <= start:
            raise ValueError("Appointment end time must be after start time.")
        if start.time() < self.business_hours_start:
            raise ValueError(
                f"Appointment start {start.time()} is before business hours "
                f"({self.business_hours_start})."
            )
        if end.time() > self.business_hours_end:
            raise ValueError(
                f"Appointment end {end.time()} is after business hours "
                f"({self.business_hours_end})."
            )

    def _get_by_id(self, appointment_id: str) -> Optional[Appointment]:
        for appt in self._appointments:
            if appt.id == appointment_id:
                return appt
        return None


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from datetime import datetime

    manager = AppointmentManager()

    appt1 = manager.book_appointment(
        name="John Doe",
        phone="+12145551001",
        email="john@example.com",
        service_type="consultation",
        start=datetime(2025, 11, 10, 10, 0),
        end=datetime(2025, 11, 10, 11, 0),
    )
    appt2 = manager.book_appointment(
        name="Jane Smith",
        phone="+12145551002",
        email="jane@example.com",
        service_type="support",
        start=datetime(2025, 11, 10, 11, 0),
        end=datetime(2025, 11, 10, 11, 30),
    )
    appt3 = manager.book_appointment(
        name="Peter Jones",
        phone="+12145551003",
        email="peter@example.com",
        service_type="maintenance",
        start=datetime(2025, 11, 10, 12, 0),
        end=datetime(2025, 11, 10, 13, 0),
    )

    print("All appointments:")
    for a in manager.list_appointments():
        print(f"  {a}")

    print(f"\nLooking up by phone '+12145551002': {manager.lookup_appointment(phone='+12145551002')}")

    manager.cancel_appointment(appt2.id)
    print(f"\nAfter cancelling appt2, appointments remaining: {len(manager.list_appointments())}")

    manager.reschedule_appointment(
        appt3.id,
        new_start=datetime(2025, 11, 10, 11, 0),
        new_end=datetime(2025, 11, 10, 12, 0),
    )
    print(f"\nAfter rescheduling appt3 to 11:00-12:00:")
    for a in manager.list_appointments():
        print(f"  {a}")

