from flask_restful import Resource

class Apicheck(Resource):
    def get(self):
        return {"info":"api is there"}, 200