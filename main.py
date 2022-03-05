from google_drive import GoogleDriveAPI


if __name__ == "__main__":
    gda = GoogleDriveAPI()

    print(gda.token, gda.token_expiry)

    upload = gda.upload(file_name="login_page.jpeg",
                        folder_id="1CvGUAtXgNtc205t1i2d__hmr7FW4OXKgerURT2",
                        file_path="../google_auth/login_page.jpeg").json()
    # print(upload)

    list_files = gda.list_files(folder_id="1CvGUAtXgNtc205t1i2d__hmr7FW4OXKgerURT2").json()
    print(list_files)

    gda.file_id = upload["id"]
    change = gda.change_file_name(file_name="login_page.jpeg",
                                  folder_id="1CvGUAtXgNtc205t1i2d__hmr7FW4OXKgerURT2").json()
    print(change)

    # update = gda.update(file_name="login_page.jpeg",
    # folder_id="1CvGUAtXgNtc205t1i2d__hmr7FW4OXKgerURT2",
    # file_path="../google_auth/login_page.jpeg").json()
    # print(update.json())

    # for item in files.json().get("files"):
    # gda.file_id = item["id"]
    # print(gda.delete().text)

    download = gda.dowload(change["id"])
    # print(download)
