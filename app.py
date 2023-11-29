from flask import Flask, render_template
from google.cloud import videointelligence_v1p3beta1 as videointelligence
import pysrt
import os
import moviepy
import ffmpeg
import subprocess

app = Flask(__name__)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "impaired-0dfab39375b5.json"

@app.route('/')
def index():
    return render_template('videoIndex.html')

@app.route('/subtitles')
def subtitles():
    # Instantiates a client
    client = videointelligence.VideoIntelligenceServiceClient()

    # The GCS path of the video to analyze
    video_path = "gs://dhyan/youtube.mp4"

    # Set the features to extract from the video
    features = [videointelligence.Feature.SPEECH_TRANSCRIPTION]

    # Configure the video request
    video_context = videointelligence.VideoContext(
        speech_transcription_config=videointelligence.SpeechTranscriptionConfig(
            language_code="en-US",
            enable_automatic_punctuation=True
        )
    )
    config = videointelligence.AnnotateVideoRequest(
        input_uri=video_path,
        features=features,
        video_context=video_context
    )

    # Perform the video analysis
    operation = client.annotate_video(request=config)
    result = operation.result(timeout=100000)

    # Extract the video transcription from the result
    transcript = ""
    for speech_transcription in result.annotation_results[0].speech_transcriptions:
        for alternative in speech_transcription.alternatives:
            transcript += " " + alternative.transcript

    # Generate an SRT file from the transcript
    srt = pysrt.SubRipFile()
    for i, line in enumerate(transcript.strip().split(".")):
        start = pysrt.SubRipTime(0, 0, i * 3)
        end = pysrt.SubRipTime(0, 0, (i + 1) * 3)
        srt.append(pysrt.SubRipItem(i + 1, start=start, end=end, text=line))
    srt_path = "my-subtitles.srt"
    srt.save(srt_path)

    # Burn the subtitles into the video using ffmpeg

    # Run ffmpeg command to burn subtitles into the video
    input_file = "youtube.mp4"

    # the subtitle file
    subtitle_file = "my-subtitles.srt"

    # the output video file
    output_file = "output.mp4"

    # the font file to be used for the subtitles
    font_file = "OpenSans-Regular.ttf"

    # run the ffmpeg command to burn the subtitles into the video
    subprocess.call([
        "ffmpeg",
        "-i", input_file,
        "-vf", f"subtitles={subtitle_file}:force_style='FontName={font_file}'",
        output_file
    ])

    return "Subtitles generated successfully!"

if __name__ == '__main__':
    app.run()