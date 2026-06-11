from flask import jsonify, redirect
from flask_jwt_extended import JWTManager

jwt = JWTManager()

def init_jwt(app):
    jwt.init_app(app)

    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        print("1")
        return redirect('/login')

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        print("2")
        return redirect('/login')
