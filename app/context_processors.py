from flask import g

def inject_current_user():
    return {'current_user': getattr(
          g, 'current_user', None
    )}