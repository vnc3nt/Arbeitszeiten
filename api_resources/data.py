from flask_restful import Resource, reqparse
from flask_restful.reqparse import RequestParser
from flask import json, jsonify, session
from sqlalchemy import func
from models import db, users, current_date, token, newdata, category #newdata und category statt data implementieren

from datetime import datetime
from decimal import Decimal
from constants import USERID

#TODO export und import der Daten -> Backup

post_arguments = RequestParser(bundle_errors=True)

post_arguments.add_argument(
    name = "category",
    type = str,
    nullable = False,
    required = True
)

post_arguments.add_argument(
    name = "data",
    type = float, # 47,55
    nullable = True,
    required = True
)

post_arguments.add_argument(
    name = "user",
    type = float,# userID
    nullable = False,
    required = True
)


patch_arguments = post_arguments.copy()
patch_arguments.add_argument(
    name = "date",
    type = str, # 2005-04-10
    nullable = True,
    required = False
)

class Data(Resource):
    def get(self):
        user_id = session.get(USERID)
        
        # Abfrage der Kategorien für den Nutzer
        categories = db.session.query(category).filter(category.userId == user_id).all()
        category_map = {categ.id: categ.name for categ in categories}
        
        # Abfrage der Daten
        existing_data = db.session.query(newdata).filter(newdata.userid == user_id).order_by(newdata.date).all()
        username = db.session.query(users).filter(users.id == user_id).first().username
        
        # Strukturierung der Daten für die Ausgabe
        output = []
        for i in existing_data:
            entry = {
                'userId': i.userid,
                'date': datetime.strftime(i.date, "%d-%m-%Y")
            }
            if i.categoryId in category_map:
                entry[category_map[i.categoryId]] = float(i.data) if i.data is not None else None
            output.append(entry)
        
        # Maximalwerte für jede Kategorie berechnen
        max_values = {}
        for categ_id, categ_name in category_map.items():
            max_value = db.session.query(func.max(newdata.data)).filter(newdata.userid == user_id, newdata.categoryId == categ_id).scalar()
            max_values[categ_name] = float(max_value) if max_value is not None else None
        
        return jsonify({
            "maxValue": max_values,
            "data": output,
            "username": username
        })

    def post(self):
        given_data = post_arguments.parse_args(strict=True)
        user = db.session.query(users).filter(users.id == session.get(USERID)).first()
        
        if user:
            user_id = user.id
            
            # Kategorie-ID für den gegebenen Kategorienamen abrufen
            category_name = given_data["category"]
            value = given_data["data"]
            category_obj = db.session.query(category).filter(category.userId == user_id, category.name == category_name).first()
            
            if not category_obj:
                print("Error: No such category found.")
            else:
                category_id = category_obj.id
            
            # Bestehende Daten für den aktuellen Tag und die Kategorie abrufen
            existing_data = db.session.query(newdata).filter(newdata.userid == user_id, newdata.date == current_date(), newdata.categoryId == category_id).first()
            
            if existing_data is None:
                # Neue Datenzeile einfügen
                new_data = newdata(userid=user_id, date=current_date(), categoryId=category_id, data=value)
                db.session.add(new_data)
            else:
                # Vorhandene Datenzeile aktualisieren
                existing_data.data = value
            
            db.session.commit()
            return {}, 200
        else:
            print("Benutzer nicht gefunden")
            return {"message": "Benutzer nicht gefunden"}, 404

