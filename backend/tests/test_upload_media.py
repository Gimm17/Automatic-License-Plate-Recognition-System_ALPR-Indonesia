from routers.detection import classify_upload_media


def test_classify_upload_media_accepts_generic_mp4_by_extension():
    assert classify_upload_media("application/octet-stream", ".mp4") == (False, True)


def test_classify_upload_media_accepts_image_by_extension():
    assert classify_upload_media("", ".webp") == (True, False)


def test_classify_upload_media_rejects_unknown_type():
    assert classify_upload_media("application/octet-stream", ".zip") == (False, False)
