import os
import sys
import time
import json
import requests
import webbrowser
from datetime import datetime, timedelta

# Go for https://console.cloud.google.com/apis/library and generate your credentials
# Your app must be of the type TVs and Limited Input Devices
# View page https://developers.google.com/identity/gsi/web/guides/devices

BASE_URL = "https://www.googleapis.com"
OAUTH2_URL = "https://oauth2.googleapis.com"
DOWMLOAD_URL = "https://drive.google.com"
BASE_DIR = os.getcwd()


class Browser(object):

    def __init__(self):
        self.response = None
        self.headers = self.get_headers()
        self.session = requests.Session()

    def get_headers(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/87.0.4280.88 Safari/537.36"
        }
        return self.headers

    def send_request(self, method, url, **kwargs):
        self.response = self.session.request(method, url, **kwargs)
        return self.response


class GoogleDriveAPI(Browser):

    def __init__(self, file_secrets=None, credentials=None):
        super().__init__()
        self.client_id = None
        self.client_secret = None
        self.credentials = credentials
        self.file_secrets = file_secrets
        self.device_code = None
        self.token = None
        self.refresh_token = None
        self.folder_id = None
        self.file_id = None
        self.token_expiry = None
        self.authenticate()

    def authenticate(self):
        if self.check_secrets():
            self.load_secrets()

        if not os.path.exists(self.credentials):
            verify_device = self.verify_device_code().json()
            if verify_device.get("error"):
                print(f"CREDENCIAIS INVÁLIDAS OU NÃO FORAM ECONTRADAS: {verify_device['error']}")
                print(f"VERIFIQUE A EXISTÊNCIA DO ARQUIVO {self.file_secrets}")
                sys.exit()
            else:
                self.device_code = verify_device["device_code"]
                print("INSIRA O SEGUINTE CÓDIGO QUANDO SOLICITADO: ", verify_device["user_code"])
                time.sleep(7)
                webbrowser.open(verify_device["verification_url"])
                next_step = input("ENTER PARA CONTINUAR, N PARA SAIR: ")
                if next_step.upper() == "N":
                    sys.exit()
                data_token = self.get_token().json()
                self.token = data_token["access_token"]
                self.refresh_token = data_token["refresh_token"]
                if 'expires_in' in data_token:
                    delta = timedelta(seconds=int(data_token['expires_in']))
                    self.token_expiry = delta + datetime.now()
                else:
                    self.token_expiry = None
                with open(self.credentials, "w") as json_file:
                    data_token["token_expiry"] = self.token_expiry.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    json_file.write(json.dumps(data_token, indent=4))
        elif self.check_token_expired():
            self.refresh()
            # os.remove(os.path.join(BASE_DIR, "credentials.json"))
        self.expires_in()
        return True

    def check_secrets(self):
        if not os.path.exists(self.file_secrets):
            return False
        return True

    def load_secrets(self):
        with open(self.file_secrets, "r") as json_file:
            result = json.loads(json_file.read())
            self.client_id = result["installed"]["client_id"]
            self.client_secret = result["installed"]["client_secret"]

    def verify_device_code(self):
        data = {
            "client_id": self.client_id,
            "scope": f"{BASE_URL}/auth/drive.file"
        }
        return self.send_request(
            "POST",
            f"{OAUTH2_URL}/device/code",
            data=data,
            headers=self.headers
        )

    def get_token(self):
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "device_code": self.device_code,
            "token_uri": f"{OAUTH2_URL}/token",
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }

        return self.send_request(
            "POST",
            f"{BASE_URL}/oauth2/v4/token",
            data=data,
            headers=self.headers
        )

    def refresh(self):
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
        }
        response = self.send_request(
            "POST",
            f"{BASE_URL}/oauth2/v4/token",
            data=data,
            headers=self.headers
        ).json()

        self.token = response['access_token']
        if 'expires_in' in response:
            delta = timedelta(seconds=int(response['expires_in']))
            self.token_expiry = delta + datetime.now()
        else:
            self.token_expiry = None

        with open(self.credentials, "r+") as json_file:
            json_data = json.load(json_file)
            json_data["token_expiry"] = self.token_expiry.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            json_data["access_token"] = self.token
            json_file.seek(0)
            json.dump(json_data, json_file, indent=4)
            json_file.truncate()

        return False

    def check_token_expired(self):
        if os.path.exists(os.path.join(BASE_DIR, self.credentials)):
            with open(self.credentials, "r") as json_file:
                json_data = json.load(json_file)
                self.token = json_data['access_token']
                self.refresh_token = json_data['refresh_token']
                self.token_expiry = datetime.strptime(json_data["token_expiry"], "%Y-%m-%dT%H:%M:%S.%fZ")

        if not self.token_expiry:
            return False

        now = datetime.now()
        if now >= self.token_expiry:
            print(f'access_token is expired. Now: {now}, token_expiry: {self.token_expiry}')
            return True

        return False

    def expires_in(self):
        if self.token_expiry:
            now = datetime.now()
            if self.token_expiry > now:
                time_delta = self.token_expiry - now
                return time_delta.days * 86400 + time_delta.seconds
            else:
                return 0

    def list_files(self):
        params = {
            "parents": [self.folder_id],
            "fields": "*",
            "trashed": False
        }
        self.headers["Authorization"] = f"Bearer {self.token}"
        return self.send_request(
            "GET",
            f"{BASE_URL}/drive/v3/files",
            params=params,
            headers=self.headers
        )

    def create_folder(self, folder_name="PyDrive", parent_id=None):
        if not self.verify_folder(folder_name):
            metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                metadata["parents"] = [parent_id]

            files = {
                "data": ("metadata", json.dumps(metadata), "application/json")
            }
            self.headers["Authorization"] = f"Bearer {self.token}"
            return self.send_request(
                "POST",
                f"{BASE_URL}/upload/drive/v3/files",
                files=files,
                headers=self.headers
            ).json()

        return self.verify_folder(folder_name)

    def verify_folder(self, root_folder="PyDrive"):
        folder_name = root_folder
        for folder in self.list_folders().json().get("files"):
            if folder.get("name") == folder_name:
                return json.loads(json.dumps(folder))
        return False

    def list_folders(self, parent_id=None):
        params = {
            "mimeType": 'application/vnd.google-apps.folder',
            "fields": "*",
            "trashed": False
        }
        if parent_id:
            params["parents"] = parent_id
        self.headers["Authorization"] = f"Bearer {self.token}"
        return self.send_request(
            "GET",
            f"{BASE_URL}/drive/v3/files",
            params=params,
            headers=self.headers
        )

    def overwrite(self, filename):
        file_list = self.list_files().json()
        if not file_list["files"] == []:
            try:
                for file in file_list["files"]:
                    if file['name'] == filename:
                        return file
            except ValueError:
                return False
        else:
            return False

    def upload(self, file_name, file_path):
        existance_file = self.overwrite(file_name)

        if existance_file:
            self.file_id = existance_file.get("id")
            self.delete()

        metadata = {
            "name": file_name,
            "fields": "*",
            "parents": [self.folder_id]
        }

        files = {
            "data": ("metadata", json.dumps(metadata), "application/json"),
            "file": open(file_path, "rb").read()
        }

        self.headers["Authorization"] = f"Bearer {self.token}"
        return self.send_request(
            "POST",
            f"{BASE_URL}/upload/drive/v3/files?uploadType=multipart",
            files=files,
            headers=self.headers
        )

    def update(self, file_name, file_path):
        metadata = {
            "name": file_name,
            "id": self.file_id,
            "parents": [self.folder_id]
        }

        files = {
            "data": ("metadata", json.dumps(metadata), "application/json"),
            "file": open(file_path, "rb").read()
        }

        self.headers["Authorization"] = f"Bearer {self.token}"
        return self.send_request(
            "PATCH",
            f"{BASE_URL}/upload/drive/v3/files/{self.file_id}",
            files=files,
            headers=self.headers
        )

    def delete(self):
        data = {
            "parents": [self.folder_id]
        }
        self.headers["Authorization"] = f"Bearer {self.token}"
        return self.send_request(
            "DELETE",
            f"{BASE_URL}/drive/v3/files/{self.file_id}",
            data=data,
            headers=self.headers
        )

    def change_file_name(self, file_name):
        metadata = {
            "parents": [self.folder_id]
        }

        files = {
            "data": ("metadata", json.dumps(metadata), "application/json"),
            "name": f"new_{file_name}"
        }

        self.headers["Authorization"] = f"Bearer {self.token}"
        return self.send_request(
            "PATCH",
            f"{BASE_URL}/drive/v3/files/{self.file_id}",
            json=files,
            headers=self.headers
        )

    def add_permissions(self, file_id):
        permissions = {
            "role": "writer",
            "type": "anyone",
            "fields": "*"
        }

        self.headers["Authorization"] = f"Bearer {self.token}"
        return self.send_request(
            "POST",
            f"{BASE_URL}/drive/v3/files/{file_id}/permissions",
            json=permissions,
            headers=self.headers
        )

    def dowload(self, file_id):
        params = {
            "id": file_id,
            "export": "download"
        }
        response = self.send_request("GET", f"{DOWMLOAD_URL}/uc", params=params, stream=True)
        file_name = response.headers.get("Content-Disposition").split("''")[1].replace('"', '')
        with open(os.path.join(f"{BASE_DIR}", file_name), 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        return file_name
