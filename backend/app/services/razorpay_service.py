from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
import uuid
import time
import httpx
import logging
from backend.app.core.config import settings
from backend.app.core.errors import PayPilotBaseException

logger = logging.getLogger(__name__)


def to_subunit(amount: float | Decimal | int | str) -> int:
    """
    Convert currency amount (e.g. INR Rupees) to smallest subunit (Paise)
    using exact Decimal arithmetic and half-up rounding to eliminate floating point inaccuracies.
    Example: 100.00 -> 10000 paise, 1500.50 -> 150050 paise.
    """
    dec = Decimal(str(amount))
    return int((dec * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


class RazorpayService(ABC):
    """Abstract interface for Razorpay payment operations."""

    @abstractmethod
    def create_payment_link(
        self,
        amount: float,
        currency: str,
        customer_name: str,
        customer_email: str,
        description: str,
        reference_id: Optional[str] = None,
        expire_by_minutes: int = 1440,
        customer_contact: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def fetch_payment_link(self, link_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def cancel_payment_link(self, link_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_refund(
        self,
        payment_id: str,
        amount: float,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_customer(self, name: str, email: str, contact: Optional[str] = None) -> Dict[str, Any]:
        pass


class MockRazorpayService(RazorpayService):
    """Deterministic Mock Razorpay Adapter for Hackathon Demos & Offline Testing."""

    def __init__(self):
        self._seq = 480

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def create_payment_link(
        self,
        amount: float,
        currency: str,
        customer_name: str,
        customer_email: str,
        description: str,
        reference_id: Optional[str] = None,
        expire_by_minutes: int = 1440,
        customer_contact: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        seq_num = self._next_seq()
        link_id = f"plink_mock_{uuid.uuid4().hex[:8]}"
        ref = reference_id or f"paypilot_mock_REC_{seq_num}"

        amount_in_subunits = to_subunit(amount)

        return {
            "id": link_id,
            "status": "created",
            "amount": amount_in_subunits,
            "amount_paid": 0,
            "currency": currency,
            "description": description,
            "reference_id": ref,
            "short_url": f"https://rzp.io/i/{link_id}",
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "contact": customer_contact or "+919876543210",
            },
            "notes": notes or {},
            "expire_by": int(time.time()) + (expire_by_minutes * 60),
            "created_at": int(time.time()),
            "provider": "mock_razorpay",
            "mock": True,
        }

    def fetch_payment_link(self, link_id: str) -> Dict[str, Any]:
        return {
            "id": link_id,
            "status": "created",
            "amount": 150000,
            "amount_paid": 0,
            "currency": "INR",
            "description": f"Mock payment link {link_id}",
            "short_url": f"https://rzp.io/i/{link_id}",
            "provider": "mock_razorpay",
            "mock": True,
        }

    def cancel_payment_link(self, link_id: str) -> Dict[str, Any]:
        return {
            "id": link_id,
            "status": "cancelled",
            "cancelled_at": int(time.time()),
            "provider": "mock_razorpay",
            "mock": True,
        }

    def health_check(self) -> Dict[str, Any]:
        return {
            "provider": "razorpay",
            "mode": "mock",
            "status": "connected",
            "key_configured": bool(settings.RAZORPAY_KEY_ID),
        }

    def create_refund(
        self,
        payment_id: str,
        amount: float,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        refund_id = f"rfnd_mock_{uuid.uuid4().hex[:8]}"
        return {
            "id": refund_id,
            "payment_id": payment_id,
            "amount": to_subunit(amount),
            "currency": "INR",
            "status": "processed",
            "notes": notes or {},
            "created_at": int(time.time()),
            "provider": "mock_razorpay",
            "mock": True,
        }

    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        return {
            "id": payment_id,
            "entity": "payment",
            "amount": 150000,
            "currency": "INR",
            "status": "captured",
            "method": "upi",
            "description": "Mock payment status check",
            "created_at": int(time.time()) - 3600,
            "provider": "mock_razorpay",
            "mock": True,
        }

    def create_customer(self, name: str, email: str, contact: Optional[str] = None) -> Dict[str, Any]:
        cust_id = f"cust_rzp_mock_{uuid.uuid4().hex[:8]}"
        return {
            "id": cust_id,
            "entity": "customer",
            "name": name,
            "email": email,
            "contact": contact or "+919876543210",
            "created_at": int(time.time()),
            "provider": "mock_razorpay",
            "mock": True,
        }


class RazorpayTestService(RazorpayService):
    """
    Razorpay TEST MODE adapter.
    Interacts with official Razorpay Test Mode REST API using Basic Authentication.
    """

    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        http_client: Optional[httpx.Client] = None,
    ):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET

        if not self.key_id or not self.key_secret:
            raise PayPilotBaseException(
                "Razorpay Test Mode configuration error: RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be configured when RAZORPAY_MODE='test'.",
                status_code=500,
            )

        self._client = http_client

    def _get_client(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        return httpx.Client(
            auth=(self.key_id, self.key_secret),
            timeout=15.0,
        )

    def health_check(self) -> Dict[str, Any]:
        """Probe Razorpay Test Mode API connectivity and authenticate credentials."""
        if not self.key_id or not self.key_secret:
            return {
                "provider": "razorpay",
                "mode": "test",
                "status": "not_configured",
                "key_configured": False,
            }

        try:
            client = self._get_client()
            # Lightweight probe to verify credentials and endpoint reachability
            resp = client.get(f"{self.BASE_URL}/payment_links?count=1")
            if resp.status_code == 200:
                masked_key = f"{self.key_id[:8]}..." if len(self.key_id) > 8 else self.key_id
                return {
                    "provider": "razorpay",
                    "mode": "test",
                    "status": "connected",
                    "key_id": masked_key,
                    "key_configured": True,
                }
            elif resp.status_code in (401, 403):
                logger.warning(f"Razorpay Test authentication rejected (status {resp.status_code}).")
                return {
                    "provider": "razorpay",
                    "mode": "test",
                    "status": "invalid_credentials",
                    "key_configured": True,
                }
            else:
                logger.warning(f"Razorpay Test health probe returned status {resp.status_code}: {resp.text}")
                return {
                    "provider": "razorpay",
                    "mode": "test",
                    "status": "unavailable",
                    "key_configured": True,
                }
        except httpx.TimeoutException:
            logger.warning("Razorpay Test health probe timed out.")
            return {
                "provider": "razorpay",
                "mode": "test",
                "status": "unavailable",
                "key_configured": True,
            }
        except Exception as e:
            logger.warning(f"Razorpay Test health probe failed ({type(e).__name__}: {str(e)}).")
            return {
                "provider": "razorpay",
                "mode": "test",
                "status": "unavailable",
                "key_configured": True,
            }

    def create_payment_link(
        self,
        amount: float,
        currency: str,
        customer_name: str,
        customer_email: str,
        description: str,
        reference_id: Optional[str] = None,
        expire_by_minutes: int = 1440,
        customer_contact: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        amount_in_subunits = to_subunit(amount)
        ref = reference_id or f"paypilot_test_{uuid.uuid4().hex[:8]}"
        expire_by = int(time.time()) + (expire_by_minutes * 60)

        customer_payload: Dict[str, Any] = {
            "name": customer_name,
            "email": customer_email,
        }
        if customer_contact:
            customer_payload["contact"] = customer_contact

        notes_payload = {
            "platform": "PayPilot AI Revenue OS",
            "reference_id": ref,
        }
        if notes:
            notes_payload.update(notes)

        payload = {
            "amount": amount_in_subunits,
            "currency": currency,
            "accept_partial": False,
            "description": description,
            "customer": customer_payload,
            "notify": {
                "sms": bool(customer_contact),
                "email": bool(customer_email),
            },
            "reminder_enable": True,
            "notes": notes_payload,
            "reference_id": ref,
            "expire_by": expire_by,
        }

        try:
            logger.info(f"Dispatching Razorpay Payment Link -> Ref: '{ref}', Amount: ₹{amount:.2f} ({amount_in_subunits} paise)")
            client = self._get_client()
            response = client.post(
                f"{self.BASE_URL}/payment_links",
                json=payload,
            )

            if response.status_code not in (200, 201):
                logger.error(f"Razorpay Test API Error ({response.status_code}): {response.text}")
                raise PayPilotBaseException(
                    f"Razorpay Payment Link creation failed: {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()
            logger.info(f"Razorpay Payment Link created successfully: ID '{data.get('id')}', Short URL '{data.get('short_url')}'")
            return {
                "id": data.get("id"),
                "status": data.get("status", "created"),
                "amount": data.get("amount", amount_in_subunits),
                "amount_paid": data.get("amount_paid", 0),
                "currency": data.get("currency", currency),
                "description": data.get("description", description),
                "reference_id": data.get("reference_id", ref),
                "short_url": data.get("short_url"),
                "customer": data.get("customer", customer_payload),
                "expire_by": data.get("expire_by", expire_by),
                "created_at": data.get("created_at", int(time.time())),
                "provider": "razorpay_test",
                "mock": False,
            }

        except httpx.TimeoutException:
            logger.error("Razorpay Test API connection timed out.")
            raise PayPilotBaseException("Razorpay Test API timed out. Please try again.", status_code=504)
        except httpx.RequestError as e:
            logger.error(f"Razorpay Test API network error: {e}")
            raise PayPilotBaseException(f"Network error connecting to Razorpay Test API: {str(e)}", status_code=502)

    def fetch_payment_link(self, link_id: str) -> Dict[str, Any]:
        try:
            client = self._get_client()
            response = client.get(f"{self.BASE_URL}/payment_links/{link_id}")
            if response.status_code != 200:
                raise PayPilotBaseException(
                    f"Failed to fetch Razorpay payment link '{link_id}': {response.text}",
                    status_code=response.status_code,
                )
            data = response.json()
            return {
                "id": data.get("id"),
                "status": data.get("status"),
                "amount": data.get("amount"),
                "amount_paid": data.get("amount_paid", 0),
                "currency": data.get("currency"),
                "description": data.get("description"),
                "short_url": data.get("short_url"),
                "provider": "razorpay_test",
                "mock": False,
            }
        except httpx.RequestError as e:
            raise PayPilotBaseException(f"Network error fetching Razorpay payment link: {str(e)}", status_code=502)

    def cancel_payment_link(self, link_id: str) -> Dict[str, Any]:
        try:
            client = self._get_client()
            response = client.post(f"{self.BASE_URL}/payment_links/{link_id}/cancel")
            if response.status_code != 200:
                raise PayPilotBaseException(
                    f"Failed to cancel Razorpay payment link '{link_id}': {response.text}",
                    status_code=response.status_code,
                )
            data = response.json()
            return {
                "id": data.get("id"),
                "status": data.get("status", "cancelled"),
                "cancelled_at": int(time.time()),
                "provider": "razorpay_test",
                "mock": False,
            }
        except httpx.RequestError as e:
            raise PayPilotBaseException(f"Network error cancelling Razorpay payment link: {str(e)}", status_code=502)

    def create_refund(
        self,
        payment_id: str,
        amount: float,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        amount_in_subunits = to_subunit(amount)
        payload = {
            "amount": amount_in_subunits,
            "notes": notes or {},
        }
        try:
            client = self._get_client()
            response = client.post(
                f"{self.BASE_URL}/payments/{payment_id}/refund",
                json=payload,
            )
            if response.status_code not in (200, 201):
                raise PayPilotBaseException(f"Razorpay refund failed: {response.text}", status_code=response.status_code)
            data = response.json()
            return {
                "id": data.get("id"),
                "payment_id": payment_id,
                "amount": data.get("amount", amount_in_subunits),
                "currency": data.get("currency", "INR"),
                "status": data.get("status", "processed"),
                "notes": notes or {},
                "created_at": data.get("created_at", int(time.time())),
                "provider": "razorpay_test",
                "mock": False,
            }
        except httpx.RequestError as e:
            raise PayPilotBaseException(f"Network error during Razorpay refund: {str(e)}", status_code=502)

    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        try:
            client = self._get_client()
            response = client.get(f"{self.BASE_URL}/payments/{payment_id}")
            if response.status_code != 200:
                raise PayPilotBaseException(f"Failed to fetch Razorpay payment: {response.text}", status_code=response.status_code)
            data = response.json()
            return {
                "id": data.get("id"),
                "entity": "payment",
                "amount": data.get("amount"),
                "currency": data.get("currency"),
                "status": data.get("status"),
                "method": data.get("method"),
                "description": data.get("description"),
                "created_at": data.get("created_at"),
                "provider": "razorpay_test",
                "mock": False,
            }
        except httpx.RequestError as e:
            raise PayPilotBaseException(f"Network error checking Razorpay status: {str(e)}", status_code=502)

    def create_customer(self, name: str, email: str, contact: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "name": name,
            "email": email,
            "contact": contact or "+919876543210",
            "fail_existing": "0",
        }
        try:
            client = self._get_client()
            response = client.post(f"{self.BASE_URL}/customers", json=payload)
            if response.status_code not in (200, 201):
                raise PayPilotBaseException(f"Failed to create Razorpay customer: {response.text}", status_code=response.status_code)
            data = response.json()
            return {
                "id": data.get("id"),
                "entity": "customer",
                "name": data.get("name", name),
                "email": data.get("email", email),
                "contact": data.get("contact"),
                "created_at": data.get("created_at", int(time.time())),
                "provider": "razorpay_test",
                "mock": False,
            }
        except httpx.RequestError as e:
            raise PayPilotBaseException(f"Network error creating Razorpay customer: {str(e)}", status_code=502)


def get_razorpay_service() -> RazorpayService:
    """Factory returning configured Razorpay Service (Mock or Test Mode)."""
    if settings.RAZORPAY_MODE == "test":
        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            return RazorpayTestService()
        else:
            logger.warning("RAZORPAY_MODE is 'test' but credentials are not configured. Falling back to Mock service.")
            return MockRazorpayService()
    return MockRazorpayService()


# Global mock service instance
mock_razorpay_service = MockRazorpayService()
