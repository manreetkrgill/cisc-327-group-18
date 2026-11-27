from flask import Blueprint, jsonify, request
from datetime import date

from app import store
from app.models.member import Member
from app.routes.loans import FINE_PER_DAY

members_bp = Blueprint("members", __name__, url_prefix="/members")


@members_bp.route("", methods=["GET"])
def list_members():
    return jsonify([m.to_dict() for m in store.members.values()])


@members_bp.route("", methods=["POST"])
def create_member():
    data = request.get_json()
    member_id = store.next_id("member")
    member = Member(id=member_id, name=data["name"], email=data["email"])
    store.members[member_id] = member
    return jsonify(member.to_dict()), 201


@members_bp.route("/<int:member_id>", methods=["GET"])
def get_member(member_id):
    member = store.members.get(member_id)
    if member is None:
        return jsonify({"error": "Member not found"}), 404
        
    # Calculate total fines for all active overdue loans
    total_fine = 0.0
    today = date.today()
    for loan in store.loans.values():
        if loan.member_id == member_id and loan.return_date is None:
            days_overdue = max(0, (today - loan.due_date).days)
            total_fine += days_overdue * FINE_PER_DAY
            
    # Convert member to dict and inject the new field
    member_data = member.to_dict()
    member_data["total_fines"] = round(total_fine, 2)
    
    return jsonify(member_data)


@members_bp.route("/<int:member_id>", methods=["PUT"])
def update_member(member_id):
    member = store.members.get(member_id)
    if member is None:
        return jsonify({"error": "Member not found"}), 404
    data = request.get_json()
    member.name = data.get("name", member.name)
    member.email = data.get("email", member.email)
    return jsonify(member.to_dict())


@members_bp.route("/<int:member_id>", methods=["DELETE"])
def delete_member(member_id):
    member = store.members.pop(member_id, None)
    if member is None:
        return jsonify({"error": "Member not found"}), 404
    return "", 204