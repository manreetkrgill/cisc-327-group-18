from datetime import date

from flask import Blueprint, jsonify, request

from app import store
from app.models.overdue_alert import OverdueAlert
from app.routes.loans import FINE_PER_DAY

overdue_bp = Blueprint("overdue", __name__, url_prefix="/overdue")


@overdue_bp.route("", methods=["GET"])
def list_overdue():
    """Front-desk overdue notifications (R4).

    Returns every unreturned loan whose due date is before today, most overdue
    first. Optional ``?member_id=`` restricts the list to one member.
    """
    member_id = None
    raw_member_id = request.args.get("member_id")
    if raw_member_id is not None:
        try:
            member_id = int(raw_member_id)
        except ValueError:
            return jsonify({"error": "member_id must be an integer"}), 400

    today = date.today()
    alerts = []
    for loan in store.loans.values():
        if loan.return_date is not None or loan.due_date >= today:
            continue
        if member_id is not None and loan.member_id != member_id:
            continue
        alerts.append(OverdueAlert(
            loan,
            store.books.get(loan.book_id),
            store.members.get(loan.member_id),
            FINE_PER_DAY,
            today,
        ))

    alerts.sort(key=lambda a: (-a.days_overdue, a.loan_id))
    return jsonify({
        "as_of": today.isoformat(),
        "count": len(alerts),
        "alerts": [a.to_dict() for a in alerts],
    })
