from gdrive.api import GoogleDriveAPI

if __name__ == "__main__":
    gda = GoogleDriveAPI()

    # folders = gda.list_folders().json()
    # print(folders)

    # print(gda.token, gda.token_expiry)

    folder_id = gda.create_folder(folder_name="TEST")["id"]
    # print(folder_id)

    gda.folder_id = folder_id

    upload = gda.upload(file_name="login_page.jpeg",
                        file_path="login_page.jpeg").json()
    print(upload)

    # list_files = gda.list_files().json()
    # print(list_files)

    # gda.file_id = upload["id"]

    # change = gda.change_file_name(file_name="login_page.jpeg").json()
    # print(change)

    # update = gda.update(file_name="login_page.jpeg",
    # file_path="login_page.jpeg").json()
    # print(update)

    # for item in files.json().get("files"):
    # gda.file_id = item["id"]
    # print(gda.delete().text)

    # download = gda.dowload(change["id"])
    # print(download)
