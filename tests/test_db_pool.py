"""Tests for US-007 — SQLAlchemy connection pool configuration and behaviour.

Test coverage:
  1. Pool configuration variables are present in the testing config.
  2. SQLALCHEMY_ENGINE_OPTIONS is populated in the Flask app config.
  3. pool_pre_ping is always enabled (applies to all pool backends).
  4. pool_recycle and pool_timeout are correctly defaulted.
  5. SQLALCHEMY_POOL_SIZE / MAX_OVERFLOW are overridden per environment.
  6. The /ready endpoint response includes a ``database.pool`` key.
  7. The pool dict always contains the ``available`` boolean key.
  8. Graceful handling: when the database raises on SELECT 1, the readiness
     probe returns status="not_ready" rather than crashing.
  9. Application recovers after a simulated transient DB failure (pre_ping
     semantics: next request succeeds when mock is cleared).
 10. Multiple sequential requests all succeed (pool is not exhausted).
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import OperationalError

from core import create_app, db

from . import BaseTestClass


class PoolConfigTestCase(BaseTestClass):
    """Verify that pool configuration variables are correctly set."""

    def test_pool_pre_ping_enabled_in_engine_options(self):
        """pool_pre_ping must be True in SQLALCHEMY_ENGINE_OPTIONS."""
        with self.app.app_context():
            opts = self.app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {})
            self.assertIn(
                "pool_pre_ping",
                opts,
                "SQLALCHEMY_ENGINE_OPTIONS should contain pool_pre_ping",
            )
            self.assertTrue(
                opts["pool_pre_ping"],
                "pool_pre_ping must be True so stale connections are detected",
            )

    def test_engine_options_dict_is_present(self):
        """SQLALCHEMY_ENGINE_OPTIONS must be set in app.config."""
        with self.app.app_context():
            self.assertIn(
                "SQLALCHEMY_ENGINE_OPTIONS",
                self.app.config,
                "SQLALCHEMY_ENGINE_OPTIONS must be configured before db.init_app",
            )

    def test_pool_size_overridden_for_testing_environment(self):
        """Testing config should override pool_size to 2."""
        with self.app.app_context():
            self.assertEqual(
                self.app.config.get("SQLALCHEMY_POOL_SIZE"),
                2,
                "Testing environment must use SQLALCHEMY_POOL_SIZE=2",
            )

    def test_max_overflow_overridden_for_testing_environment(self):
        """Testing config should override max_overflow to 3."""
        with self.app.app_context():
            self.assertEqual(
                self.app.config.get("SQLALCHEMY_MAX_OVERFLOW"),
                3,
                "Testing environment must use SQLALCHEMY_MAX_OVERFLOW=3",
            )

    def test_pool_recycle_is_set(self):
        """SQLALCHEMY_POOL_RECYCLE must be configured (default 1800 s)."""
        with self.app.app_context():
            recycle = self.app.config.get("SQLALCHEMY_POOL_RECYCLE")
            self.assertIsNotNone(recycle)
            self.assertGreater(recycle, 0)

    def test_pool_timeout_is_set(self):
        """SQLALCHEMY_POOL_TIMEOUT must be configured (default 30 s)."""
        with self.app.app_context():
            timeout = self.app.config.get("SQLALCHEMY_POOL_TIMEOUT")
            self.assertIsNotNone(timeout)
            self.assertGreater(timeout, 0)


class PoolMetricsEndpointTestCase(BaseTestClass):
    """Verify that /ready exposes pool metrics in its JSON response."""

    def test_ready_response_contains_database_key(self):
        """GET /ready must include a 'database' key in 'checks'."""
        res = self.client.get("/ready")
        data = json.loads(res.data)
        self.assertIn("checks", data)
        self.assertIn("database", data["checks"])

    def test_ready_response_database_has_pool_key(self):
        """The 'database' check dict must include a 'pool' key."""
        res = self.client.get("/ready")
        data = json.loads(res.data)
        db_check = data["checks"]["database"]
        self.assertIn(
            "pool",
            db_check,
            "database check should expose a 'pool' sub-dict",
        )

    def test_pool_metrics_contain_available_flag(self):
        """pool dict must always contain the 'available' boolean."""
        res = self.client.get("/ready")
        data = json.loads(res.data)
        pool = data["checks"]["database"]["pool"]
        self.assertIn("available", pool)
        self.assertIsInstance(pool["available"], bool)

    def test_pool_metrics_structure_when_available(self):
        """When pool metrics are available, all expected keys must be present."""
        res = self.client.get("/ready")
        data = json.loads(res.data)
        pool = data["checks"]["database"]["pool"]
        if pool["available"]:
            for key in (
                "pool_size",
                "checked_out",
                "checked_in",
                "overflow",
                "max_overflow",
                "utilization_pct",
                "saturated",
            ):
                self.assertIn(
                    key,
                    pool,
                    f"pool dict must contain '{key}' when available=true",
                )

    def test_pool_saturated_is_boolean(self):
        """'saturated' flag must be a boolean when pool metrics are available."""
        res = self.client.get("/ready")
        data = json.loads(res.data)
        pool = data["checks"]["database"]["pool"]
        if pool["available"]:
            self.assertIsInstance(pool["saturated"], bool)

    def test_pool_utilization_pct_is_numeric(self):
        """utilization_pct must be a numeric value when available."""
        res = self.client.get("/ready")
        data = json.loads(res.data)
        pool = data["checks"]["database"]["pool"]
        if pool["available"]:
            self.assertIsInstance(pool["utilization_pct"], (int, float))
            self.assertGreaterEqual(pool["utilization_pct"], 0.0)
            self.assertLessEqual(pool["utilization_pct"], 100.0)


class PoolReconnectionTestCase(BaseTestClass):
    """Verify graceful handling of transient database failures (pre_ping behaviour)."""

    def test_ready_returns_not_ready_when_db_select_fails(self):
        """When SELECT 1 raises OperationalError, /ready must return 503 not_ready."""
        mock_error = OperationalError(
            "SELECT 1", params={}, orig=Exception("connection dropped")
        )
        with patch.object(db.session, "execute", side_effect=mock_error):
            res = self.client.get("/ready")
            data = json.loads(res.data)

        self.assertEqual(res.status_code, 503)
        self.assertEqual(data["status"], "not_ready")
        self.assertEqual(data["checks"]["database"]["status"], "error")

    def test_ready_recovers_after_transient_db_failure(self):
        """After a transient failure, the next request to /ready must succeed."""
        mock_error = OperationalError(
            "SELECT 1", params={}, orig=Exception("transient drop")
        )
        # First call: simulate failure
        with patch.object(db.session, "execute", side_effect=mock_error):
            res_fail = self.client.get("/ready")
        self.assertEqual(res_fail.status_code, 503)

        # Second call: no patch — real SQLite connection should succeed
        res_ok = self.client.get("/ready")
        data_ok = json.loads(res_ok.data)
        self.assertIn(
            res_ok.status_code, (200, 503)
        )  # depends on ext services
        self.assertEqual(data_ok["checks"]["database"]["status"], "ok")

    def test_health_endpoint_always_returns_200(self):
        """GET /health (liveness) must return 200 regardless of DB state."""
        mock_error = OperationalError(
            "SELECT 1", params={}, orig=Exception("db down")
        )
        with patch.object(db.session, "execute", side_effect=mock_error):
            res = self.client.get("/health")

        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "ok")


class PoolConcurrencyTestCase(BaseTestClass):
    """Verify that multiple sequential requests do not exhaust the pool."""

    def test_multiple_sequential_requests_succeed(self):
        """/ready must respond successfully for 10 consecutive calls."""
        for i in range(10):
            res = self.client.get("/ready")
            data = json.loads(res.data)
            self.assertEqual(
                data["checks"]["database"]["status"],
                "ok",
                f"Request #{i + 1} to /ready: database check failed unexpectedly",
            )

    def test_multiple_health_requests_succeed(self):
        """10 sequential GET /health requests must all return 200."""
        for i in range(10):
            res = self.client.get("/health")
            self.assertEqual(
                res.status_code,
                200,
                f"Health request #{i + 1} returned unexpected status {res.status_code}",
            )

    def test_pool_not_exhausted_after_sequential_db_operations(self):
        """10 sequential /ready calls (each executing SELECT 1) must all succeed."""
        failures = []
        for i in range(10):
            res = self.client.get("/ready")
            data = json.loads(res.data)
            if data["checks"]["database"]["status"] != "ok":
                failures.append(i + 1)
        self.assertFalse(
            failures,
            f"Requests {failures} had database status != ok — pool may be exhausted",
        )


if __name__ == "__main__":
    unittest.main()
