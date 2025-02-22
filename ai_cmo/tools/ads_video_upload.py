import requests
import urllib.request
import argparse

def upload_ads_video(ad_account_id, video_path, access_token, title="", description=""):
    """Uploads a video to Meta's Marketing API."""
    url = f"https://graph.facebook.com/v20.0/act_{ad_account_id}/advideos"
    headers = {"Authorization": f"Bearer {access_token}"}
    print("Invoking video upload...")
    with open(video_path, "rb") as video_file:
        files = {"source": video_file}
        data = {"title": title, "description": description}
        res = requests.post(url, headers=headers, files=files, data=data)
    return res.json()['id']

def download_file(remote_url, file_name):
    """Downloads a file from a remote repository and stores it in a local directory."""
    save_path = file_name
    print("Downloading file...")
    try:
        urllib.request.urlretrieve(remote_url, save_path)
        print("File download successful!")
    except Exception as e:
        print(f"Download failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload a video to a Meta Ad Account.")
    parser.add_argument("--ad_account_id", required=True, help="The Ad Account ID (numbers only).")
    parser.add_argument("--access_token", required=True, help="The access token for Meta's Graph API.")
    parser.add_argument("--remote_file_path", required=True, help="Remote URL of the video file to download.")
    parser.add_argument("--file_name", required=True, help="Name to save the downloaded file as.")
    parser.add_argument("--title", default="testing3", help="Title for the uploaded video.")
    parser.add_argument("--description", default="testing3", help="Description for the uploaded video.")

    args = parser.parse_args()

    local_file_path = f"./{args.file_name}"

    print(f"Downloading video from: {args.remote_file_path}")
    download_file(args.remote_file_path, local_file_path)

    vid_id = upload_ads_video(
        args.ad_account_id,
        local_file_path,
        args.access_token,
        title=args.title,
        description=args.description
    )
    if vid_id:
        print(f"Video uploaded successfully! Video ID: {vid_id}")
    else:
        print("Video upload failed.")