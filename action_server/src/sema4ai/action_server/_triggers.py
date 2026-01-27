"""
Trigger engine for the Action Server.

Handles webhook triggers for event-driven action execution.
"""

import hashlib
import hmac
import json
import logging
import re
import secrets
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class TriggerEngine:
    """
    Engine for handling webhook and other triggers.

    Features:
    - HMAC signature validation
    - Rate limiting
    - Payload templating
    """

    def __init__(self):
        """Initialize the trigger engine."""
        # Rate limit tracker: trigger_id -> list of invocation timestamps
        self._rate_limit_tracker: Dict[str, List[datetime]] = defaultdict(list)

    async def handle_webhook(
        self,
        trigger_id: str,
        payload: Any,
        headers: Dict[str, str],
        source_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle an incoming webhook request.

        Args:
            trigger_id: The trigger ID from the URL
            payload: Request body (parsed JSON or raw)
            headers: Request headers
            source_ip: Source IP address

        Returns:
            Dict with status and any created run/work_item IDs
        """
        from sema4ai.action_server._database import datetime_to_str
        from sema4ai.action_server._gen_ids import gen_uuid
        from sema4ai.action_server._models import (
            Trigger,
            TriggerInvocation,
            TriggerInvocationStatus,
            get_db,
        )

        now = datetime.now(timezone.utc)
        invocation_id = gen_uuid("trigger_invocation")

        db = get_db()

        # Get the trigger
        with db.connect():
            try:
                trigger = db.first(
                    Trigger,
                    "SELECT * FROM trigger WHERE id = ?",
                    [trigger_id],
                )
            except KeyError:
                return {
                    "status": "error",
                    "message": f"Trigger not found: {trigger_id}",
                }

        # Check if trigger is enabled
        if not trigger.enabled:
            return {
                "status": "rejected",
                "message": "Trigger is disabled",
            }

        # Validate signature if configured
        if trigger.webhook_secret:
            if not self._validate_signature(trigger, payload, headers):
                await self._record_invocation(
                    invocation_id,
                    trigger_id,
                    now,
                    source_ip,
                    payload,
                    headers,
                    TriggerInvocationStatus.REJECTED,
                    error_message="Invalid signature",
                )
                return {
                    "status": "rejected",
                    "message": "Invalid signature",
                }

        # Check rate limit
        if not self._check_rate_limit(trigger, now):
            await self._record_invocation(
                invocation_id,
                trigger_id,
                now,
                source_ip,
                payload,
                headers,
                TriggerInvocationStatus.RATE_LIMITED,
                error_message="Rate limit exceeded",
            )
            return {
                "status": "rate_limited",
                "message": "Rate limit exceeded",
            }

        # Apply payload template to get inputs
        try:
            inputs = self._apply_template(
                trigger.inputs_template_json,
                payload,
                headers,
                trigger,
            )
        except Exception as e:
            await self._record_invocation(
                invocation_id,
                trigger_id,
                now,
                source_ip,
                payload,
                headers,
                TriggerInvocationStatus.ERROR,
                error_message=f"Template error: {e}",
            )
            return {
                "status": "error",
                "message": f"Failed to apply template: {e}",
            }

        # Execute the trigger
        try:
            run_id = None
            work_item_id = None

            if trigger.execution_mode == "run":
                run_id = await self._create_action_run(trigger, inputs)
            elif trigger.execution_mode == "work_item":
                work_item_id = await self._create_work_item(trigger, inputs)

            # Record successful invocation
            await self._record_invocation(
                invocation_id,
                trigger_id,
                now,
                source_ip,
                payload,
                headers,
                TriggerInvocationStatus.ACCEPTED,
                run_id=run_id,
                work_item_id=work_item_id,
            )

            # Update trigger stats
            with db.connect():
                with db.transaction():
                    db.update_by_id(
                        Trigger,
                        trigger_id,
                        {
                            "last_triggered_at": datetime_to_str(now),
                            "trigger_count": trigger.trigger_count + 1,
                            "updated_at": datetime_to_str(now),
                        },
                    )

            result = {
                "status": "accepted",
                "invocation_id": invocation_id,
            }
            if run_id:
                result["run_id"] = run_id
            if work_item_id:
                result["work_item_id"] = work_item_id

            log.info(
                f"Trigger {trigger_id} ({trigger.name}) invoked successfully"
            )
            return result

        except Exception as e:
            await self._record_invocation(
                invocation_id,
                trigger_id,
                now,
                source_ip,
                payload,
                headers,
                TriggerInvocationStatus.ERROR,
                error_message=str(e),
            )
            return {
                "status": "error",
                "message": str(e),
            }

    def _validate_signature(
        self,
        trigger: "Trigger",
        payload: Any,
        headers: Dict[str, str],
    ) -> bool:
        """
        Validate the webhook signature.

        Supports common signature formats:
        - X-Hub-Signature-256 (GitHub style, HMAC-SHA256)
        - X-Signature-256 (generic HMAC-SHA256)
        - X-Webhook-Signature (generic)
        """
        secret = trigger.webhook_secret
        if not secret:
            return True  # No secret = no validation required

        # Get the raw payload as bytes
        if isinstance(payload, (dict, list)):
            raw_payload = json.dumps(payload, separators=(",", ":")).encode()
        elif isinstance(payload, str):
            raw_payload = payload.encode()
        elif isinstance(payload, bytes):
            raw_payload = payload
        else:
            raw_payload = str(payload).encode()

        # Try different signature headers
        signature_headers = [
            "x-hub-signature-256",
            "x-signature-256",
            "x-webhook-signature",
            "x-signature",
        ]

        for header_name in signature_headers:
            signature = headers.get(header_name)
            if signature:
                return self._verify_hmac_signature(
                    secret.encode(),
                    raw_payload,
                    signature,
                )

        # No signature header found
        log.warning(f"Trigger {trigger.id}: no signature header found in request")
        return False

    def _verify_hmac_signature(
        self,
        secret: bytes,
        payload: bytes,
        signature: str,
    ) -> bool:
        """Verify HMAC signature."""
        # Handle "sha256=..." prefix
        if "=" in signature:
            algorithm, sig_value = signature.split("=", 1)
        else:
            algorithm = "sha256"
            sig_value = signature

        if algorithm == "sha256":
            expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        elif algorithm == "sha1":
            expected = hmac.new(secret, payload, hashlib.sha1).hexdigest()
        else:
            log.warning(f"Unknown signature algorithm: {algorithm}")
            return False

        return hmac.compare_digest(expected, sig_value)

    def _check_rate_limit(
        self,
        trigger: "Trigger",
        now: datetime,
    ) -> bool:
        """Check if the trigger's rate limit allows invocation."""
        if not trigger.rate_limit_enabled:
            return True

        # Clean up old entries (keep last minute)
        minute_ago = now - timedelta(minutes=1)
        self._rate_limit_tracker[trigger.id] = [
            ts for ts in self._rate_limit_tracker[trigger.id]
            if ts > minute_ago
        ]

        # Check limit
        if len(self._rate_limit_tracker[trigger.id]) >= trigger.rate_limit_max_per_minute:
            return False

        # Record this invocation
        self._rate_limit_tracker[trigger.id].append(now)
        return True

    def _apply_template(
        self,
        template_json: str,
        payload: Any,
        headers: Dict[str, str],
        trigger: "Trigger",
    ) -> Dict[str, Any]:
        """
        Apply payload template to create action inputs.

        Template variables:
        - {{payload.field}} - Access webhook body fields
        - {{headers.X-Header}} - Access request headers
        - {{meta.trigger_id}} - Trigger metadata
        - {{meta.timestamp}} - Invocation timestamp
        """
        if not template_json:
            # No template - use payload as-is if it's a dict
            if isinstance(payload, dict):
                return payload
            return {"payload": payload}

        template = json.loads(template_json)
        return self._resolve_template(template, payload, headers, trigger)

    def _resolve_template(
        self,
        template: Any,
        payload: Any,
        headers: Dict[str, str],
        trigger: "Trigger",
    ) -> Any:
        """Recursively resolve template variables."""
        if isinstance(template, str):
            return self._resolve_string_template(template, payload, headers, trigger)
        elif isinstance(template, dict):
            return {
                k: self._resolve_template(v, payload, headers, trigger)
                for k, v in template.items()
            }
        elif isinstance(template, list):
            return [
                self._resolve_template(item, payload, headers, trigger)
                for item in template
            ]
        else:
            return template

    def _resolve_string_template(
        self,
        template: str,
        payload: Any,
        headers: Dict[str, str],
        trigger: "Trigger",
    ) -> Any:
        """
        Resolve a string that may contain template variables.

        If the entire string is a single variable reference, return the actual value.
        Otherwise, perform string interpolation.
        """
        # Check if entire string is a single variable
        match = re.fullmatch(r"\{\{(.+?)\}\}", template.strip())
        if match:
            path = match.group(1).strip()
            return self._get_template_value(path, payload, headers, trigger)

        # String interpolation for mixed content
        def replace_var(m):
            path = m.group(1).strip()
            value = self._get_template_value(path, payload, headers, trigger)
            return str(value) if value is not None else ""

        return re.sub(r"\{\{(.+?)\}\}", replace_var, template)

    def _get_template_value(
        self,
        path: str,
        payload: Any,
        headers: Dict[str, str],
        trigger: "Trigger",
    ) -> Any:
        """Get a value from the template context by path."""
        parts = path.split(".")

        if not parts:
            return None

        root = parts[0]
        rest = parts[1:]

        if root == "payload":
            obj = payload
        elif root == "headers":
            obj = headers
        elif root == "meta":
            obj = {
                "trigger_id": trigger.id,
                "trigger_name": trigger.name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            return None

        # Navigate the path
        for part in rest:
            if isinstance(obj, dict):
                obj = obj.get(part)
            elif isinstance(obj, list):
                try:
                    obj = obj[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None

            if obj is None:
                return None

        return obj

    async def _record_invocation(
        self,
        invocation_id: str,
        trigger_id: str,
        now: datetime,
        source_ip: Optional[str],
        payload: Any,
        headers: Dict[str, str],
        status: str,
        run_id: Optional[str] = None,
        work_item_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Record a trigger invocation in the database."""
        from sema4ai.action_server._database import datetime_to_str
        from sema4ai.action_server._models import TriggerInvocation, get_db

        db = get_db()

        # Serialize payload and headers
        payload_json = None
        if payload is not None:
            try:
                payload_json = json.dumps(payload)
            except (TypeError, ValueError):
                payload_json = str(payload)

        headers_json = json.dumps(dict(headers)) if headers else None

        with db.connect():
            with db.transaction():
                invocation = TriggerInvocation(
                    id=invocation_id,
                    trigger_id=trigger_id,
                    invoked_at=datetime_to_str(now),
                    source_ip=source_ip,
                    payload_json=payload_json,
                    headers_json=headers_json,
                    status=status,
                    run_id=run_id,
                    work_item_id=work_item_id,
                    error_message=error_message,
                )
                db.insert(invocation)

    async def _create_action_run(
        self,
        trigger: "Trigger",
        inputs: Dict[str, Any],
    ) -> str:
        """Create an action run for a trigger."""
        from sema4ai.action_server._actions_run import (
            _create_run,
            _create_run_artifacts_dir,
        )
        from sema4ai.action_server._gen_ids import gen_uuid
        from sema4ai.action_server._models import Action, get_db

        if not trigger.action_id:
            raise ValueError("Trigger has no action_id configured")

        db = get_db()
        with db.connect():
            try:
                action = db.first(
                    Action,
                    "SELECT * FROM action WHERE id = ?",
                    [trigger.action_id],
                )
            except KeyError:
                raise ValueError(f"Action not found: {trigger.action_id}")

            if not action.enabled:
                raise ValueError(f"Action {action.id} is disabled")

        # Create the run
        run_id = gen_uuid("run")
        relative_artifacts_dir = _create_run_artifacts_dir(action, run_id)

        with db.connect():
            run = _create_run(
                action=action,
                run_id=run_id,
                inputs=inputs,
                relative_artifacts_dir=relative_artifacts_dir,
                request_id=f"trigger:{trigger.id}",
            )

        log.info(
            f"Trigger {trigger.id}: created run {run_id} for action {action.name}"
        )

        return run_id

    async def _create_work_item(
        self,
        trigger: "Trigger",
        inputs: Dict[str, Any],
    ) -> Optional[str]:
        """
        Create a work item for a trigger.

        Uses the actions-work-items package to create work items that can be
        consumed by producer-consumer workflows.

        Returns the work item ID.
        """
        from datetime import datetime, timezone

        queue_name = trigger.work_item_queue or "default"

        # Add trigger metadata
        inputs["_trigger_id"] = trigger.id
        inputs["_trigger_name"] = trigger.name
        inputs["_triggered_at"] = datetime.now(timezone.utc).isoformat()

        try:
            from actions.work_items import create_adapter, init, seed_input

            # Create adapter targeting the action server's work items storage
            from sema4ai.action_server._settings import get_settings
            settings = get_settings()

            # Use action server's data directory for work items
            db_path = str(settings.datadir / "workitems.db")
            files_dir = str(settings.datadir / "work_item_files")

            adapter = create_adapter(
                adapter_type="sqlite",
                db_path=db_path,
                queue_name=queue_name,
                files_dir=files_dir,
            )
            init(adapter)

            # Seed the work item
            work_item_id = seed_input(payload=inputs)

            log.info(
                f"Trigger {trigger.id}: created work item {work_item_id} "
                f"in queue '{queue_name}'"
            )
            return work_item_id

        except ImportError:
            log.warning(
                f"Trigger {trigger.id}: actions-work-items package not installed, "
                "cannot create work items. Install with: pip install actions-work-items"
            )
            return None
        except Exception as e:
            log.error(
                f"Trigger {trigger.id}: failed to create work item: {e}"
            )
            return None

    def generate_webhook_secret(self, length: int = 32) -> str:
        """Generate a secure random webhook secret."""
        return secrets.token_urlsafe(length)


# Global trigger engine instance
_global_trigger_engine: Optional[TriggerEngine] = None


def get_trigger_engine() -> TriggerEngine:
    """Get the global trigger engine instance."""
    global _global_trigger_engine
    if _global_trigger_engine is None:
        _global_trigger_engine = TriggerEngine()
    return _global_trigger_engine


def set_trigger_engine(engine: Optional[TriggerEngine]) -> None:
    """Set the global trigger engine instance."""
    global _global_trigger_engine
    _global_trigger_engine = engine
