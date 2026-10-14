import re
from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import jsonify, session
from models import db, profiles, data, category
from constants import PROFILEID
from login import get_authenticated_api_user_id

HEX_COLOR_REGEX = re.compile(r"^#[0-9a-fA-F]{6}$")

post_arguments = RequestParser(bundle_errors=True)
post_arguments.add_argument(name="name", type=str, nullable=False, required=True)
post_arguments.add_argument(name="color", type=str, nullable=False, required=True)

patch_arguments = post_arguments.copy()


def _get_active_owned_profile_id(user_id: int):
    profile_id = session.get(PROFILEID)
    if profile_id is not None:
        owned = db.session.query(profiles).filter_by(id=profile_id, userid=user_id).first()
        if owned:
            return owned.id
    first_profile = db.session.query(profiles).filter_by(userid=user_id).order_by(profiles.id).first()
    if first_profile:
        session[PROFILEID] = first_profile.id
        return first_profile.id
    return None


class Categories(Resource):
    def get(self):
        user_id = get_authenticated_api_user_id()
        if user_id is None:
            return {"message": "Nicht autorisiert"}, 401

        profile_id = _get_active_owned_profile_id(user_id)
        if profile_id is None:
            return jsonify([])

        categories = category.query.filter_by(profileid=profile_id, userid=user_id).all()
        return jsonify([{
            'id': categ.id,
            'userid': categ.userid,
            'name': categ.name,
            'color': categ.color,
        } for categ in categories])

    def post(self):
        user_id = get_authenticated_api_user_id()
        if user_id is None:
            return {"message": "Nicht autorisiert"}, 401

        given_data = post_arguments.parse_args(strict=False)
        profile_id = _get_active_owned_profile_id(user_id)
        if profile_id is None:
            return {"message": "Kein Profil gefunden"}, 404

        category_name = (given_data["name"] or "").strip()
        category_color = (given_data["color"] or "").strip()

        if not category_name or len(category_name) > 30:
            return {"message": "Ungültiger Kategoriename"}, 400
        if not HEX_COLOR_REGEX.fullmatch(category_color):
            return {"message": "Ungültiger Farbcode (Format: #RRGGBB)"}, 400

        existing_category = db.session.query(category).filter_by(
            profileid=profile_id, name=category_name
        ).first()
        if existing_category is not None:
            return {"message": "Kategorie existiert bereits"}, 409

        new_category = category(
            userid=user_id,
            profileid=profile_id,
            name=category_name,
            color=category_color
        )
        db.session.add(new_category)
        db.session.commit()
        return {}, 201

    def put(self, category_id):
        user_id = get_authenticated_api_user_id()
        if user_id is None:
            return {"message": "Nicht autorisiert"}, 401

        given_data = patch_arguments.parse_args(strict=False)
        profile_id = _get_active_owned_profile_id(user_id)

        existing_category = db.session.query(category).filter_by(
            profileid=profile_id, userid=user_id, id=category_id
        ).first()
        if not existing_category:
            return {"message": "Kategorie nicht gefunden"}, 404

        category_name = (given_data["name"] or "").strip()
        category_color = (given_data["color"] or "").strip()
        if not category_name or len(category_name) > 30 or not HEX_COLOR_REGEX.fullmatch(category_color):
            return {"message": "Ungültige Eingabedaten"}, 400

        existing_category.name = category_name
        existing_category.color = category_color
        db.session.commit()
        return {}, 200

    def delete(self, category_id):
        user_id = get_authenticated_api_user_id()
        if user_id is None:
            return {"message": "Nicht autorisiert"}, 401

        profile_id = _get_active_owned_profile_id(user_id)
        deleted = db.session.query(category).filter_by(
            profileid=profile_id, userid=user_id, id=category_id
        ).delete()

        if deleted:
            db.session.query(data).filter_by(profileid=profile_id, categoryid=category_id).delete()
            db.session.commit()
            return {"message": "Kategorie erfolgreich gelöscht"}, 200
        return {"message": "Kategorie nicht gefunden"}, 404
