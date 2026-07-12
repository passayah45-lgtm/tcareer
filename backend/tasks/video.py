import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 30},
    name="tasks.video.trigger_transcoding",
)
def trigger_transcoding(self, s3_key: str, lesson_id: str, video_lesson_id: str = "") -> None:
    """
    Triggers AWS MediaConvert transcoding after a video upload completes.
    Stores the returned job ID on the VideoLesson for webhook correlation.
    """
    from apps.courses.models import VideoLesson, TranscodingStatus

    try:
        from services.aws.mediaconvert import submit_transcoding_job
        job_id = submit_transcoding_job(
            s3_key=s3_key,
            lesson_id=lesson_id,
            video_lesson_id=video_lesson_id,
        )
        if video_lesson_id:
            VideoLesson.objects.filter(id=video_lesson_id).update(
                mediaconvert_job_id=job_id,
                transcoding_status=TranscodingStatus.PROCESSING,
            )
        logger.info("Transcoding job %s submitted for lesson %s", job_id, lesson_id)
    except Exception as exc:
        logger.error("Transcoding submission failed for lesson %s: %s", lesson_id, exc)
        if video_lesson_id:
            VideoLesson.objects.filter(id=video_lesson_id).update(
                transcoding_status=TranscodingStatus.FAILED,
            )
        raise
