from operations.mongo_operation import mongoOperation
from operations.common_operations import commonOperation
from utils.constant import constant_dict
import os, json
from flask import (Flask, render_template, request, session, send_file)
from flask_cors import CORS
from datetime import datetime, date
from operations.mail_sending import emailOperation
from utils.html_format import htmlOperation
from operations.maps_integration import MapsIntegration
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
            "profile_url": "",
            "dob": dob,
            "gender": gender,
            "password": password,
            "email": email,
            "phone_number": phone_number,
            "bio": "",
            "vehicle_details": {},
            "payment_details": {},
            "is_profile": False,
            "is_vehicle": False,
            "is_email": is_email,
            "is_bio": False,
            "is_phone": is_phone,
            "is_payment": False,
            "is_verified": False,
            "is_active": True,
            "type": "email",
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

@app.route("/quickoo/google-auth", methods=["POST"])
def google_auth():
    try:
        first_name = request.form.get("first_name", "")
        profile_url = request.form.get("profile_url", "")
        email = request.form.get("email", "")
        if profile_url:
            is_profile = True
        else:
            is_profile = False

        get_all_user_data = mongoOperation().get_all_data_from_coll(client, "quickoo", "user_data")
        all_userids = [user_data["user_id"] for user_data in get_all_user_data]
        all_emails = [user_data["email"] for user_data in get_all_user_data]
        if email in all_emails:
            return commonOperation().get_error_msg("Email already exits..")

        flag = True
        user_id = ""
        while flag:
            user_id = str(uuid.uuid4())
            if user_id not in all_userids:
                flag = False

        mapping_dict = {
            "user_id": user_id,
            "first_name": first_name,
            "profile_url": profile_url,
            "dob": "",
            "gender": "",
            "password": "",
            "email": email,
            "phone_number": "",
            "bio": "",
            "vehicle_details": {},
            "payment_details": {}
            "is_profile": is_profile,
            "is_vehicle": False,
            "is_email": True,
            "is_bio": False,
            "is_phone": False,
            "is_payment": False,
            "is_verified": False,
            "is_active": True,
            "type": "google",
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

@app.route("/quickoo/get-user-data", methods=["POST"])
def get_user_data():
    try:
        user_id = request.form["user_id"]
        get_all_user_data = list(mongoOperation().get_spec_data_from_coll(client, "quickoo", "user_data", {"user_id": user_id}))
        response_data = get_all_user_data[0]
        del response_data["_id"]
        del response_data["created_at"]
        del response_data["updated_at"]
        response_data_msg = commonOperation().get_success_response(200, response_data)
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

@app.route("/quickoo/get-cities-for-location", methods=["POST"])
def get_cities_for_locations():
    try:
        from_location = request.form.get("from")
        to_location = request.form.get("to")
        cities = MapsIntegration().find_cities_along_route(from_location, to_location, sample_points=20)
        return commonOperation().get_success_response(200, cities)

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again...")
        print(f"{datetime.now()}: Error in updare user data route: {str(e)}")
        return response_data

@app.route("/quickoo/save_rides", methods=["POST"])
def save_rides():
    try:
        user_id = request.form.get("user_id")
        from_location = request.form.get("from")
        to_location = request.form.get("to")
        cities = list(request.form.get("cities"))
        start_date = request.form.get("start_date")
        start_time = request.form.get("start_time")
        person_count = request.form.get("count")
        is_daily = request.form.get("is_daily")
        days = list(request.form.get("days"))
        if from_location.lower() == to_location.lower():
            response_data = commonOperation().get_error_msg("Pickup & Drop Point are same...")
        else:
            mapping_dict = {
                "user_id": user_id,
                "from_location": from_location,
                "to_location": to_location,
                "cities": list(cities),
                "start_date": start_date,
                "start_time": start_time,
                "persons": int(person_count),
                "is_daily": is_daily,
                "days": list(days),
                "is_completed": False,
                "created_on": datetime.utcnow()
            }
        
            mongoOperation().insert_data_from_coll(client, "quickoo", "rides_data", mapping_dict)
            response_data = commonOperation().get_success_response(200, {"message": "Ride created successfully..."})

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again...")
        print(f"{datetime.now()}: Error in create ride route: {str(e)}")
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
