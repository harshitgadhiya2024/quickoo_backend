from operations.mongo_operation import mongoOperation
from operations.common_operations import commonOperation
from utils.constant import constant_dict
import os, json
from flask import (Flask, render_template, request, session, send_file, jsonify, send_from_directory)
from flask_cors import CORS
from datetime import datetime, date
from operations.mail_sending import emailOperation
from utils.html_format import htmlOperation
from operations.maps_integration import MapsIntegration
import uuid
from werkzeug.utils import secure_filename
from operations.route_checker import RouteValidator

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = constant_dict.get("secreat_key")
UPLOAD_FOLDER = 'static/uploads/'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Utility to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        for user_data in get_all_user_data:
            if email==user_data["email"]:
                response_data_msg = commonOperation().get_success_response(200, {"user_id": user_data["user_id"]})
                return response_data_msg

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
            "payment_details": {},
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
        cities = json.loads(request.form.get("cities"))
        start_date = request.form.get("start_date")
        start_time = request.form.get("start_time")
        person_count = int(request.form.get("count", 1))
        is_daily = request.form.get("is_daily")
        if is_daily=="false":
            is_daily = False
        else:
            is_daily = True
        days = json.loads(request.form.get("days"))
        if from_location.lower() == to_location.lower():
            response_data = commonOperation().get_error_msg("Pickup & Drop Point are same...")
        else:
            all_rides_data = list(mongoOperation().get_all_data_from_coll(client, "quickoo", "rides_data"))
            all_rideids = [ride_data["ride_id"] for ride_data in all_rides_data]

            flag = True
            ride_id = ""
            while flag:
                ride_id = str(uuid.uuid4())
                if ride_id not in all_rideids:
                    flag = False
            
            mapping_dict = {
                "user_id": user_id,
                "ride_id": ride_id,
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
        
        return response_data
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


@app.route('/upload-profile-photo', methods=['POST'])
def upload_profile_picture():
    try:
        user_id = request.form.get("user_id", "")
        if 'image' not in request.files:
            return commonOperation().get_error_msg("No selected file")
        
        file = request.files['image']

        if file.filename == '':
            return commonOperation().get_error_msg("No selected file")
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_url = request.host_url + 'static/uploads/' + filename
            mongoOperation().update_mongo_data(client, "quickoo", "user_data", {"user_id": user_id}, {"profile_url": image_url, "is_profile": True})
            return commonOperation().get_success_response(200, {"profile_url": image_url})
        else:
            return commonOperation().get_error_msg("File type not allowed..")
        
    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again..")
        print(f"{datetime.utcnow()}: Error in sms sending for phone number: {str(e)}")
        return response_data

@app.route('/quickoo/check-verified', methods=['GET'])
def check_verified():
    try:
        user_id = request.args.get("user_id", "")
        user_data = list(mongoOperation().get_spec_data_from_coll(client, "quickoo", "user_data", {"user_id": user_id}))
        user_data = user_data[0]
        return commonOperation().get_success_response(200, {"verified": user_data["is_verified"]})
        
    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again..")
        print(f"{datetime.utcnow()}: Error in check verified status from user: {str(e)}")
        return response_data

@app.route('/quickoo/get_ride', methods=['POST'])
def get_ride():
    try:
        user_id = request.form.get("user_id", "")
        pickup = request.form.get("pickup", "")
        drop = request.form.get("drop", "")
        start_date = request.form.get("start_date", "")
        count = int(request.form.get("count", 1))
        ride_data = list(mongoOperation().get_spec_data_from_coll(client, "quickoo", "rides_data", {"is_completed": False, "start_date": start_date}))
        validator = RouteValidator("AIzaSyB-Z1yfO79TH2uuDT9-fu-0YmHCRL_B9IA")
        
        # Add the route from your example
        all_data = []
        for ride_d in ride_data:
            del ride_d["_id"]
            validator.add_route(
                route_id=f"{ride_d['from_location']}_{ride_d['to_location']}",
                from_city=ride_d["from_location"],
                to_city=ride_d["to_location"],
                via_cities=[f"{city}, Gujarat, India" for city in ride_d["cities"]]
            )
            print("step1")
            result = validator.validate_user_trip(pickup, drop)
            print("step2")
            if result['valid']:
                user_id_data = ride_d["user_id"]
                print("step3")
                user_spec_data = list(mongoOperation().get_spec_data_from_coll(client, "quickoo", "user_data", {"user_id": user_id_data}))[0]
                del user_spec_data["_id"]
                print("step4")
                all_data.append({"user_data": user_spec_data, "rides_data": ride_d})
            else:
                print(f"❌ Invalid trip. The journey from {result.get('pickup_address', pickup)} to {result.get('drop_address', drop)} doesn't match any defined routes.")
            print("completed")
        return commonOperation().get_success_response(200, all_data)
        
    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again..")
        print(f"{datetime.utcnow()}: Error in check verified status from user: {str(e)}")
        return response_data

@app.route('/quickoo/get_past_rides', methods=['GET'])
def get_past_rides():
    try:
        user_id = request.form.get("user_id", "")
        ride_data = mongoOperation().get_spec_data_from_coll(client, "quickoo", "rides_data", {"user_id": user_id})
        rides_data = []
        for ride in ride_data:
            del ride["_id"]
            rides_data.append(ride)
        return commonOperation().get_success_response(200, rides_data)
        
    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again..")
        print(f"{datetime.utcnow()}: Error in check get past rides from user: {str(e)}")
        return response_data
    
@app.route('/quickoo/get_spec_past_ride', methods=['GET'])
def get_spec_past_ride():
    try:
        ride_id = request.form.get("ride_id", "")
        ride_data = mongoOperation().get_spec_data_from_coll(client, "quickoo", "rides_data", {"ride_id": ride_id})
        rides_data = []
        for ride in ride_data:
            passengers = []
            if ride.get("passengers", "none")=="none":
                ride["passengers"]=passengers
            del ride["_id"]

            rides_data.append(ride)
        return commonOperation().get_success_response(200, rides_data)
        
    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again..")
        print(f"{datetime.utcnow()}: Error in check get past rides from user: {str(e)}")
        return response_data


#User creation in quickoo
@app.route("/quickoo_uk/register-user", methods=["POST"])
def quickoo_uk_register_user():
    try:
        name = request.form["name"]
        email = request.form["email"]
        phone_number = request.form["phone_number"]
        gender = request.form["gender"]
        password = request.form["password"]

        get_all_user_data = mongoOperation().get_all_data_from_coll(client, "quickoo_uk", "user_data")
        all_emails = [user_data["email"] for user_data in get_all_user_data]
        if email in all_emails:
            return commonOperation().get_error_msg("Email already registered...")

        get_all_user_data = mongoOperation().get_all_data_from_coll(client, "quickoo_uk", "login_mapping")
        all_userids = [user_data["id"] for user_data in get_all_user_data]

        flag = True
        user_id = ""
        while flag:
            user_id = str(uuid.uuid4())
            if user_id not in all_userids:
                flag = False

        mapping_dict = {
            "id": user_id,
            "name": name,
            "gender": gender,
            "email": email,
            "phone_number": phone_number,
            "password": password,
            "user_type": "user",
            "type": "email",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        login_mapping = {
            "id": user_id,
            "email": email,
            "password": password,
            "user_type": "user",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        mongoOperation().insert_data_from_coll(client, "quickoo_uk", "user_data", mapping_dict)
        mongoOperation().insert_data_from_coll(client, "quickoo_uk", "login_mapping", login_mapping)
        response_data_msg = commonOperation().get_success_response(200, {"id": user_id, "email": email})
        return response_data_msg

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again..")
        print(f"{datetime.utcnow()}: Error in register user data route: {str(e)}")
        return response_data

# login process for user data
@app.route("/quickoo_uk/login", methods=["POST"])
def quickoo_uk_login_user():
    try:
        email = request.form["email"]
        password = request.form["password"]

        get_all_user_data = mongoOperation().get_spec_data_from_coll(client, "quickoo_uk", "login_mapping", {"email": email, "password": password})
        if get_all_user_data:
            if get_all_user_data[0]["is_active"]:
                response_data_msg = commonOperation().get_success_response(200, {"id": get_all_user_data[0]["id"], "email": email})
            else:
                response_data_msg = commonOperation().get_error_msg("Your account disabled.. Please contact administration")
        else:
            response_data_msg = commonOperation().get_error_msg("Enter correct credentials")

        return response_data_msg

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again..")
        print(f"{datetime.utcnow()}: Error in login user data route: {str(e)}")
        return response_data

@app.route("/quickoo_uk/otp-email-verification", methods=["POST"])
def quickoo_uk_user_otp_email_verification():
    try:
        otp = request.form["otp"]
        email = request.form["email"]
        get_all_user_data = mongoOperation().get_all_data_from_coll(client, "quickoo_uk", "user_data")
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


@app.route("/quickoo_uk/forgot-password", methods=["POST"])
def quickoo_uk_user_forgot_password():
    try:
        email = request.form["email"]
        otp = request.form["otp"]
        email_condition_dict = {"email": email}
        email_data = mongoOperation().get_spec_data_from_coll(client, "quickoo_uk", "user_data", email_condition_dict)
        if email_data:
            if email_data[0]["is_active"]:
                html_format = htmlOperation().otp_verification_process(otp)
                emailOperation().send_email(email, "Quickoo: Your Account Verification Code", html_format)
                return commonOperation().get_success_response(200, {"message": "Account Exits..", "id": email_data[0]["id"]})
            else:
                return commonOperation().get_error_msg("Your account was disabled, Contact administration")
        else:
            response_data = commonOperation().get_error_msg("Account not exits..")
        return response_data

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again...")
        print(f"{datetime.now()}: Error in forgot password route: {str(e)}")
        return response_data

@app.route("/quickoo_uk/change-password", methods=["POST"])
def quickoo_uk_change_password():
    try:
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        user_id = request.form.get("id")
        if password==confirm_password:
            mongoOperation().update_mongo_data(client, "quickoo_uk", "user_data", {"id":user_id}, {"password": password})
            mongoOperation().update_mongo_data(client, "quickoo_uk", "login_mapping", {"id":user_id}, {"password": password})
            return commonOperation().get_success_response(200, {"message": "Password updated"})
        else:
            return commonOperation().get_error_msg("Password doesn't match...")

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again...")
        print(f"{datetime.now()}: Error in change password route: {str(e)}")
        return response_data

@app.route("/quickoo_uk/get-user-data", methods=["POST"])
def quickoo_uk_get_user_data():
    try:
        user_id = request.form["id"]
        get_all_user_data = list(mongoOperation().get_spec_data_from_coll(client, "quickoo_uk", "user_data", {"id": user_id}))
        response_data = get_all_user_data[0]
        del response_data["_id"]
        del response_data["created_at"]
        del response_data["updated_at"]
        response_data_msg = commonOperation().get_success_response(200, response_data)
        return response_data_msg

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again..")
        print(f"{datetime.utcnow()}: Error in get user data route: {str(e)}")
        return response_data

@app.route("/quickoo_uk/update-user-data", methods=["POST"])
def quickoo_uk_update_user_data():
    try:
        name = request.form.get("name")
        email = request.form.get("email", "")
        phone_number = request.form.get("phone_number", "")
        user_id = request.form.get("id", "")

        if name:
            mongoOperation().update_mongo_data(client, "quickoo_uk", "user_data", {"id":user_id}, {"name": name})
            return commonOperation().get_success_response(200, {"message": "Name updated successfully..."})
        elif email:
            get_all_user_data = mongoOperation().get_all_data_from_coll(client, "quickoo_uk", "user_data")
            all_emails = [user_data["email"] for user_data in get_all_user_data]
            if email in all_emails:
                return commonOperation().get_error_msg("Email already registered...")
            mongoOperation().update_mongo_data(client, "quickoo_uk", "user_data", {"id":user_id}, {"email": email})
            mongoOperation().update_mongo_data(client, "quickoo_uk", "login_mapping", {"id":user_id}, {"email": email})
            return commonOperation().get_success_response(200, {"message": "Email updated successfully..."})
        elif phone_number:
            mongoOperation().update_mongo_data(client, "quickoo_uk", "user_data", {"id":user_id}, {"phone_number": phone_number, "is_phone": True})
            return commonOperation().get_success_response(200, {"message": "Phone number updated successfully..."})
        else:
            return commonOperation().get_error_msg("Something won't wrong!")

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again...")
        print(f"{datetime.now()}: Error in update user data route: {str(e)}")
        return response_data

@app.route("/quickoo_uk/request-ride", methods=["POST"])
def quickoo_uk_request_ride():
    try:
        user_id = request.form.get("id")
        from_location = request.form.get("from")
        to_location = request.form.get("to")
        start_date = request.form.get("start_date")
        start_time = request.form.get("start_time")
        vehicle_type = request.form.get("vehicle_type")
        if from_location.lower() == to_location.lower():
            response_data = commonOperation().get_error_msg("Pickup & Drop Point are same...")
        else:
            all_rides_data = list(mongoOperation().get_all_data_from_coll(client, "quickoo_uk", "rides_data"))
            all_rideids = [ride_data["ride_id"] for ride_data in all_rides_data]

            flag = True
            ride_id = ""
            while flag:
                ride_id = str(uuid.uuid4())
                if ride_id not in all_rideids:
                    flag = False

            mapping_dict = {
                "id": user_id,
                "ride_id": ride_id,
                "from_location": from_location,
                "to_location": to_location,
                "start_date": start_date,
                "start_time": start_time,
                "vehicle_type": vehicle_type,
                "driver_details": {},
                "is_driver": False,
                "is_completed": False,
                "created_on": datetime.utcnow()
            }

            mongoOperation().insert_data_from_coll(client, "quickoo_uk", "rides_data", mapping_dict)
            response_data = commonOperation().get_success_response(200, {"message": "Ride created successfully..."})

        return response_data
    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again...")
        print(f"{datetime.now()}: Error in create ride route: {str(e)}")
        return response_data

@app.route('/quickoo_uk/get-current-ride', methods=['POST'])
def quickoo_uk_get_current_ride():
    try:
        user_id = request.form.get("id", "")
        ride_data = list(mongoOperation().get_spec_data_from_coll(client, "quickoo_uk", "rides_data",{"is_completed": False, "id": user_id}))
        all_data = []
        for ride_d in ride_data:
            del ride_d["_id"]
            del ride_d["created_on"]
            all_data.append(ride_d)
        return commonOperation().get_success_response(200, all_data)

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again..")
        print(f"{datetime.utcnow()}: Error in get current active ride for user: {str(e)}")
        return response_data

@app.route('/quickoo_uk/get_past_rides', methods=['POST'])
def quickoo_uk_get_past_rides():
    try:
        user_id = request.form.get("id", "")
        ride_data = mongoOperation().get_spec_data_from_coll(client, "quickoo_uk", "rides_data", {"id": user_id, "is_completed": True})
        rides_data = []
        for ride in ride_data:
            del ride["_id"]
            del ride["created_on"]
            rides_data.append(ride)
        return commonOperation().get_success_response(200, rides_data)

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again..")
        print(f"{datetime.utcnow()}: Error in check get past rides for user: {str(e)}")
        return response_data

@app.route('/quickoo_uk/get_spec_past_ride', methods=['POST'])
def quickoo_uk_get_spec_past_ride():
    try:
        ride_id = request.form.get("ride_id", "")
        user_id = request.form.get("id", "")
        ride_data = list(mongoOperation().get_spec_data_from_coll(client, "quickoo_uk", "rides_data", {"ride_id": ride_id, "id": user_id}))
        ride_dict = ride_data[0]
        del ride_dict["_id"]
        del ride_dict["created_on"]
        return commonOperation().get_success_response(200, ride_dict)

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again..")
        print(f"{datetime.utcnow()}: Error in check get specific ride data for user: {str(e)}")
        return response_data

@app.route('/quickoo_uk/user-dashboard', methods=['POST'])
def quickoo_uk_api_user_dashboard():
    try:
        user_id = request.form.get("id", "")
        active_rides = []
        past_rides = []
        completed_ride = 0
        active_ride = 0
        ride_data = list(mongoOperation().get_spec_data_from_coll(client, "quickoo_uk", "rides_data", {"id": user_id}))[::-1]
        for ride in ride_data:
            del ride["_id"]
            del ride["created_on"]
            if ride["is_completed"]:
                completed_ride+=1
                if len(past_rides)!=3:
                    past_rides.append(ride)
            else:
                active_ride+=1
                if len(active_rides)!=3:
                    active_rides.append(ride)

        ride_dict = {
            "id": user_id,
            "total_ride": len(ride_data),
            "completed_ride": completed_ride,
            "active_ride": active_ride,
            "active_rides": active_rides,
            "past_rides": past_rides
        }

        return commonOperation().get_success_response(200, ride_dict)

    except Exception as e:
        response_data = commonOperation().get_error_msg("Please try again..")
        print(f"{datetime.utcnow()}: Error in check get dashboard data for user: {str(e)}")
        return response_data



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
