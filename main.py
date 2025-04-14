from operations.mongo_operation import mongoOperation
from operations.common_operations import commonOperation
from utils.constant import constant_dict
import os, json
from flask import (Flask, render_template, request, session, send_file)
from flask_cors import CORS
from datetime import datetime, date
from operations.mail_sending import emailOperation
from utils.html_format import htmlOperation
import uuid

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = constant_dict.get("secreat_key")
UPLOAD_FOLDER = 'static/uploads/'

client = mongoOperation().mongo_connect(get_mongourl=constant_dict.get("mongo_url"))

@app.route("/quickoo/register-user", methods=["POST"])
def register_user():
    try:
        first_name = request.form["first_name"]
        dob = request.form["dob"]
        gender = request.form["gender"]
        password = request.form["password"]
        email = request.form.get("email", "")
        phone_number = request.form.get("phone_number", "")
        if email:
            is_email = True
        else:
            is_email = False

        if phone_number:
            is_phone = True
        else:
            is_phone = False

        get_all_user_data = mongoOperation().get_all_data_from_coll(client, "quickoo", "user_data")
        all_userids = [user_data["user_id"] for user_data in get_all_user_data]

        flag = True
        user_id = ""
        while flag:
            user_id = str(uuid.uuid4())
            if user_id not in all_userids:
                flag = False

        mapping_dict = {
            "user_id": user_id,
            "first_name": first_name,
            "dob": dob,
            "gender": gender,
            "password": password,
            "email": email,
            "phone_number": phone_number,
            "is_active": True,
            "is_email": is_email,
            "is_phone": is_phone,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        mongoOperation().insert_data_from_coll(client, "quickoo", "user_data", mapping_dict)
        response_data_msg = commonOperation().get_success_response(200, {"user_id": mapping_dict["user_id"]})
        return response_data_msg

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again..")
        print(f"{datetime.utcnow()}: Error in register user data route: {str(e)}")
        return response_data

@app.route("/quickoo/otp-email-verification", methods=["POST"])
def otp_email_verification():
    try:
        otp = request.form["otp"]
        email = request.form["email"]
        get_all_user_data = mongoOperation().get_all_data_from_coll(client, "quickoo", "user_data")
        all_emails = [user_data["email"] for user_data in get_all_user_data]
        if email in all_emails:
            return commonOperation().get_error_msg("Email already registered...")

        html_format = htmlOperation().otp_verification_process(otp)
        emailOperation().send_email(email, "Quickoo: Your Account Verification Code", html_format)
        response_data = commonOperation().get_success_response(200, {"message": "Mail sent successfully..."})
        return response_data

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again...")
        print(f"{datetime.now()}: Error in otp email verification: {str(e)}")
        return response_data

@app.route("/quickoo/login", methods=["POST"])
def login():
    try:
        email = request.form["email"]
        password = request.form["password"]
        email_condition_dict = {"email": email, "password": password}
        phone_condition_dict = {"phone_number": email, "password": password}
        email_data = mongoOperation().get_spec_data_from_coll(client, "quickoo", "user_data", email_condition_dict)
        phone_data = mongoOperation().get_spec_data_from_coll(client, "quickoo", "user_data", phone_condition_dict)
        if email_data or phone_data:
            if email_data:
                if email_data[0]["is_active"]:
                    return commonOperation().get_success_response(200, {"user_id": email_data[0]["user_id"]})
                else:
                    return commonOperation().get_error_msg("Your account was disabled, Contact administration")
            else:
                if phone_data[0]["is_active"]:
                    return commonOperation().get_success_response(200, {"user_id": phone_data[0]["user_id"]})
                else:
                    return commonOperation().get_error_msg("Your account was disabled, Contact administration")
        else:
            response_data = commonOperation().get_error_msg("Your credential doesn't match...")
        return response_data

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again...")
        print(f"{datetime.now()}: Error in login route: {str(e)}")
        return response_data

@app.route("/quickoo/forgot-password", methods=["POST"])
def forgot_password():
    try:
        email = request.form["email"]
        otp = request.form["otp"]
        email_condition_dict = {"email": email}
        email_data = mongoOperation().get_spec_data_from_coll(client, "quickoo", "user_data", email_condition_dict)
        if email_data:
            if email_data[0]["is_active"]:
                html_format = htmlOperation().otp_verification_process(otp)
                emailOperation().send_email(email, "Quickoo: Your Account Verification Code", html_format)
                return commonOperation().get_success_response(200, {"message": "Account Exits..", "user_id": email_data[0]["user_id"]})
            else:
                return commonOperation().get_error_msg("Your account was disabled, Contact administration")
        else:
            response_data = commonOperation().get_error_msg("Account not exits..")
        return response_data

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again...")
        print(f"{datetime.now()}: Error in forgot password route: {str(e)}")
        return response_data

@app.route("/quickoo/change-password", methods=["POST"])
def change_password():
    try:
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        user_id = request.args.get("user_id")
        if password==confirm_password:
            mongoOperation().update_mongo_data(client, "quickoo", "user_data", {"user_id":user_id}, {"password": password})
            return commonOperation().get_success_response(200, {"message": "Password updated"})
        else:
            return commonOperation().get_error_msg("Password doesn't match...")

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again...")
        print(f"{datetime.now()}: Error in change password route: {str(e)}")
        return response_data

@app.route("/quickoo/update-user-data", methods=["POST"])
def update_user_data():
    try:
        first_name = request.form.get("first_name")
        dob = request.form.get("dob")
        email = request.form.get("email", "")
        phone_number = request.form.get("phone_number", "")
        user_id = request.form.get("user_id", "")

        if first_name:
            mongoOperation().update_mongo_data(client, "quickoo", "user_data", {"user_id":user_id}, {"first_name": first_name})
            return commonOperation().get_success_response(200, {"message": "Name updated successfully..."})
        elif dob:
            mongoOperation().update_mongo_data(client, "quickoo", "user_data", {"user_id":user_id}, {"dob": dob})
            return commonOperation().get_success_response(200, {"message": "Date of birth updated successfully..."})
        elif email:
            mongoOperation().update_mongo_data(client, "quickoo", "user_data", {"user_id":user_id}, {"email": email, "is_email": True})
            return commonOperation().get_success_response(200, {"message": "Email updated successfully..."})
        elif phone_number:
            mongoOperation().update_mongo_data(client, "quickoo", "user_data", {"user_id":user_id}, {"phone_number": phone_number, "is_phone": True})
            return commonOperation().get_success_response(200, {"message": "Phone number updated successfully..."})
        else:
            return commonOperation().get_error_msg("Something won't wrong!")

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again...")
        print(f"{datetime.now()}: Error in updare user data route: {str(e)}")
        return response_data


# @app.route("/quickoo/driving_licence", methods=["POST"])
# def change_password():
#     try:
#         password = request.form["password"]
#         confirm_password = request.form["confirm_password"]
#         user_id = request.args.get("user_id")
#         if password==confirm_password:
#             mongoOperation().update_mongo_data(client, "quickoo", "user_data", {"user_id":user_id}, {"password": password})
#             return commonOperation().get_success_response(200, {"message": "Password updated"})
#         else:
#             return commonOperation().get_error_msg("Password doesn't match...")
#
#     except Exception as e:
#         response_data = commonOperation().get_error_msg("Please try again...")
#         print(f"{datetime.now()}: Error in change password route: {str(e)}")
#         return response_data

@app.route("/quickoo/sms-sending", methods=["POST"])
def sms_sending():
    try:
        number = request.form["number"]
        otp = request.form["otp"]
        message_body = f"OTP was: {otp}"
        emailOperation().sms_sending(message_body, number)
        response_data_msg = commonOperation().get_success_response(200, {"message": "Sms sent successfully..."})
        return response_data_msg

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again..")
        print(f"{datetime.utcnow()}: Error in sms sending for phone number: {str(e)}")
        return response_data




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
