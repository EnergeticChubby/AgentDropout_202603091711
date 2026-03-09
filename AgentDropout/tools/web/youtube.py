#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytube import YouTube
from AgentDropout.utils.const import AgentPrune_ROOT

def Youtube(url, has_subtitles):
    # get video id from url
    video_id=url.split('v=')[-1].split('&')[0]
    # Create a YouTube object
    youtube = YouTube(url)
    # Get the best available video stream
    video_stream = youtube.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    if has_subtitles:
        # Download the video to a location
        print('Downloading video')
        output_dir = AgentPrune_ROOT / "workspace"
        output_dir.mkdir(parents=True, exist_ok=True)
        video_stream.download(output_path=str(output_dir), filename=f"{video_id}.mp4")
        print('Video downloaded successfully')
        return str(output_dir / f"{video_id}.mp4")
    else:
        return video_stream.url 