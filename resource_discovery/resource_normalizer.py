def normalize_whitespace(value):
    if value is None:
        return None

    return " ".join(value.split())

def create_resource(
        title,
        url,
        source=None,
        creator=None,
        resource_format=None,
        resource_type=None,
        duration_seconds=None,
        description=None,
        views=None,
        likes=None,
        upload_date=None,
        pricing_model=None,
):
    return {
        "title": normalize_whitespace(title),
        "url": url,
        "source": source,
        "creator": normalize_whitespace(creator),
        "resource_format": resource_format,
        "resource_type": resource_type,
        "description": normalize_whitespace(description),
        "duration_seconds": duration_seconds,
        "views": views,
        "likes": likes,
        "upload_date": upload_date,
        "pricing_model": pricing_model,
    }
