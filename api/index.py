from flask import Flask, request, jsonify
import requests
import binascii
import base64
import json
import random
import sys
import os

app = Flask(__name__)

# ---------- Constants ----------
FREEFIRE_VERSION = "OB54"
MAJOR_LOGIN_URL = "https://loginbp.ggpolarbear.com/MajorLogin"
OAUTH_URL = "https://100067.connect.garena.com/oauth/guest/token/grant"

KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

# ---------- Device Database ----------
DEVICES = [
    {"model": "SM-G998B", "android": "13", "api": "33", "cpu": "ARMv8 | 2800 | 8", "gpu": "Mali-G78", "res": ["1440", "1080"], "dpi": "480", "ram": "8192", "build": "TP1A.220624.014"},
    {"model": "realme C31", "android": "12", "api": "31", "cpu": "ARMv8 | 2000 | 8", "gpu": "Mali-G52", "res": ["720", "1600"], "dpi": "320", "ram": "4096", "build": "SQ3A.220705.003"},
    {"model": "Mi 11", "android": "12", "api": "32", "cpu": "ARMv8 | 2500 | 8", "gpu": "Adreno 650", "res": ["1080", "2400"], "dpi": "395", "ram": "6144", "build": "SQ3A.220705.003"},
    {"model": "OnePlus 9", "android": "13", "api": "33", "cpu": "ARMv8 | 2900 | 8", "gpu": "Adreno 660", "res": ["1080", "2400"], "dpi": "420", "ram": "8192", "build": "TP1A.220624.014"},
    {"model": "Pixel 6", "android": "13", "api": "33", "cpu": "ARMv8 | 2800 | 8", "gpu": "Mali-G78", "res": ["1080", "2400"], "dpi": "440", "ram": "8192", "build": "TP1A.220624.014"},
]

def get_random_device():
    device = random.choice(DEVICES)
    return {
        "model": device["model"],
        "android": device["android"],
        "api": device["api"],
        "cpu": device["cpu"],
        "gpu": device["gpu"],
        "width": device["res"][0],
        "height": device["res"][1],
        "dpi": device["dpi"],
        "ram": device["ram"],
        "build": device["build"]
    }

def encrypt_data(data_bytes):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    padded = pad(data_bytes, AES.block_size)
    return cipher.encrypt(padded)

def get_name_region_from_reward(access_token):
    try:
        url = "https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/"
        headers = {
            "accept": "application/json, text/plain, */*",
            "access-token": access_token,
            "user-agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, verify=False, timeout=15)
        data = resp.json()
        return data.get("uid"), data.get("name"), data.get("region")
    except:
        return None, None, None

def get_openid_from_shop2game(uid):
    if not uid: return None
    try:
        url = "https://topup.pk/api/auth/player_id_login"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36",
            "X-Requested-With": "mark.via.gp",
        }
        payload = {"app_id": 100067, "login_id": str(uid)}
        resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=15)
        return resp.json().get("open_id")
    except:
        return None

def perform_guest_login(uid, password):
    payload = {
        'uid': uid,
        'password': password,
        'response_type': "token",
        'client_type': "2",
        'client_secret': "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        'client_id': "100067"
    }
    headers = {
        'User-Agent': f"GarenaMSDK/4.0.19P9({random.choice(['SM-G998B','realme C31','Mi 11'])} ;Android 13;pt;BR;)",
        'Connection': "Keep-Alive"
    }
    try:
        resp = requests.post(OAUTH_URL, data=payload, headers=headers, timeout=15, verify=False)
        data = resp.json()
        if 'access_token' in data:
            return data['access_token'], data.get('open_id')
    except:
        pass
    return None, None

def perform_major_login(access_token, open_id):
    try:
        import my_pb2
        device = get_random_device()
        
        game_data = my_pb2.GameData()
        game_data.timestamp = "2025-01-15 10:30:45"
        game_data.game_name = "free fire"
        game_data.game_version = 1
        game_data.version_code = "1.121.0"
        game_data.os_info = f"Android OS {device['android']} / API-{device['api']} ({device['build']})"
        game_data.device_type = "Handheld"
        game_data.network_provider = "Verizon Wireless"
        game_data.connection_type = "WIFI"
        game_data.screen_width = int(device['width'])
        game_data.screen_height = int(device['height'])
        game_data.dpi = device['dpi']
        game_data.cpu_info = device['cpu']
        game_data.total_ram = int(device['ram'])
        game_data.gpu_name = device['gpu']
        game_data.gpu_version = "OpenGL ES 3.2"
        game_data.user_id = f"Google|{random.randint(1000000000000, 9999999999999)}"
        game_data.ip_address = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        game_data.language = "en"
        game_data.open_id = open_id
        game_data.access_token = access_token
        game_data.platform_type = 8
        game_data.field_99 = "8"
        game_data.field_100 = "8"
        game_data.device_form_factor = "Phone"
        game_data.device_model = device['model']

        serialized = game_data.SerializeToString()
        encrypted = encrypt_data(serialized)
        hex_encrypted = binascii.hexlify(encrypted).decode()
        edata = bytes.fromhex(hex_encrypted)
        
        headers = {
            "User-Agent": f"Dalvik/2.1.0 (Linux; U; Android {device['android']}; {device['model']})",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/octet-stream",
            "Expect": "100-continue",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": FREEFIRE_VERSION
        }
        
        resp = requests.post(MAJOR_LOGIN_URL, data=edata, headers=headers, verify=False, timeout=15)
        
        if resp.status_code == 200:
            try:
                import output_pb2
                msg = output_pb2.Garena_420()
                msg.ParseFromString(resp.content)
                for field in msg.DESCRIPTOR.fields:
                    if field.name == "token":
                        return getattr(msg, field.name)
            except:
                pass
    except Exception as e:
        print("MajorLogin error:", e)
    return None

def decode_jwt_info(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None, None, None
        payload_b64 = parts[1]
        payload_b64 += '=' * ((4 - len(payload_b64) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
        uid = payload.get("account_id")
        region = payload.get("lock_region")
        nickname = payload.get("nickname")
        return str(uid), nickname, region
    except:
        return None, None, None

# ---------- Routes ----------
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "api": "Profile Item API (OB54)",
        "credit": "SHAPPNO_CODEX",
        "status": "running on Vercel ✅"
    })

@app.route('/item', methods=['GET'])
def change_items():
    jwt_token = request.args.get('token') or request.args.get('jwt')
    uid = request.args.get('uid')
    password = request.args.get('pass')
    access_token = request.args.get('access')

    final_jwt = None
    login_method = "Direct JWT"
    final_uid = None
    final_name = None
    final_region = None

    try:
        if jwt_token:
            final_jwt = jwt_token
            j_uid, j_name, j_region = decode_jwt_info(jwt_token)
            final_uid = j_uid
            final_name = j_name
            final_region = j_region
            
        elif uid and password:
            login_method = "UID/Pass Login"
            acc_token, open_id = perform_guest_login(uid, password)
            if acc_token and open_id:
                final_jwt = perform_major_login(acc_token, open_id)
                if final_jwt:
                    j_uid, j_name, j_region = decode_jwt_info(final_jwt)
                    final_uid = j_uid
                    final_name = j_name
                    final_region = j_region
                else:
                    return jsonify({"status": "error", "message": "JWT Generation Failed"}), 500
            else:
                return jsonify({"status": "error", "message": "Guest Login Failed"}), 401

        elif access_token:
            login_method = "Access Token Login"
            f_uid, f_name, f_region = get_name_region_from_reward(access_token)
            final_uid = f_uid
            final_name = f_name
            final_region = f_region

            if not final_uid:
                return jsonify({"status": "error", "message": "Invalid Access Token"}), 400

            open_id = get_openid_from_shop2game(final_uid)
            if open_id:
                final_jwt = perform_major_login(access_token, open_id)
            else:
                return jsonify({"status": "error", "message": "OpenID Fetch Failed"}), 400
        
        else:
            return jsonify({"status": "error", "message": "Provide token, uid+pass, or access"}), 400

        if not final_jwt:
            return jsonify({"status": "error", "message": "JWT Generation Failed"}), 500

        # Build simple request
        url = "https://clientbp.ggpolarbear.com/SetPlayerGalleryShowInfo"
        headers = {
            "Authorization": f"Bearer {final_jwt}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": FREEFIRE_VERSION,
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; SM-G998B)",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # Simple test data
        data = "test=1"
        response = requests.post(url, headers=headers, data=data, timeout=20, verify=False)
        
        return jsonify({
            "status": "success",
            "login_method": login_method,
            "code": response.status_code,
            "uid": str(final_uid) if final_uid else None,
            "name": final_name,
            "region": final_region,
            "generated_jwt": final_jwt,
            "version": "OB54"
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== VERCEL HANDLER ==========
def handler(request, context):
    return app(request, context)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=False)