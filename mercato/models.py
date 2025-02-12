from django.db import models


class Kap(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='kap_images/', blank=True, null=True)
    description = models.TextField(null=True, blank=True)

class Participant(models.Model):
    name = models.CharField(max_length=200)
    kap = models.ForeignKey(Kap, on_delete=models.CASCADE)

class KapParticipation(models.Model):
    kap = models.ForeignKey(Kap, on_delete=models.CASCADE)
    year = models.IntegerField()
    number_of_participants = models.IntegerField(min= 0, max= 2)

class Participation(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    year = models.IntegerField()
    kap_participation = models.ForeignKey(KapParticipation, on_delete=models.CASCADE)

class Choice(models.Model):
    participation = models.ForeignKey(Participation, on_delete=models.CASCADE)
    kap = models.ForeignKey(Kap, on_delete=models.CASCADE)


