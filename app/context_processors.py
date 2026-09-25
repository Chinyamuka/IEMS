from flask import g, session

from app.models import User


def load_current_user():
    """
    Load the authenticated user from the database
    for the current request.
    """
    user_id = session.get("user_id")
    if not user_id:
        g.current_user = None
        return

    g.current_user = User.query.get(user_id)
    # If the account was deleted or deactivated,
    # remove the authentication session.
    if g.current_user is None or not g.current_user.is_active:
        session.clear()
        g.current_user = None


def inject_current_user():
    """
    Make the current user and permission helper
    available to every Jinja template.
    """
    def has_role(*roles):
        """
        Check whether the current user has one
        of the supplied roles.
        """
        if g.current_user is None:
            return False
        return g.current_user.role in roles
    return {
        "current_user": getattr(
            g,
            "current_user",
            None
        ),
        "has_role": has_role,
    }