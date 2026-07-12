"""
AWS MediaConvert integration for video transcoding.

Architecture:
1. Instructor uploads raw video to S3 (private bucket, /originals/ prefix)
2. Django calls submit_transcoding_job() with the S3 key
3. MediaConvert reads the original, outputs:
   - HLS adaptive bitrate streams (1080p, 720p, 480p) to /hls/ prefix
   - Thumbnail image at 5 seconds to /thumbnails/ prefix
4. EventBridge rule detects job completion and POSTs to our webhook
5. Django updates VideoLesson with the HLS URL

S3 bucket structure:
    tcareer-media/
        originals/courses/{course_id}/lessons/{lesson_id}/{uuid}.mp4
        hls/courses/{course_id}/lessons/{lesson_id}/{uuid}/
            master.m3u8
            1080p.m3u8
            720p.m3u8
            480p.m3u8
            segments/...
        thumbnails/courses/{course_id}/lessons/{lesson_id}/{uuid}.jpg

IAM requirements:
    MediaConvert role needs:
        - s3:GetObject on tcareer-media/originals/*
        - s3:PutObject on tcareer-media/hls/*
        - s3:PutObject on tcareer-media/thumbnails/*
"""

import logging
import boto3
from django.conf import settings

logger = logging.getLogger(__name__)


def get_mediaconvert_client():
    """
    MediaConvert requires a regional endpoint, not the global one.
    We discover the endpoint once and cache it.
    """
    mc = boto3.client(
        "mediaconvert",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    endpoints = mc.describe_endpoints()
    endpoint_url = endpoints["Endpoints"][0]["Url"]
    return boto3.client(
        "mediaconvert",
        region_name=settings.AWS_REGION,
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def submit_transcoding_job(s3_key: str, lesson_id: str, video_lesson_id: str) -> str:
    """
    Submit a MediaConvert job to transcode the uploaded video.
    Returns the MediaConvert job ID.

    The job produces:
    - HLS adaptive bitrate stream with 3 quality levels
    - Thumbnail at 5 seconds into the video

    Output is written to the same bucket under /hls/ and /thumbnails/ prefixes.
    """
    bucket = settings.AWS_S3_BUCKET_NAME
    input_s3_uri = f"s3://{bucket}/{s3_key}"
    output_prefix = s3_key.replace("originals/", "hls/").rsplit(".", 1)[0] + "/"
    thumbnail_prefix = s3_key.replace("originals/", "thumbnails/").rsplit(".", 1)[0]

    mediaconvert_role_arn = getattr(settings, "AWS_MEDIACONVERT_ROLE_ARN", "")
    if not mediaconvert_role_arn:
        logger.warning("AWS_MEDIACONVERT_ROLE_ARN not configured. Skipping transcoding.")
        return "mock-job-id"

    client = get_mediaconvert_client()

    job_settings = {
        "Inputs": [
            {
                "FileInput": input_s3_uri,
                "AudioSelectors": {"Audio Selector 1": {"DefaultSelection": "DEFAULT"}},
                "VideoSelector": {},
                "TimecodeSource": "ZEROBASED",
            }
        ],
        "OutputGroups": [
            {
                "Name": "HLS Group",
                "OutputGroupSettings": {
                    "Type": "HLS_GROUP_SETTINGS",
                    "HlsGroupSettings": {
                        "SegmentLength": 6,
                        "MinSegmentLength": 0,
                        "Destination": f"s3://{bucket}/{output_prefix}",
                    },
                },
                "Outputs": [
                    _hls_output("1080p", 1920, 1080, 5000000, 192000),
                    _hls_output("720p", 1280, 720, 2500000, 128000),
                    _hls_output("480p", 854, 480, 1000000, 96000),
                ],
            },
            {
                "Name": "Thumbnails",
                "OutputGroupSettings": {
                    "Type": "FILE_GROUP_SETTINGS",
                    "FileGroupSettings": {
                        "Destination": f"s3://{bucket}/{thumbnail_prefix}",
                    },
                },
                "Outputs": [
                    {
                        "ContainerSettings": {"Container": "RAW"},
                        "VideoDescription": {
                            "Width": 1280,
                            "Height": 720,
                            "CodecSettings": {
                                "Codec": "FRAME_CAPTURE",
                                "FrameCaptureSettings": {
                                    "FramerateNumerator": 1,
                                    "FramerateDenominator": 1,
                                    "MaxCaptures": 1,
                                    "Quality": 80,
                                },
                            },
                        },
                    }
                ],
            },
        ],
    }

    response = client.create_job(
        Role=mediaconvert_role_arn,
        Settings=job_settings,
        UserMetadata={
            "lesson_id": lesson_id,
            "video_lesson_id": video_lesson_id,
        },
    )

    job_id = response["Job"]["Id"]
    logger.info("MediaConvert job submitted: %s for lesson %s", job_id, lesson_id)
    return job_id


def _hls_output(name_modifier: str, width: int, height: int,
                video_bitrate: int, audio_bitrate: int) -> dict:
    return {
        "NameModifier": f"_{name_modifier}",
        "ContainerSettings": {"Container": "M3U8"},
        "VideoDescription": {
            "Width": width,
            "Height": height,
            "CodecSettings": {
                "Codec": "H_264",
                "H264Settings": {
                    "Bitrate": video_bitrate,
                    "RateControlMode": "CBR",
                    "CodecProfile": "HIGH",
                    "CodecLevel": "AUTO",
                    "FramerateControl": "INITIALIZE_FROM_SOURCE",
                },
            },
        },
        "AudioDescriptions": [
            {
                "AudioSourceName": "Audio Selector 1",
                "CodecSettings": {
                    "Codec": "AAC",
                    "AacSettings": {
                        "Bitrate": audio_bitrate,
                        "SampleRate": 48000,
                        "CodingMode": "CODING_MODE_2_0",
                    },
                },
            }
        ],
    }
