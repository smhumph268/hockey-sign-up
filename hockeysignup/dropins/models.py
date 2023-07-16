from django.db import models

from users import models as CustomUserModel


class Rink(models.Model):
    name = models.CharField(max_length=50, unique=True)
    address = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'address')


class DropIn(models.Model):
    rink = models.ForeignKey(Rink, on_delete=models.PROTECT)
    name = models.CharField(max_length=100, help_text='Name of the drop-in as appears on the Chiller website')
    datetime = models.DateTimeField('drop in datetime')
    visible = models.BooleanField(default=False, help_text='Makes this drop-in visible on the website for users')

    def __str__(self):
        return self.datetime.strftime('%B %d, %Y %I:%M %p')+' | '+self.name.__str__()+' | '+self.rink.__str__()

    class Meta:
        verbose_name_plural = 'Drop-Ins'
        unique_together = ('rink', 'datetime', 'name')


class SignUp(models.Model):
    user = models.ForeignKey(CustomUserModel.CustomUser, on_delete=models.CASCADE)
    dropIn = models.ForeignKey(DropIn, on_delete=models.CASCADE)
    datetime = models.DateTimeField('sign up datetime')
    paid = models.BooleanField(default=False)
    rostered = models.BooleanField(default=False)
    isGoalie = models.BooleanField(default=False)
    isWhiteTeam = models.BooleanField(default=False, help_text='Denotes if player is on the white team')

    class Meta:
        verbose_name_plural = 'Sign-ups'
        unique_together = ('user', 'dropIn')


class Games(models.Model):
    dropIn = models.ForeignKey(DropIn, on_delete=models.CASCADE)
    winning_team_name = models.CharField(max_length=50)
    losing_team_name = models.CharField(max_length=50)
    winning_score = models.IntegerField(default=0)
    losing_score = models.IntegerField(default=0)
    game_number = models.IntegerField(default=0, help_text='1 = first, 2 = second, etc.')

    def __str__(self):
        return self.dropIn.__str__()+' | Game '+self.game_number.__str__()

    class Meta:
        verbose_name_plural = 'Games'
        unique_together = ('dropIn', 'game_number')


class Stats(models.Model):
    user = models.ForeignKey(CustomUserModel.CustomUser, on_delete=models.CASCADE)
    game = models.ForeignKey(Games, on_delete=models.CASCADE)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Stats'
        unique_together = ('user', 'game')
