from django.db import models
from tu_entrega_app.models import User


# Create your models here.

class BlockPlayer(models.Model):
    player_blocker = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="blocking_players", null=True)
    player_blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocked_by_players")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=['player_blocker', 'player_blocked'],
                name="player_can_only_block_other_player_once",
            )
        ]

