from flask_restful import Resource, reqparse
from flask_restful.reqparse import RequestParser
from flask import json, jsonify, session
from sqlalchemy import func
from models import db, users, profiles, current_date, token, data, category #data und category statt data implementieren

from datetime import datetime
from decimal import Decimal
from constants import USERID, PROFILEID

#TODO export und import der Daten -> Backup

post_arguments = RequestParser(bundle_errors=True)

post_arguments.add_argument(
    name = "name",
    type = str,
    nullable = False,
    required = True
)

post_arguments.add_argument(
    name = "color", # mit # vor color-Wert
    type = str,
    nullable = False,
    required = True
)

post_arguments.add_argument(
    name = "unit",
    type = str,
    nullable = False,
    required = True
)


patch_arguments = post_arguments.copy()


class Categories(Resource):
    def get(self):
        profile_id = session.get(PROFILEID)
        if profile_id is None:
            profile = db.session.query(profiles).filter_by(userid=session.get(USERID)).order_by(profiles.id).first()
            profile_id = profile.id if profile else None
        categories = category.query.filter_by(profileid=profile_id).all()
        return jsonify([{
            'id': categ.id,
            'userid': categ.userid,
            'name': categ.name,
            'color': categ.color,
            'unit': categ.unit
        } for categ in categories])

    def post(self):
        given_data = post_arguments.parse_args(strict=False)
        user = db.session.query(users).filter(users.id == session.get(USERID)).first()


        if user:
            user_id = session.get(PROFILEID)
            if user_id is None:
                profile = db.session.query(profiles).filter_by(userid=session.get(USERID)).order_by(profiles.id).first()
                user_id = profile.id if profile else None
            
            # Kategorie-ID für den gegebenen Kategorienamen abrufen
            category_id = db.session.query(func.max(category.id)).scalar() + 1
            category_name = given_data["name"]
            category_unit = given_data["unit"]
            category_color = given_data["color"]
            print(category_name)
            
            # Bestehende Daten für den aktuellen Tag und die Kategorie abrufen
            existing_category = db.session.query(category).filter(category.profileid == user_id, category.name == category_name).first()
            
            if existing_category is None:
                # Neue Datenzeile einfügen
                new_category = category(
                    id=category_id,
                    userid=session.get(USERID),
                    profileid=user_id,
                    name=category_name,
                    unit=category_unit,
                    color=category_color
                )
                db.session.add(new_category)
                
            else:
                # Kategorie existiert bereits
                print("Kategorie existiert bereits")
                return {}, 403
            
            db.session.commit()
            return {}, 201
        else:
            print("Benutzer nicht gefunden")
            return {"message": "Benutzer nicht gefunden"}, 404
        
    def put(self, category_id):

        print("something")
        given_data = patch_arguments.parse_args(strict=False)
        user = db.session.query(users).filter(users.id == session.get(USERID)).first()


        

        if user:
            user_id = session.get(PROFILEID)
            if user_id is None:
                profile = db.session.query(profiles).filter_by(userid=session.get(USERID)).order_by(profiles.id).first()
                user_id = profile.id if profile else None
            print(f"Benutzer gefunden: {user_id}")

            existing_category = db.session.query(category).filter(category.profileid == user_id, category.id == category_id).first()
            
            if existing_category:
                print(f"Kategorie gefunden: {existing_category.name}")
                existing_category.name = given_data["name"]
                existing_category.unit = given_data["unit"]
                existing_category.color = given_data["color"]
                
                db.session.commit()
                return {}, 200
            else:
                print("Kategorie nicht gefunden")
                return {"message": "Kategorie nicht gefunden"}, 404
        else:
            print("Benutzer nicht gefunden")
            return {"message": "Benutzer nicht gefunden"}, 404
        

    def delete(self, category_id):
        user = db.session.query(users).filter(users.id == session.get(USERID)).first()
        
        if user:
            user_id = session.get(PROFILEID)
            if user_id is None:
                profile = db.session.query(profiles).filter_by(userid=session.get(USERID)).order_by(profiles.id).first()
                user_id = profile.id if profile else None
            category_to_delete = db.session.query(category).filter(category.profileid == user_id, category.id == category_id).delete()
            
            if category_to_delete:
                # Löschen aller verknüpften Daten
                db.session.query(data).filter(data.profileid == user_id, data.categoryid == category_id).delete()
                
                # Löschen der Kategorie
                db.session.commit()
                
                return {"message": "Kategorie erfolgreich gelöscht"}, 200
            else:
                return {"message": "Kategorie nicht gefunden"}, 404
        else:
            return {"message": "Benutzer nicht gefunden"}, 404
