from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User, PolicyRule


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    mask_fields: tuple[str, ...]
    policy_id: int | None
    reason: str


def evaluate_policy(
    db: Session,
    user: User,
    resource: str
) -> PolicyDecision:

    statement = (
        select(PolicyRule)
        .where(
            PolicyRule.resource == resource,
            PolicyRule.enabled.is_(True)
        )
        .order_by(
            PolicyRule.priority.desc(),
            PolicyRule.id.asc()
        )
    )

    rules = db.scalars(statement).all()

    for rule in rules:

        if user.role not in rule.allowed_roles:
            continue

        if rule.effect == "deny":
            return PolicyDecision(
                allowed=False,
                mask_fields=(),
                policy_id=rule.id,
                reason="策略拒绝访问"
            )

        if rule.effect == "allow":
            return PolicyDecision(
                allowed=True,
                mask_fields=tuple(rule.mask_fields),
                policy_id=rule.id,
                reason="策略允许访问"
            )

    return PolicyDecision(
        allowed=False,
        mask_fields=(),
        policy_id=None,
        reason="未匹配允许访问的策略"
    )