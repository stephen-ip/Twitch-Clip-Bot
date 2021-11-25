# Twitch-Clip-Bot
A bot that automatically uploads the top Twitch clips to its Youtube Channel. In its earlier version, it had found clips by going through top streamers, and uploaded their top clips within a small time period if it met a certain view count, but due to the large quantitative difference between different streamers' metrics, many random clips were uploaded in the process. The YouTube API quota limit is also too small relative to this project, so only the best clips should be uploaded. This is why the bot now just scrapes the top clips from the LivestreamFail (LSF) subreddit since clips here are voted popular by a large group of users, and account for the diverse population of streamers on Twitch. Now, every clip uploaded by the bot is good, but it is still limted by its quota limit as it can only upload about 4 videos per day, which can be changed if I file an application for Youtube to raise my daily quota limit. This project was inspired by the mass amounts of Youtube channels that have thousands of subscribers/views and all they do is just download top clips from twitch and upload it to their channel.


Technology Used: Python, Twitch API, Reddit API (PRAW), Youtube API, youtube-dl, Google Compute Engine (VM Instance)

Link to Channel:
https://www.youtube.com/channel/UCi5yUb5-6umox6uICceMaVA