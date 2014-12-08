import json
import uuid
from datetime import datetime
from django.contrib.auth.models import User
from database import models

#HDFS_PATH = 'http://155.69.146.44/content/files/'
# for deployment
HDFS_VIDEO_PATH = 'http://155.69.148.210/content/files/'
HDFS_IMG_PATH   = 'http://155.69.146.44/content/files/'
SHARED_CONTENT_URL = 'http://155.69.146.44/migration/contents/'
# for develop
# HDFS_VIDEO_PATH = 'http://155.69.148.208:8080/content/files/'
# HDFS_IMG_PATH   = 'http://155.69.148.208/content/files/'
# SHARED_CONTENT_URL = 'http://155.69.148.208/migration/contents/'
class Convertor:

    @staticmethod
    def get_duration(probe_str):
        if len(probe_str) < 1:
            return -1
        try:
            data = json.loads(probe_str)
            format_str = data.get("format")
            duration = None
            if format_str is not None:
                duration = format_str.get("duration")
                try:
                    return float(duration)
                except:
                    pass
            for stream in data.get("streams"):
                duration = stream.get("duration")
                try:
                    return float(duration)
                except:
                    pass
        except:
            pass
        return -1

    @classmethod
    def __build_img_url(cls, name, ext):
        return HDFS_IMG_PATH + name + "." + ext

    @classmethod
    def __build_video_url(cls, name, ext):
        return HDFS_VIDEO_PATH + name + "." + ext

    @classmethod
    def __build_thumbnail(cls, id):
        return cls.__build_img_url(id + "-thumb", "jpg")

    @classmethod
    def __build_shared_url(cls, prefix, name, ext):
        return SHARED_CONTENT_URL + prefix + '/'+ name + "." + ext

    @classmethod
    def __build_shared_thumbnail(cls, prefix, id):
        return cls.__build_shared_url(prefix, id + "-thumb", "jpg")

    @classmethod
    def __video_status(cls, value):
        status = "unknown"
        if (value == 1):
            status = "ready"
        elif (value == 2):
            status = "transcoding"
        elif (value == 3):
            status = "corrupted"
        elif (value == 4):
            status = "deleted"
        return status

    @classmethod
    def __rating(cls, total, count):
        if count == 0:
            return -1
        return total * 1.0 / count

    @classmethod
    def __tags(cls, tags):
        result = []
        for tag in tags:
            result.append(tag.name)
        return result

    @classmethod
    def gen_uuid(cls):
        return uuid.uuid1().hex

    @classmethod
    def get_range(cls, obj):
        return (obj["startIndex"], obj["maxCount"])

    @classmethod
    def get_shared_type_value(cls, type_str):
        if type_str == 'image':
            return models.SHARED_MEDIA_TYPE_IMAGE
        if type_str == 'clip':
            return models.SHARED_MEDIA_TYPE_CLIP
        return 0

    @classmethod
    def basic_video_object(cls, obj):
        return {
            "type":      "video",
            "uuid":      obj.id,
            "title":     obj.title,
            "length":    cls.get_duration(obj.video_info),
            "category":  cls.category_object(obj.category),
            "length":    cls.get_duration(obj.video_info),
            "thumbnail": cls.__build_thumbnail(obj.id),
            "score":     cls.__rating(obj.rating_total, obj.rating_count),
            "status":    cls.__video_status(obj.status)
        }

    @classmethod
    def user_object(cls, obj):
        if obj is not None:
            return {
                "type":      "user",
                "uuid":      obj.id,
                "name":      obj.get_full_name()
            }
        return {
            "type":      "user",
            "uuid":      None,
            "name":      "OTT Crawler"
        }

    @classmethod
    def ott_source_object(cls, obj):
        return {
            "type":      "source-ott",
            "uuid":      obj.id,
            "name":      obj.name,
            "link":      obj.link,
            "icon":      obj.icon
        }

    @classmethod
    def category_object(cls, obj):
        return {
            "type":      "video-category",
            "uuid":      obj.id,
            "name":      obj.name
        }

    @classmethod
    def ott_video_object(cls, basic, ott):
        result = cls.basic_video_object(basic)
        result["type"] = "video-ott"
        result["source"] = cls.ott_source_object(ott.ottsource)
        result["originalLink"] = ott.original_link
        return result

    @classmethod
    def shared_object(cls, obj):
        shared_type = "shared-unknown"
        shared_ext  = "mp4"
        shared_prefix = "unknown"
        if (obj.type == 1):
            shared_type   = "shared-image"
            shared_ext    = "jpg"
            shared_prefix = "image"
        elif (obj.type == 2):
            shared_type   = "shared-clip"
            shared_ext    = "mp4"
            shared_prefix = "video"
        return {
            "type":      shared_type,
            "uuid":      obj.id,
            "title":     obj.title,
            "create_time": datetime.strftime(obj.creation_time, "%Y-%m-%d %H:%M"),
            "url":       cls.__build_shared_url(shared_prefix, obj.id, shared_ext),
            "sender":    cls.user_object(obj.sender),
            "thumbnail": cls.__build_shared_thumbnail(shared_prefix, obj.id)
        }

    @classmethod
    def detailed_object(cls, obj, tags, rating = -1, ott = None):
        result = {
            "type":      "video-detail",
            "uuid":      obj.id,
            "title":     obj.title,
            "url":       cls.__build_video_url(obj.id, "mp4"),
            "length":    cls.get_duration(obj.video_info),
            "category":  cls.category_object(obj.category),
            "watch_count":obj.watch_count,
            "tags":      cls.__tags(tags),
            "description": obj.description,
            "updateTime": datetime.strftime(obj.update_time, "%Y-%m-%d %H:%M"),
            "owner":     cls.user_object(obj.owner),
            "thumbnail": cls.__build_thumbnail(obj.id),
            "score":     cls.__rating(obj.rating_total, obj.rating_count),
            "rating":    rating
        }
        if ott is not None:
            result["source"] = cls.ott_source_object(ott.ottsource)
            result["originalLink"] = ott.original_link
        return result
