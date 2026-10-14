from datetime import datetime
from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import jsonify
from sqlalchemy import func
from models import db, users, current_date, data, category
from login import get_authenticated_api_user_id
from .category import _get_active_owned_profile_id

post_arguments = RequestParser(bundle_errors=True)
post_arguments.add_argument(name="category", type=str, nullable=False, required=True)
post_arguments.add_argument(name="data", type=float, nullable=True, required=True)


class Data(Resource):
    def get(self):
        user_id = get_authenticated_api_user_id()
        if user_id is None:
            return {"message": "Nicht autorisiert"}, 401

        profile_id = _get_active_owned_profile_id(user_id)
        user_obj = db.session.query(users).filter_by(id=user_id).first()
        if not user_obj or profile_id is None:
            return {"message": "Benutzer oder Profil nicht gefunden"}, 404

        categories = db.session.query(category).filter_by(profileid=profile_id).all()
        category_map = {categ.id: categ.name for categ in categories}

        existing_data = db.session.query(data).filter_by(profileid=profile_id).order_by(data.date).all()

        output = []
        for i in existing_data:
            entry = {
                'userid': i.userid,
                'date': datetime.strftime(i.date, "%d-%m-%Y")
            }
            if i.categoryid in category_map:
                entry[category_map[i.categoryid]] = float(i.data) if i.data is not None else None
            output.append(entry)

        max_values = {}
        for categ_id, categ_name in category_map.items():
            max_value = db.session.query(func.max(data.data)).filter_by(
                profileid=profile_id, categoryid=categ_id
            ).scalar()
            max_values[categ_name] = float(max_value) if max_value is not None else None

        return jsonify({
            "maxValue": max_values,
            "data": output,
            "username": user_obj.username
        })

    def post(self):
        user_id = get_authenticated_api_user_id()
        if user_id is None:
            return {"message": "Nicht autorisiert"}, 401

        given_data = post_arguments.parse_args(strict=True)
        profile_id = _get_active_owned_profile_id(user_id)
        if profile_id is None:
            return {"message": "Profil nicht gefunden"}, 404

        category_name = (given_data["category"] or "").strip()
        value = given_data["data"]
        if value is not None and not (0 <= value <= 999.99):
            return {"message": "Wert muss zwischen 0 und 999,99 liegen"}, 400

        category_obj = db.session.query(category).filter_by(
            profileid=profile_id, name=category_name
        ).first()
        if not category_obj:
            return {"message": "Kategorie nicht gefunden"}, 404

        existing_data = db.session.query(data).filter_by(
            profileid=profile_id, date=current_date(), categoryid=category_obj.id
        ).first()

        if existing_data is None:
            new_data = data(
                userid=user_id,
                profileid=profile_id,
                date=current_date(),
                categoryid=category_obj.id,
                data=value
            )
            db.session.add(new_data)
        else:
            existing_data.data = value

        db.session.commit()
        return {}, 200
