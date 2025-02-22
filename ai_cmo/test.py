import requests

def upload_ads_video(ad_account_id, video_path, access_token, title="", description=""):
    """Uploads a video to Meta's Marketing API."""
    url = f"https://graph.facebook.com/v19.0/act_{ad_account_id}/advideos"
    headers = {"Authorization": f"Bearer {access_token}"}
    print("invoking upload...")

    with open(video_path, "rb") as video_file:
        files = {"source": video_file}
        data = {"title": title, "description": description}
        res = requests.post(url, headers=headers, files=files, data=data)
        print(res.json())
    return res.json()

if __name__ == "__main__":
    AD_ACCOUNT_ID = "1139671647289993"
    ACCESS_TOKEN = "EAASO6K2Xl0MBO8ZBXxGF1Rq1ZCYwyiMQZBbwl7F5X6HvGZCq0H6cgvCOdF0QPbrD9fjlHR5TvH5cAAevfnXFzJ0BDhj2GIQEFOdyV6XFCZADz5zGFMGEyKH6EOZBa1Q3FmIrYsZCNEXQl87yYd6MjZBoDwAGLJJWwlMOSkac1X02hHmQq0znwhCcchR12N3nB02K"
    FILE_PATH = "./test_vid.mp4"

    response = upload_ads_video(AD_ACCOUNT_ID, FILE_PATH, ACCESS_TOKEN, "testing", "testing")
    print(response)