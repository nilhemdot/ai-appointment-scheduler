"""Unit tests for AppointmentManager."""

import unittest
from datetime import datetime, time

from appointment_manager import Appointment, AppointmentManager


def _dt(hour: int, minute: int = 0, day: int = 10) -> datetime:
    """Helper: create a datetime on 2025-11-{day} at hour:minute."""
    return datetime(2025, 11, day, hour, minute)


class TestBookAppointment(unittest.TestCase):
    def setUp(self):
        self.manager = AppointmentManager()

    def test_book_returns_appointment(self):
        appt = self.manager.book_appointment(
            name="Alice",
            phone="+10000000001",
            email="alice@example.com",
            service_type="consultation",
            start=_dt(10),
            end=_dt(11),
        )
        self.assertIsInstance(appt, Appointment)
        self.assertEqual(appt.name, "Alice")
        self.assertIsNotNone(appt.id)

    def test_book_adds_to_list(self):
        self.manager.book_appointment(
            name="Bob", phone="+1", email="b@x.com",
            service_type="support", start=_dt(10), end=_dt(11),
        )
        self.assertEqual(len(self.manager.list_appointments()), 1)

    def test_conflict_raises(self):
        self.manager.book_appointment(
            name="A", phone="+1", email="a@x.com",
            service_type="s", start=_dt(10), end=_dt(11),
        )
        with self.assertRaises(ValueError):
            self.manager.book_appointment(
                name="B", phone="+2", email="b@x.com",
                service_type="s", start=_dt(10, 30), end=_dt(11, 30),
            )

    def test_adjacent_slots_do_not_conflict(self):
        self.manager.book_appointment(
            name="A", phone="+1", email="a@x.com",
            service_type="s", start=_dt(10), end=_dt(11),
        )
        self.manager.book_appointment(
            name="B", phone="+2", email="b@x.com",
            service_type="s", start=_dt(11), end=_dt(12),
        )
        self.assertEqual(len(self.manager.list_appointments()), 2)

    def test_outside_business_hours_raises(self):
        with self.assertRaises(ValueError):
            self.manager.book_appointment(
                name="A", phone="+1", email="a@x.com",
                service_type="s", start=_dt(9), end=_dt(10),
            )

    def test_end_after_business_hours_raises(self):
        with self.assertRaises(ValueError):
            self.manager.book_appointment(
                name="A", phone="+1", email="a@x.com",
                service_type="s", start=_dt(17), end=_dt(19),
            )

    def test_end_before_start_raises(self):
        with self.assertRaises(ValueError):
            self.manager.book_appointment(
                name="A", phone="+1", email="a@x.com",
                service_type="s", start=_dt(11), end=_dt(10),
            )


class TestCancelAppointment(unittest.TestCase):
    def setUp(self):
        self.manager = AppointmentManager()
        self.appt = self.manager.book_appointment(
            name="Alice", phone="+1", email="a@x.com",
            service_type="s", start=_dt(10), end=_dt(11),
        )

    def test_cancel_existing(self):
        result = self.manager.cancel_appointment(self.appt.id)
        self.assertTrue(result)
        self.assertEqual(len(self.manager.list_appointments()), 0)

    def test_cancel_nonexistent(self):
        result = self.manager.cancel_appointment("does-not-exist")
        self.assertFalse(result)

    def test_cancel_leaves_others(self):
        other = self.manager.book_appointment(
            name="Bob", phone="+2", email="b@x.com",
            service_type="s", start=_dt(11), end=_dt(12),
        )
        self.manager.cancel_appointment(self.appt.id)
        remaining = self.manager.list_appointments()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].id, other.id)


class TestLookupAppointment(unittest.TestCase):
    def setUp(self):
        self.manager = AppointmentManager()
        self.a1 = self.manager.book_appointment(
            name="Alice", phone="+10000000001", email="alice@example.com",
            service_type="s", start=_dt(10), end=_dt(11),
        )
        self.a2 = self.manager.book_appointment(
            name="Bob", phone="+10000000002", email="bob@example.com",
            service_type="s", start=_dt(11), end=_dt(12),
        )

    def test_lookup_by_phone(self):
        results = self.manager.lookup_appointment(phone="+10000000001")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.a1.id)

    def test_lookup_by_email(self):
        results = self.manager.lookup_appointment(email="bob@example.com")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.a2.id)

    def test_lookup_case_insensitive_email(self):
        results = self.manager.lookup_appointment(email="ALICE@EXAMPLE.COM")
        self.assertEqual(len(results), 1)

    def test_lookup_no_criteria_raises(self):
        with self.assertRaises(ValueError):
            self.manager.lookup_appointment()

    def test_lookup_not_found_returns_empty(self):
        results = self.manager.lookup_appointment(phone="+19999999999")
        self.assertEqual(results, [])


class TestRescheduleAppointment(unittest.TestCase):
    def setUp(self):
        self.manager = AppointmentManager()
        self.appt = self.manager.book_appointment(
            name="Alice", phone="+1", email="a@x.com",
            service_type="s", start=_dt(10), end=_dt(11),
        )

    def test_reschedule_changes_times(self):
        updated = self.manager.reschedule_appointment(
            self.appt.id, new_start=_dt(14), new_end=_dt(15),
        )
        self.assertEqual(updated.start, _dt(14))
        self.assertEqual(updated.end, _dt(15))

    def test_reschedule_nonexistent_raises(self):
        with self.assertRaises(ValueError):
            self.manager.reschedule_appointment(
                "no-such-id", new_start=_dt(14), new_end=_dt(15),
            )

    def test_reschedule_conflict_raises(self):
        self.manager.book_appointment(
            name="Bob", phone="+2", email="b@x.com",
            service_type="s", start=_dt(12), end=_dt(13),
        )
        with self.assertRaises(ValueError):
            self.manager.reschedule_appointment(
                self.appt.id, new_start=_dt(12), new_end=_dt(13),
            )

    def test_reschedule_outside_hours_raises(self):
        with self.assertRaises(ValueError):
            self.manager.reschedule_appointment(
                self.appt.id, new_start=_dt(8), new_end=_dt(9),
            )


class TestListAppointments(unittest.TestCase):
    def test_list_sorted_by_start(self):
        manager = AppointmentManager()
        manager.book_appointment(
            name="B", phone="+2", email="b@x.com",
            service_type="s", start=_dt(12), end=_dt(13),
        )
        manager.book_appointment(
            name="A", phone="+1", email="a@x.com",
            service_type="s", start=_dt(10), end=_dt(11),
        )
        appointments = manager.list_appointments()
        self.assertEqual(appointments[0].start, _dt(10))
        self.assertEqual(appointments[1].start, _dt(12))

    def test_list_empty(self):
        manager = AppointmentManager()
        self.assertEqual(manager.list_appointments(), [])


if __name__ == "__main__":
    unittest.main()
