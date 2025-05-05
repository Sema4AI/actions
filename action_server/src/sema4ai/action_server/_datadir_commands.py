import logging

from sema4ai.action_server._protocols import ArgumentsNamespaceDatadir

log = logging.getLogger(__name__)


def datadir_command(
    args: ArgumentsNamespaceDatadir,
) -> int:
    if args.datadir_command == "clear-actions":
        _clear_all_actions()
    return 0


def _clear_all_actions():
    """
    Disables all previously imported actions in the database.

    Args:
        datadir: The data directory where the database is located.

    Returns:
        None
    """
    from sema4ai.action_server._models import Action, get_db

    try:
        db = get_db()
        all_actions = db.all(Action)

        if not all_actions:
            log.info("No actions found to disable.")
            return

        with db.transaction():
            disabled_count = 0
            for action in all_actions:
                if action.enabled:
                    log.info("Disabling action: %s", action.name)
                    db.update_by_id(Action, action.id, dict(enabled=False))
                    disabled_count += 1

            if disabled_count > 0:
                log.info("Disabled %s action(s)", disabled_count)
            else:
                log.info("All actions were already disabled")
    except Exception as e:
        log.error("Error while disabling actions: %s", str(e))
        raise
