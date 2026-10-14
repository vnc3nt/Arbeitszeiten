from decimal import Decimal, InvalidOperation
from flask import jsonify, session
from flask_restful import Resource, reqparse
from constants import PROFILEID
from models import db, profiles, category, data
from login import get_authenticated_api_user_id

create_parser = reqparse.RequestParser()
create_parser.add_argument("name", type=str, required=True)
create_parser.add_argument("maxhours", type=float, required=True)

update_parser = reqparse.RequestParser()
update_parser.add_argument("name", type=str, required=False)
update_parser.add_argument("visible", type=bool, required=False)


def _serialize(profile):
    return {
        "id": profile.id,
        "name": profile.name,
        "maxhours": float(profile.maxhours or 0),
        "visible": bool(profile.visible),
        "position": int(profile.position or 0),
    }


def _owned_profile(profile_id, user_id):
    if user_id is None:
        return None
    return profiles.query.filter_by(id=profile_id, userid=user_id).first()


class Profiles(Resource):
    def get(self):
        user_id = get_authenticated_api_user_id()
        if user_id is None:
            return {"message": "Nicht autorisiert"}, 401

        profile_rows = (
            profiles.query.filter_by(userid=user_id)
            .order_by(profiles.position.asc(), profiles.id.asc())
            .all()
        )

        active_profile_id = session.get(PROFILEID)
        if not any(profile.id == active_profile_id for profile in profile_rows):
            active_profile = next((p for p in profile_rows if p.visible), None)
            active_profile_id = active_profile.id if active_profile else None
            if active_profile_id is not None:
                session[PROFILEID] = active_profile_id

        return jsonify({
            "profiles": [_serialize(profile) for profile in profile_rows],
            "active_profile_id": active_profile_id,
        })

    def post(self):
        user_id = get_authenticated_api_user_id()
        if user_id is None:
            return {"message": "Nicht autorisiert"}, 401

        values = create_parser.parse_args()
        name = (values["name"] or "").strip()
        if not name or len(name) > 30:
            return {"message": "Ungültiger Profilname"}, 400

        try:
            maxhours = Decimal(str(values["maxhours"]))
        except (InvalidOperation, TypeError):
            return {"message": "Ungültige Monatsstunden"}, 400

        if maxhours <= 0 or maxhours > Decimal("999.99"):
            return {"message": "Ungültige Monatsstunden"}, 400

        if profiles.query.filter_by(userid=user_id, name=name).first():
            return {"message": "Dieses Profil existiert bereits"}, 409

        max_pos = db.session.query(db.func.max(profiles.position)).filter_by(userid=user_id).scalar()
        next_pos = (max_pos + 1) if max_pos is not None else 0

        profile = profiles(
            userid=user_id,
            name=name,
            maxhours=maxhours,
            visible=True,
            position=next_pos,
        )
        db.session.add(profile)
        db.session.commit()
        session[PROFILEID] = profile.id
        return _serialize(profile), 201

    def patch(self, profile_id):
        user_id = get_authenticated_api_user_id()
        if user_id is None:
            return {"message": "Nicht autorisiert"}, 401

        profile = _owned_profile(profile_id, user_id)
        if profile is None:
            return {"message": "Profil nicht gefunden"}, 404

        values = update_parser.parse_args()
        if values.get("name") is not None:
            name = values["name"].strip()
            if not name or len(name) > 30:
                return {"message": "Ungültiger Profilname"}, 400
            duplicate = profiles.query.filter(
                profiles.userid == user_id,
                profiles.name == name,
                profiles.id != profile.id,
            ).first()
            if duplicate:
                return {"message": "Dieses Profil existiert bereits"}, 409
            profile.name = name

        if values.get("visible") is not None:
            visible = bool(values["visible"])
            if not visible and profile.visible and profiles.query.filter_by(
                userid=user_id, visible=True
            ).count() <= 1:
                return {"message": "Mindestens ein Profil muss sichtbar bleiben"}, 400
            profile.visible = visible
            if not visible and session.get(PROFILEID) == profile.id:
                replacement = profiles.query.filter_by(
                    userid=user_id, visible=True
                ).filter(profiles.id != profile.id).order_by(profiles.id).first()
                session[PROFILEID] = replacement.id if replacement else None

        db.session.commit()
        return _serialize(profile), 200

    def delete(self, profile_id):
        user_id = get_authenticated_api_user_id()
        if user_id is None:
            return {"message": "Nicht autorisiert"}, 401

        profile = _owned_profile(profile_id, user_id)
        if profile is None:
            return {"message": "Profil nicht gefunden"}, 404

        if profiles.query.filter_by(userid=user_id).count() <= 1:
            return {"message": "Das letzte Profil kann nicht gelöscht werden"}, 400

        db.session.query(data).filter_by(profileid=profile.id).delete()
        db.session.query(category).filter_by(profileid=profile.id).delete()
        db.session.delete(profile)
        db.session.commit()

        if session.get(PROFILEID) == profile_id:
            replacement = profiles.query.filter_by(
                userid=user_id, visible=True
            ).order_by(profiles.id).first()
            session[PROFILEID] = replacement.id if replacement else None

        return {"message": "Arbeitsprofil gelöscht"}, 200


class ProfileSwitch(Resource):
    def post(self, profile_id):
        user_id = get_authenticated_api_user_id()
        if user_id is None:
            return {"message": "Nicht autorisiert"}, 401

        profile = _owned_profile(profile_id, user_id)
        if profile is None or not profile.visible:
            return {"message": "Profil nicht gefunden"}, 404

        session[PROFILEID] = profile.id
        return {"message": "Profil gewechselt"}, 200
