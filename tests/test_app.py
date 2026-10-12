import unittest
from unittest import mock

import requests

from app import RateProvider, create_app


class FakeProvider:
    def __init__(self, rates=None, fail=False):
        self.rates = rates or {"USD": 1.1, "GBP": 0.85}
        self.fail = fail
        self.calls = 0

    def get_rates(self, base):
        self.calls += 1
        if self.fail:
            raise requests.ConnectionError("offline")
        return self.rates


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.provider = FakeProvider()
        self.client = create_app(self.provider).test_client()

    def post(self, **body):
        return self.client.post("/convert", json=body)

    def test_converts_amount(self):
        res = self.post(base="eur", target="USD", amount="100")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["converted_amount"], 110.0)

    def test_same_currency_does_not_call_api(self):
        res = self.post(base="EUR", target="EUR", amount=5)
        self.assertEqual(res.get_json()["converted_amount"], 5.0)
        self.assertEqual(self.provider.calls, 0)

    def test_rejects_bad_amounts(self):
        for amount in ["abc", None, -3, 0]:
            with self.subTest(amount=amount):
                self.assertEqual(self.post(base="EUR", target="USD", amount=amount).status_code, 400)

    def test_rejects_unknown_currency(self):
        self.assertEqual(self.post(base="EUR", target="XYZ", amount=1).status_code, 400)

    def test_rejects_non_json_body(self):
        res = self.client.post("/convert", data="hello", content_type="text/plain")
        self.assertEqual(res.status_code, 400)

    def test_api_failure_returns_503(self):
        client = create_app(FakeProvider(fail=True)).test_client()
        res = client.post("/convert", json={"base": "EUR", "target": "USD", "amount": 1})
        self.assertEqual(res.status_code, 503)

    def test_index_and_currency_list(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertIn("EUR", self.client.get("/api/currencies").get_json())


class RateProviderTests(unittest.TestCase):
    def test_caches_rates_until_ttl_expires(self):
        now = [0]
        provider = RateProvider(ttl=60, clock=lambda: now[0])
        fake_response = mock.Mock()
        fake_response.json.return_value = {"rates": {"USD": 1.1}}

        with mock.patch("app.requests.get", return_value=fake_response) as get:
            provider.get_rates("EUR")
            provider.get_rates("EUR")
            self.assertEqual(get.call_count, 1)
            now[0] = 61
            provider.get_rates("EUR")
            self.assertEqual(get.call_count, 2)


if __name__ == "__main__":
    unittest.main()
