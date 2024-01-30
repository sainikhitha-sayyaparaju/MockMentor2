from djongo import models
# from gridfs_storage.storage import GridFSStorage


class Interview(models.Model):
    topic = models.CharField(max_length=30)
    subtopic = models.CharField(max_length=30, default='not required')
    expertise = models.CharField(max_length=30)
    number = models.IntegerField(default=10)


class Interview_Feedback(models.Model):
    topic = models.CharField(max_length=30, default="")
    subtopic = models.CharField(max_length=30, default='not required')
    expertise = models.CharField(max_length=30, default="")
    number = models.IntegerField(default=10)
    up = models.IntegerField(default=0)
    happy = models.IntegerField(default=0)
    neutral = models.IntegerField(default=0)
    surprise = models.IntegerField(default=0)
    max_emotions = models.TextField(default='ans')
    feedback = models.TextField(default='ans')
    ec_center = models.IntegerField(default=0)
    loc1 = models.BooleanField(default=True)
    loc2 = models.BooleanField(default=True)
    questions = models.TextField(default='ans')
    answers = models.TextField(default='ans')
    answers_feedback = models.TextField(default='ans_feed')
    indices = models.TextField(default='ans')
    num = models.IntegerField(default=0)