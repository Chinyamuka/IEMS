"""
IEMS Category Management Routes

Administrator-only CRUD for the Category lookup table.

Categories are referenced by Equipment.category_id.
Deleting a category that still has equipment attached
is blocked by a server-side guard.
"""

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)

from app.extensions import db
from app.models import Category, Equipment
from app.auth.decorators import login_required
from app.utils.permissions import role_required


# =========================================================
# BLUEPRINT
# =========================================================

categories_bp = Blueprint(
    "categories",
    __name__,
    url_prefix="/categories",
)


# =========================================================
# HELPER
# =========================================================

def _name_in_use(name, exclude_id=None):
    """True if a Category with this name already exists."""
    query = Category.query.filter(
        db.func.lower(Category.name) == name.lower()
    )

    if exclude_id is not None:
        query = query.filter(Category.id != exclude_id)

    return query.first() is not None


# =========================================================
# LIST
# =========================================================

@categories_bp.route("/")
@login_required
@role_required("Administrator")
def index():
    """Display all categories."""
    categories = Category.query.order_by(
        Category.name.asc()
    ).all()

    return render_template(
        "categories/index.html",
        categories=categories,
    )


# =========================================================
# CREATE
# =========================================================

@categories_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required("Administrator")
def create():
    """Create a new category."""

    if request.method == "POST":

        name        = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Category name is required.", "danger")
            return render_template("categories/create.html")

        if _name_in_use(name):
            flash(
                f"A category named '{name}' already exists.",
                "danger",
            )
            return render_template("categories/create.html")

        category = Category(
            name=name,
            description=description or None,
        )

        db.session.add(category)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "The category could not be saved. "
                "Please try again.",
                "danger",
            )
            return render_template("categories/create.html")

        flash(
            f"Category '{category.name}' was created.",
            "success",
        )
        return redirect(url_for("categories.index"))

    return render_template("categories/create.html")


# =========================================================
# EDIT
# =========================================================

@categories_bp.route("/<int:category_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("Administrator")
def edit(category_id):
    """Edit an existing category."""

    category = db.get_or_404(Category, category_id)

    if request.method == "POST":

        name        = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Category name is required.", "danger")
            return render_template(
                "categories/edit.html",
                category=category,
            )

        if _name_in_use(name, exclude_id=category.id):
            flash(
                f"A category named '{name}' already exists.",
                "danger",
            )
            return render_template(
                "categories/edit.html",
                category=category,
            )

        category.name = name
        category.description = description or None

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "The category could not be saved. "
                "Please try again.",
                "danger",
            )
            return render_template(
                "categories/edit.html",
                category=category,
            )

        flash(
            f"Category '{category.name}' was updated.",
            "success",
        )
        return redirect(url_for("categories.index"))

    return render_template(
        "categories/edit.html",
        category=category,
    )


# =========================================================
# DELETE
# =========================================================

@categories_bp.route("/<int:category_id>/delete", methods=["POST"])
@login_required
@role_required("Administrator")
def delete(category_id):
    """
    Delete a category.

    POST-only. Refuses to delete a category that is
    still referenced by any equipment record.
    """

    category = db.get_or_404(Category, category_id)

    # -----------------------------------------------------
    # REFERENCE GUARD
    # -----------------------------------------------------

    equipment_count = Equipment.query.filter_by(
        category_id=category.id
    ).count()

    if equipment_count > 0:
        flash(
            f"Cannot delete '{category.name}' — "
            f"{equipment_count} equipment item"
            f"{'s are' if equipment_count != 1 else ' is'} "
            f"still categorised here.",
            "warning",
        )
        return redirect(url_for("categories.index"))

    # -----------------------------------------------------
    # DELETE
    # -----------------------------------------------------

    db.session.delete(category)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(
            "The category could not be deleted. "
            "Please try again.",
            "danger",
        )
        return redirect(url_for("categories.index"))

    flash(
        f"Category '{category.name}' was deleted.",
        "success",
    )
    return redirect(url_for("categories.index"))

