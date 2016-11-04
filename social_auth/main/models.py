from django.db import models
from django.contrib import admin


class Token(models.Model):
    access_token = models.CharField(max_length=500)
    expires = models.DateTimeField()
    user_id = models.IntegerField()
    source = models.CharField(max_length=100)


class SocialGroups(models.Model):
    source = models.CharField(max_length=100)
    group_name = models.CharField(max_length=200)
    group_id = models.PositiveIntegerField()


class TokenAdmin(admin.ModelAdmin):
    pass

class SocialGroupsAdmin(admin.ModelAdmin):
    pass

admin.site.register(Token, TokenAdmin)
admin.site.register(SocialGroups, SocialGroupsAdmin)