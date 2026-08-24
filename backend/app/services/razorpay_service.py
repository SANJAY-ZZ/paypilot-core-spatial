from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import uuid
import time
import httpx
import logging
from backend.app.core.config import settings
from backend.app.core.errors import PayPilotBaseException

logger = logging.getLogger(__name__)


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
    ) -> Dict[str, Any]:
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
    ) -> Dict[str, Any]:
        seq_num = self._next_seq()
        link_id = f"plink_mock_{uuid.uuid4().hex[:8]}"
        ref = reference_id or f"paypilot_mock_REC_{seq_num}"

        return {
            "id": link_id,
            "status": "created",
            "amount": int(round(amount * 100)),  # In smallest currency sub-unit (paise)
            "amount_paid": 0,
            "currency": currency,
            "description": description,
            "reference_id": ref,
            "short_url": f"https://rzp.io/i/{link_id}",
            "customer": {
                "name": customer_name,
                "email": customer_email,
            },
            "expire_by": int(time.time()) + (expire_by_minutes * 60),
            "created_at": int(time.time()),
            "provider": "mock_razorpay",
            "mock": True,
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
            "amount": int(round(amount * 100)),
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
    Interacts with official Razorpay Test Mode REST API using test credentials.
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
            timeout=10.0,
        )

    def create_payment_link(
        self,
        amount: float,
        currency: str,
        customer_name: str,
        customer_email: str,
        description: str,
        reference_id: Optional[str] = None,
        expire_by_minutes: int = 1440,
    ) -> Dict[str, Any]:
        # Convert INR Rupees to Paise
        amount_in_subunits = int(round(amount * 100))
        ref = reference_id or f"paypilot_test_{uuid.uuid4().hex[:8]}"
        expire_by = int(time.time()) + (expire_by_minutes * 60)

        payload = {
            "amount": amount_in_subunits,
            "currency": currency,
            "accept_partial": False,
            "description": description,
            "customer": {
                "name": customer_name,
                "email": customer_email,
            },
            "notify": {
                "sms": False,
                "email": True,
            },
            "reminder_enable": True,
            "notes": {
                "platform": "PayPilot AI Revenue OS",
                "reference_id": ref,
            },
            "reference_id": ref,
            "expire_by": expire_by,
        }

        try:
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
            return {
                "id": data.get("id"),
                "status": data.get("status", "created"),
                "amount": data.get("amount", amount_in_subunits),
                "amount_paid": data.get("amount_paid", 0),
                "currency": data.get("currency", currency),
                "description": data.get("description", description),
                "reference_id": data.get("reference_id", ref),
                "short_url": data.get("short_url"),
                "customer": data.get("customer", {"name": customer_name, "email": customer_email}),
                "expire_by": data.get("expire_by", expire_by),
                "created_at": data.get("created_at", int(time.time())),
                "provider": "razorpay_test",
                "mock": False,
            }

        except httpx.RequestError as e:
            logger.error(f"Razorpay Test API network error: {e}")
            raise PayPilotBaseException(f"Network error connecting to Razorpay Test API: {str(e)}", status_code=502)

    def create_refund(
        self,
        payment_id: str,
        amount: float,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        amount_in_subunits = int(round(amount * 100))
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
        return RazorpayTestService()
    return MockRazorpayService()


# Shared mock instance
mock_razorpay_service = MockRazorpayService()
