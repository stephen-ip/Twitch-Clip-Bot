from googleapiclient.http import MediaFileUpload
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl  # pip3 install --upgrade youtube_dl
import os
import requests  # pip3 install --upgrade requests
import pickle
import ast
import time
from datetime import datetime, timedelta  # pip3 install --upgrade datetime
from pyrfc3339 import generate  # pip3 install --upgrade pyrfc3339
import pytz  # pip3 install --upgrade pytz
import sys
# pip3 install --upgrade google-api-python-client
# pip3 install --upgrade google-auth-oauthlib google-auth-httplib2
import praw  # pip3 install --upgrade praw
import apiclient  # pip3 install --upgrade apiclient
import http.client
import httplib2  # pip3 install --upgrade httplib2
import random  # pip3 install --upgrade random
import urllib.request


class TwitchClipBot:

    def __init__(self):
        # TWITCH CREDENTIALS
        self.twitch_client_id = "REDACTED"  # static
        self.twitch_client_secret = "REDACTED"  # static
        try:  # try to find previous save of dictionary containing twitch access and refresh tokens
            with open('twitch_tokens.txt', 'r') as f:
                twitch_tokens = ast.literal_eval(f.read())
        except Exception:  # if there is no previous save, use original tokens (may be invalid)
            twitch_tokens = {"access_token": "REDACTED",
                             "refresh_token": "REDACTED"}
        self.twitch_access_token = twitch_tokens["access_token"]
        self.twitch_refresh_token = twitch_tokens["refresh_token"]
        self.twitch_broadcaster_ids = {"loltyler1": "51496027",  # add GreekGodx, JinnyTTV, Ninja, Asmongoldm moistcritikal, summit1g?
                                       "xqcow": "71092938",
                                       "mizkif": "94753024",
                                       "shroud": "37402112",
                                       "riotgames": "36029255",
                                       "souljaboy": "47694770",
                                       "pokimane": "44445592"}
        self.twitch_game_ids = {"21779": "League of Legends"}  # might implement game tag later

        # YOUTUBE / GOOGLE CREDENTIALS
        self.scopes = ["https://www.googleapis.com/auth/youtube"]  # scope to manage youtube account (do almost everything)
        self.client_secrets_file = "client_secret_REDACTED.apps.googleusercontent.com.json"

        # PROGRESS TRACKER AND TEMP VARS
        try:  # dictionary of all uploaded clips: clip urls as keys and name as values
            with open('uploaded_clips.txt', 'r') as f:  # see if there is a saved version of the uploaded_clips dict
                self.uploaded_clips = ast.literal_eval(f.read())  # interpret the saved string as a dictionary
        except Exception:  # if there is an error or no saved version of the songs_dict:
            self.uploaded_clips = dict()  # just create an empty dict if no previous save was found
        self.clip_title = ""  # reset at each new iteration
        self.clip_streamer = ""  # reset at each new iteration
        self.clip_url = ""  # reset at each new iteration

    def find_and_upload_clip_from_twitch(self):  # function that checks each streamer's channel for suitable clips and uploads it if there are
        self.refresh_twitch_api()  # refresh twitch api credentials before using it
        for streamer in self.twitch_broadcaster_ids.keys():  # iterate through list of streamers to search for clips
            if self.find_twitch_clip(streamer):  # if a clip that meet the requirements is found...
                if self.download_twitch_clip():  # then download the clip, and upload it
                    self.upload_to_youtube()  # and upload it
                    time.sleep(900)

    def find_twitch_clip(self, streamer):  # Use twitch API to find top clips from a streamer in the past 24 hrs (method can be changed)
        try:
            broadcaster_id = self.twitch_broadcaster_ids[streamer]
            yesterday_rfc3999 = generate((datetime.now() - timedelta(1)).replace(tzinfo=pytz.utc))
            query = f"https://api.twitch.tv/helix/clips?broadcaster_id={broadcaster_id}&started_at={yesterday_rfc3999}&first=1"  # choose streamer with broadcaster_id, and it will find top clips in the past 24hrs
            response = requests.get(query, headers={"Client-ID": f"{self.twitch_client_id}",
                                                    "Authorization": f"Bearer {self.twitch_access_token}"})
            if response.status_code == 200:
                response_json = response.json()
                if not response_json["data"]:  # if no data on search, that means no clips were found in the past 24hrs
                    # print("could not find any clips in the past 24 hrs from:", streamer)
                    # print()
                    return False  # if no clip was found then go to next iteration
                else:
                    clip_info = response_json["data"][0]
                if clip_info["url"] in self.uploaded_clips:  # check if url is already uploaded
                    # print(clip_info["title"], "from", clip_info["broadcaster_name"], "is already uploaded")
                    # print()
                    return False  # if the clip that was found was already uploaded then go to next iteration
                elif clip_info["view_count"] < 5000:  # implement a check for the view count to see if it is good
                    return False
                else:  # clip is new and popular (suitable for upload)
                    self.clip_title = clip_info["title"]
                    self.clip_streamer = clip_info["broadcaster_name"]
                    self.clip_url = clip_info["url"]
                    print(self.clip_title)
                    print(self.clip_streamer)
                    print(self.clip_url)
                    sys.stdout.flush()
                    return True
            else:
                # print("Error searching for clips: response code != 200")
                # print()
                return False
        except Exception:
            # print("Error using Twitch API to search for clips")
            # print()
            return False

    def find_and_upload_clip_from_lsf(self):  # use reddit API PRAW to find top submissions in the lsf subreddit
        reddit = praw.Reddit(
            client_id="REDACTED",  # personal use script
            client_secret="REDACTED",  # client secret
            user_agent="Twitch Clip Bot",  # can be anything. used by reddit to identify who is requesting
        )
        try:
            for submission in reddit.subreddit("LivestreamFail").hot(limit=10):
                if not submission.stickied:  # do not look at pinned posts
                    if "https://clips.twitch.tv/" in submission.url:  # check if submission is a twitch clip
                        if submission.url not in self.uploaded_clips:  # make sure clip is not uploaded already
                            self.clip_title = submission.title
                            self.clip_url = submission.url
                            tag = submission.link_flair_text
                            if tag:  # if there is a tag
                                if ":twitch: " in tag:  # format twitch flair to get tag
                                    self.clip_streamer = tag.replace(":twitch: ", "")
                                else:
                                    self.clip_streamer = "LSF"
                            else:
                                self.clip_streamer = "LSF"
                            print(self.clip_title)
                            print(self.clip_streamer)
                            print(self.clip_url)
                            sys.stdout.flush()
                            if self.download_twitch_clip():  # if download is success, upload to youtube
                                self.upload_to_youtube()
                                time.sleep(900)
                            elif self.download_twitch_clip_alternate():
                                self.upload_to_youtube()
                                time.sleep(900)
        except Exception:
            print("Error has occurred during LSF function")
            sys.stdout.flush()
            return False

    def download_twitch_clip(self):  # use youtube-dl to download the recently found twitch clip stored in class vars
        try:
            ydl_opts = {  # options for downloading clip
                'format': 'best',  # best quality
                'outtmpl': "twitch_clip.mp4",  # downloaded clip file name
                'quiet': True  # don't print downloading message
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.clip_url])
            return True
        except Exception:
            print("Error downloading twitch clip")
            print()
            sys.stdout.flush()
            return False

    def download_twitch_clip_alternate(self):  # used when yt-dl was down for a bit
        try:
            url = self.clip_url
            slug = url.rpartition('/')[-1]
            self.refresh_twitch_api()
            clip_info = requests.get("https://api.twitch.tv/helix/clips?id=" + slug, headers={"Client-ID": f"{self.twitch_client_id}",
                                                                                              "Authorization": f"Bearer {self.twitch_access_token}"}).json()
            thumb_url = clip_info['data'][0]['thumbnail_url']
            mp4_url = thumb_url.split("-preview", 1)[0] + ".mp4"
            urllib.request.urlretrieve(mp4_url, "twitch_clip.mp4")
            print("Downloaded clip using alternate method")
            return True
        except Exception:
            print("Error downloading twitch clip")
            print()
            sys.stdout.flush()
            return False

    def upload_to_youtube(self):
        # Get credentials and create an API client
        try:
            credentials = None
            if os.path.exists("token.pickle"):  # check if a save of token credentials in saved
                with open("token.pickle", "rb") as token:
                    credentials = pickle.load(token)  # retrieve last save of tokens
            if not credentials or not credentials.valid:  # check if tokens were retrieved or valid
                if credentials and credentials.expired and credentials.refresh_token:  # if tokens are not valid, refresh it with the refresh token
                    credentials.refresh(Request())
                else:  # if no refresh token, and tokens are not valid, then we need to manually authorize it
                    print("NEED MANUAL AUTHENTICATION FOR YOUTUBE CREDENTIALS")
                    sys.stdout.flush()  # end the function here since there is no point building with no credentials
                    os.remove("twitch_clip.mp4")  # remove downloaded clip
                    return None
                try:  # save updated credentials to token.pickle file
                    with open("token.pickle", "wb") as f:
                        pickle.dump(credentials, f)
                except Exception:
                    print("failed to update token.pickle")
                    sys.stdout.flush()
        except Exception:
            print("Unknown Error has occurred getting Youtube credentials")
            sys.stdout.flush()  # end the function here since there is no point building with no credentials
            os.remove("twitch_clip.mp4")  # remove downloaded clip
            return None

        # build youtube client object using credentials we just got
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)  # api_service = youtube, api_version = v3

        # format request body to upload video (metadata)
        request_body = {  # video information
            "snippet": {
                "title": self.clip_title,
                "description": f"clip from {self.clip_streamer}: {self.clip_url}",  # change when finished
                "tags": ["live",
                         "live stream fails",
                         "twitch",
                         "twitch highlight",
                         "funny",
                         "trainwrecks",
                         "summit1g",
                         "tfue",
                         "minecraft",
                         "shroud",
                         "xqc",
                         "clips",
                         "pokimane",
                         "tyler1",
                         "mizkif",
                         "trend",
                         "viral",
                         "sodapoppin",
                         "ninja",
                         "forsen",
                         "react",
                         "response",
                         "drama",
                         "leak",
                         "exposed",
                         "league of legends",
                         "new",
                         "pewdiepie",
                         "mrbeast",
                         "OTV",
                         "otk"]
            },
            "status": {
                "privacyStatus": "public"
            }
        }

        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=MediaFileUpload("twitch_clip.mp4", chunksize=-1, resumable=True)  # chunksize: -1 to upload in one request. Enable resumable to make more stable
        )
        try:
            self.resumable_upload(request)  # send insert request into function that will handle the upload
            print(datetime.now().strftime("%m/%d/%Y %I:%M %p"))  # print the time the request was executed
            print()
            sys.stdout.flush()
            os.remove("twitch_clip.mp4")  # remove downloaded clip after upload attempt was made
        except apiclient.errors.HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred:{e.content}")
            print(datetime.now().strftime("%m/%d/%Y %I:%M %p"))  # print the time the request was executed
            print()
            sys.stdout.flush()
            os.remove("twitch_clip.mp4")  # remove downloaded clip after upload attempt was made
            return False

    def resumable_upload(self, insert_request):
        httplib2.RETRIES = 1  # Explicitly tell the underlying HTTP transport library not to retry, since we are handling retry logic ourselves.
        MAX_RETRIES = 10  # max number of retries before quitting
        RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
                                http.client.IncompleteRead, http.client.ImproperConnectionState,
                                http.client.CannotSendRequest, http.client.CannotSendHeader,
                                http.client.ResponseNotReady, http.client.BadStatusLine)
        RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                # uploading file
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        print(f"Video id '{response['id']}' was successfully uploaded.")
                        self.uploaded_clips[self.clip_url] = self.clip_title  # keep track of uploading clips to avoid duplicates
                        try:  # save new iteration of songs_dict to backup
                            with open('uploaded_clips.txt', 'w') as f:
                                f.write(str(self.uploaded_clips))
                        except Exception:  # if it fails, just update it next iteration
                            print("failed to update uploaded_clips.txt")
                        print(f"Uploaded: {self.clip_title} from {self.clip_streamer}, url = {self.clip_url}")
                    else:
                        print(f"The upload failed with an unexpected response: {response}")
                        return False
            except apiclient.errors.HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = f"A retriable HTTP error {e.resp.status} occurred:{e.content}"
                elif e.resp.status == 403:  # 403 means quota is exceeded
                    print("The request cannot be completed because you have exceeded your quota.")
                    return False
                else:
                    print(f"An unretriable HTTP error {e.resp.status} occurred. Quiting...")
                    return False
            except RETRIABLE_EXCEPTIONS as e:
                error = f"A retriable error occurred: {e}"

            if error is not None:
                print(error)
                retry += 1
                if retry > MAX_RETRIES:
                    print("No longer attempting to retry.")
                    return False

                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                print(f"Sleeping {sleep_seconds} seconds and then retrying...")
                sys.stdout.flush()
                time.sleep(sleep_seconds)

    def refresh_twitch_api(self):  # refresh access and refresh tokens. refresh tokens also can change in this api
        query = f"https://id.twitch.tv/oauth2/token?grant_type=refresh_token&refresh_token={self.twitch_refresh_token}&client_id={self.twitch_client_id}&client_secret={self.twitch_client_secret}"
        response = requests.post(query)
        if response.status_code == 200:
            response_json = response.json()
            self.twitch_access_token = response_json["access_token"]
            self.twitch_refresh_token = response_json["refresh_token"]
            twitch_tokens = {"access_token": self.twitch_access_token,
                             "refresh_token": self.twitch_refresh_token}
            try:
                with open('twitch_tokens.txt', 'w') as f:  # save updated twitch tokens to backup
                    f.write(str(twitch_tokens))
            except Exception:  # if it fails, just update it next iteration
                pass
            return True
        else:
            print("error refreshing twitch tokens")
            print()
            return False


TCB = TwitchClipBot()
while True:
    TCB.find_and_upload_clip_from_lsf()  # first look for LSF clips
    sys.stdout.flush()
    time.sleep(1800)  # 30 min wait before each iteration

