"""Configuration and refresh failures must not log credentials or identifiers."""

import logging
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from py_nationalgrid.exceptions import (
    CannotConnectError,
    InvalidAuthError,
    NationalGridError,
)

from custom_components.national_grid_us.const import DOMAIN

from .conftest import MOCK_ACCOUNT_ID, MOCK_PASSWORD, MOCK_SERVICE_POINT, MOCK_USERNAME
from .test_coordinator import _make_api, _make_coordinator


@pytest.mark.parametrize(
    "error_type", [CannotConnectError, InvalidAuthError, NationalGridError]
)
async def test_login_errors_do_not_log_secrets(hass, caplog, error_type):
    """Even a backend error containing credentials must be safe to log."""
    caplog.set_level(logging.DEBUG)
    secret = f"{MOCK_USERNAME} {MOCK_PASSWORD} {MOCK_ACCOUNT_ID}"
    with patch(
        "custom_components.national_grid_us.config_flow.NationalGridClient"
    ) as cls:
        client = cls.return_value
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        client.get_linked_accounts = AsyncMock(side_effect=error_type(secret))
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"username": MOCK_USERNAME, "password": MOCK_PASSWORD},
        )
    assert result["type"] == "form"
    for value in (MOCK_USERNAME, MOCK_PASSWORD, MOCK_ACCOUNT_ID):
        assert value not in caplog.text
    records = [
        r
        for r in caplog.records
        if r.name.startswith("custom_components.national_grid_us")
    ]
    assert records
    assert all(r.exc_info is None for r in records)


async def test_refresh_logs_are_anonymous(hass, caplog):
    """Successful data fetches and per-account errors omit account and meter IDs."""
    caplog.set_level(logging.DEBUG)
    api = _make_api()
    coordinator = _make_coordinator(hass, api)
    await coordinator._async_update_data()
    api.get_billing_account.side_effect = NationalGridError(MOCK_PASSWORD)
    await coordinator._async_update_data()
    messages = "\n".join(
        record.getMessage()
        for record in caplog.records
        if record.name.startswith("custom_components.national_grid_us")
    )
    for value in (MOCK_ACCOUNT_ID, MOCK_SERVICE_POINT, MOCK_PASSWORD):
        assert value not in messages
