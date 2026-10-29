"""Regression tests for the catalog sync contract used by the iOS client.

The client decodes this response into ServerUpdateMessage/NewFoodRequest and
acts on `reset` by deleting its cached global foods, so the shape of this
payload and the conditions under which `reset` is True are load-bearing.
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Food

URL = "/foods/api/foods/"


class CatalogContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for i in range(3):
            Food.objects.create(name=f"Food {i}", cal=100 + i, fat=1, car=2,
                                pro=3, approved=True)
        Food.objects.create(name="Pending", cal=1, fat=1, car=1, pro=1,
                            approved=False)

    def get(self, **params):
        res = self.client.get(URL, params)
        self.assertEqual(res.status_code, 200)
        return res.json()

    def test_response_shape_matches_client_struct(self):
        body = self.get()
        self.assertEqual(set(body), {"foods", "timestamp", "reset"})
        self.assertIsInstance(body["timestamp"], str)
        self.assertIsInstance(body["reset"], bool)
        for food in body["foods"]:
            self.assertLessEqual({"id", "name", "cal", "car", "fat", "pro"},
                                 set(food))

    def test_unapproved_foods_are_not_served(self):
        names = [f["name"] for f in self.get()["foods"]]
        self.assertNotIn("Pending", names)
        self.assertEqual(len(names), 3)

    def test_caught_up_client_gets_nothing_and_no_reset(self):
        body = self.get(time=self.get()["timestamp"])
        self.assertEqual(body["foods"], [])
        self.assertFalse(body["reset"])

    def test_stale_client_gets_full_catalog_and_reset(self):
        body = self.get(time="2000-01-01T00:00:00Z")
        self.assertEqual(len(body["foods"]), 3)
        self.assertTrue(body["reset"])

    def test_incremental_update_does_not_reset(self):
        before = timezone.now().isoformat().replace("+00:00", "Z")
        Food.objects.create(name="Fresh", cal=9, fat=1, car=1, pro=1,
                            approved=True)
        body = self.get(time=before)
        self.assertEqual([f["name"] for f in body["foods"]], ["Fresh"])
        self.assertFalse(body["reset"])

    def test_empty_catalog_never_orders_a_wipe(self):
        """0 == 0 used to satisfy the reset condition, telling every client to
        delete its catalog with nothing to repopulate from."""
        Food.objects.all().update(approved=False)
        body = self.get(time="2026-01-01T00:00:00Z")
        self.assertEqual(body["foods"], [])
        self.assertFalse(body["reset"])

    def test_malformed_timestamp_serves_full_catalog_instead_of_500(self):
        """A corrupt stored timestamp used to reach the ORM as None and raise."""
        body = self.get(time="not-a-timestamp")
        self.assertEqual(len(body["foods"]), 3)

    def test_timestamp_precedes_queryset(self):
        """Guards the ordering in list(): a food saved mid-request must be
        re-sent next time rather than skipped permanently."""
        src = open("foods/views.py").read()
        self.assertLess(src.index("now = timezone.now()"),
                        src.index("approved = Food.objects.filter(approved=True)"))


class WriteSurfaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.food = Food.objects.create(name="Target", cal=1, fat=1, car=1,
                                       pro=1, approved=True)

    def test_submission_is_accepted_but_unapproved(self):
        res = self.client.post(URL, {"name": "Submitted", "cal": 5, "fat": 1,
                                     "car": 1, "pro": 1},
                               content_type="application/json")
        self.assertEqual(res.status_code, 201)
        self.assertFalse(Food.objects.get(name="Submitted").approved)

    def test_client_supplied_id_is_ignored(self):
        res = self.client.post(URL, {"id": 10000, "name": "Ignored", "cal": 1,
                                     "fat": 1, "car": 1, "pro": 1},
                               content_type="application/json")
        self.assertNotEqual(res.json()["id"], 10000)

    def test_blank_name_rejected(self):
        res = self.client.post(URL, {"name": "   ", "cal": 1, "fat": 1,
                                     "car": 1, "pro": 1},
                               content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_negative_macros_rejected(self):
        res = self.client.post(URL, {"name": "Negative", "cal": -5, "fat": 1,
                                     "car": 1, "pro": 1},
                               content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_detail_routes_do_not_exist(self):
        """These were unauthenticated on a ModelViewSet and 500'd only because
        `queryset` was undefined. They must not be reachable at all."""
        detail = f"{URL}{self.food.pk}/"
        for method in ("get", "put", "patch", "delete"):
            res = getattr(self.client, method)(detail)
            self.assertIn(res.status_code, (404, 405), f"{method} -> {res.status_code}")
        self.food.refresh_from_db()
        self.assertEqual(self.food.name, "Target")


class SeedCommandTests(TestCase):
    def test_create_foods_is_idempotent(self):
        from django.core.management import call_command
        from io import StringIO
        call_command("create_foods", stdout=StringIO())
        first = Food.objects.count()
        call_command("create_foods", stdout=StringIO())
        self.assertEqual(Food.objects.count(), first)

    def test_seeded_serving_is_stripped(self):
        from django.core.management import call_command
        from io import StringIO
        call_command("create_foods", stdout=StringIO())
        self.assertFalse(any(f.serving != f.serving.strip()
                             for f in Food.objects.all()))
