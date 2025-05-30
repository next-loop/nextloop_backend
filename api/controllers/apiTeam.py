from ninja import Router
from typing import List

from api.models.team import TeamMember, TeamMemberOut

team_router = Router(tags=["Team APIs"])

@team_router.get("/", response=List[TeamMemberOut])
def get_team_members(request):
    members = TeamMember.objects.all()
    return [
        TeamMemberOut(
            id=member.id,
            name=member.name,
            designation=member.designation,
            description=member.description,
            photo=member.photo.url if member.photo else None
        )
        for member in members
    ]
