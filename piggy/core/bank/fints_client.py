"""
Thin FinTS client wrapper with lazy import and minimal surface area.

Note: The real FinTS/HBCI flow often requires SCA/TAN. This wrapper models a simple
login/fetch flow and exposes challenge status. It avoids storing PINs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional, Iterable

logger = logging.getLogger(__name__)


class FinTSNotAvailable(RuntimeError):
    pass


@dataclass
class FinTSTransaction:
    booking_date: date
    amount: str  # decimal as string in minor units or standard string
    description: str
    partner_name: Optional[str]
    partner_iban: Optional[str]


class FinTSClient:
    def __init__(
        self,
        bank_code: str,
        login: str,
        customer_id: Optional[str] = None,
        server: Optional[str] = None,
        product_id: Optional[str] = None,
    ):
        try:
            # Lazy import to keep dependency optional
            from fints.client import FinTS3PinTanClient  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise FinTSNotAvailable(
                "python-fints is not installed. Please install 'fints' package."
            ) from exc
        self._bank_code = bank_code
        self._login = login
        self._customer_id = customer_id
        self._server = server
        self._product_id = (
            product_id or "6151256F3D4F9975B877BD4A2"
        )  # Working DKB product ID from community
        self._client_cls = FinTS3PinTanClient
        self._client = None
        self._tan_required = False
        self._tan_message = None

    @property
    def tan_required(self) -> bool:
        return bool(self._tan_required)

    @property
    def tan_message(self) -> Optional[str]:
        return self._tan_message

    def open(self, pin: str):
        # Delayed import to keep module importable without dependency
        from fints.client import FinTS3PinTanClient  # type: ignore

        # DKB specific fix: If server is missing, use the most reliable one
        server = self._server
        if not server and self._bank_code == "12030000":
            server = "https://fints.dkb.de/fints"
            logger.info("Using default DKB FinTS server: %s", server)

        if not server:
            logger.error(
                "FinTS server URL is missing for bank_code %s", self._bank_code
            )
            # We don't raise here yet, as fints might have its own discovery,
            # but we logged it to explain the 'None' error.

        try:
            cust_id = self._customer_id
            # DKB expects empty customer_id; python-fints would otherwise default it to user_id
            if self._bank_code == "12030000" and not cust_id:
                cust_id = ""

            self._client = FinTS3PinTanClient(
                self._bank_code,
                self._login,
                pin,
                customer_id=cust_id,
                server=server,
                product_id=self._product_id,
            )

            # DKB specific: Pre-fetch mechanisms and set to 940 (App) if available
            if self._bank_code == "12030000":
                try:
                    self._client.fetch_tan_mechanisms()
                    self._client.set_tan_mechanism("940")
                except Exception as e:
                    logger.warning("Failed to pre-fetch DKB TAN mechanisms: %s", e)

            # Try to establish connection (context manager starts dialog)
            # Note: This might block for polling if we implement it here,
            # but for now we follow the 'NeedTANResponse' detection logic.
            with self._client:
                # Handle initial SCA response
                init_resp = getattr(self._client, "init_tan_response", None)
                if init_resp and "NeedTANResponse" in str(type(init_resp)):
                    # Decoupled flow polling (DKB App)
                    if getattr(init_resp, "decoupled", False):
                        logger.info(
                            "DKB Decoupled SCA started, polling for approval..."
                        )
                        from fints.client import NeedTANResponse  # type: ignore
                        import time

                        while isinstance(
                            self._client.init_tan_response, NeedTANResponse
                        ):
                            # We poll for up to 2 minutes (typical DKB timeout)
                            time.sleep(2)
                            self._client.init_tan_response = self._client.send_tan(
                                self._client.init_tan_response, None
                            )
                        logger.info("DKB Decoupled SCA resolved.")
                        # Wait a bit for the bank to settle as per working snippet
                        time.sleep(3)
                    else:
                        self._tan_required = True
                        self._tan_message = getattr(
                            init_resp, "challenge", "SCA required"
                        )
                        logger.info("FinTS SCA required: %s", self._tan_message)
        except Exception as e:
            # Handle the case where a TAN is required (often raised as an exception in some fints versions)
            if "NeedTANResponse" in str(type(e)):
                self._tan_required = True
                self._tan_message = getattr(e, "challenge", "SCA required")
                logger.info(
                    "FinTS SCA required (from exception): %s", self._tan_message
                )
                return

            logger.error("FinTS client initialization failed: %s", e)
            raise

    def close(self):  # pragma: no cover - thin wrapper
        if self._client is not None:
            try:
                self._client.deconstruct()
            finally:
                self._client = None

    def list_accounts(self) -> Iterable[dict]:  # pragma: no cover - passthrough
        assert self._client is not None, "Client not opened"
        accounts = self._client.get_sepa_accounts()
        return [
            {
                "iban": a.iban,
                "bic": a.bic,
                "account_number": a.accountnumber,
                "bank_code": a.blz,
                "name": getattr(a, "name", None),
            }
            for a in accounts
        ]

    def fetch_transactions(
        self, iban: str, start: date, end: date
    ) -> list[FinTSTransaction]:
        assert self._client is not None, "Client not opened"

        # FinTS get_transactions requires a SEPAAccount object, not just an IBAN string.
        accounts = self._client.get_sepa_accounts()
        target_account = next((a for a in accounts if a.iban == iban), None)

        if not target_account:
            logger.error("Account with IBAN %s not found in FinTS session", iban)
            return []

        stmt = self._client.get_transactions(
            target_account, start_date=start, end_date=end
        )
        result: list[FinTSTransaction] = []
        for tx in stmt:
            # python-fints returns either mt940.models.Transaction (attributes)
            # or fints.models.Transaction (namedtuple with dict in .data)
            data = getattr(tx, "data", None)

            # Booking date
            booking_date = None
            if data and isinstance(data, dict):
                booking_date = data.get("date")
            if not booking_date:
                booking_date = getattr(tx, "date", None)

            # Amount normalization to string
            amount_str = None
            if data and isinstance(data, dict):
                amt = data.get("amount")
                if amt is not None:
                    amount_str = str(getattr(amt, "amount", amt))
            if amount_str is None:
                amt = getattr(tx, "amount", None)
                if amt is not None:
                    amount_str = str(getattr(amt, "amount", amt))
            if amount_str is None:
                amount_str = "0"

            # Partner info and description (robust fallbacks)
            def _first_nonempty(*vals):
                for v in vals:
                    if v is None:
                        continue
                    if isinstance(v, (list, tuple)):
                        v = " ".join([str(x) for x in v if x])
                    v = str(v).strip()
                    if v:
                        return v
                return None

            if data and isinstance(data, dict):
                partner_name = _first_nonempty(
                    data.get("applicant_name"),
                    data.get("creditor_name"),
                    data.get("debtor_name"),
                )
                partner_iban = _first_nonempty(
                    data.get("applicant_iban"),
                    data.get("creditor_iban"),
                    data.get("debtor_iban"),
                )
                purpose = _first_nonempty(
                    data.get("purpose"),
                    data.get("remittance_information"),
                    data.get("text"),
                    data.get("transaction_details"),
                    data.get("description"),
                    data.get("info"),
                )
            else:
                partner_name = _first_nonempty(
                    getattr(tx, "applicant_name", None),
                )
                partner_iban = _first_nonempty(
                    getattr(tx, "applicant_iban", None),
                )
                purpose = _first_nonempty(
                    getattr(tx, "purpose", None),
                    getattr(tx, "text", None),
                )

            description = _first_nonempty(purpose, partner_name) or ""

            result.append(
                FinTSTransaction(
                    booking_date=booking_date or start,  # fallback to start if missing
                    amount=amount_str,
                    description=description,
                    partner_name=partner_name,
                    partner_iban=partner_iban,
                )
            )
        return result
