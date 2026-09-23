"""
Stage 7: Finance/Payment Integration Gateway (governance stub).

The platform must never claim that CSR/funding money has actually moved unless a
configured, real payment/finance backend confirms it. No such backend is configured
in this deployment, so every settlement request deterministically reports
NOT_CONFIGURED and the caller must keep the ledger row in a "pending external
confirmation" state rather than mark it paid.

Wiring a real provider later means implementing `confirm_settlement` against that
provider's API and setting `settings.FINANCE_INTEGRATION_PROVIDER`; nothing else in
the funding workflow needs to change.
"""
from typing import Optional
from dataclasses import dataclass
from backend.app.core.config import settings


@dataclass
class SettlementResult:
    confirmed: bool
    status: str
    provider_reference: Optional[str] = None
    reason: Optional[str] = None


class FinanceIntegrationService:
    @property
    def configured_provider(self) -> Optional[str]:
        return getattr(settings, "FINANCE_INTEGRATION_PROVIDER", None) or None

    def is_configured(self) -> bool:
        return bool(self.configured_provider)

    def confirm_settlement(self, funding_record_id: int, amount: float, currency: str, reference: Optional[str] = None) -> SettlementResult:
        """
        Attempts to confirm a fund disbursement against the configured finance/payment
        integration. Deterministically returns NOT_CONFIGURED when none is set up —
        it never fabricates a successful transfer.
        """
        provider = self.configured_provider
        if not provider:
            return SettlementResult(
                confirmed=False,
                status="NOT_CONFIGURED",
                reason="No payment/finance integration is configured for this deployment. "
                       "Funds cannot be marked as transferred until a real provider confirms settlement."
            )
        # Real provider integrations would be dispatched here based on `provider`.
        return SettlementResult(confirmed=False, status="PROVIDER_UNREACHABLE", reason=f"Provider '{provider}' integration not implemented.")


finance_integration_service = FinanceIntegrationService()
