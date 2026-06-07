import enum

class VotingType(str, enum.Enum):
    JUDGES = "JUDGES"
    PARTICIPANTS = "PARTICIPANTS"
    ALL_USERS = "ALL_USERS"

class ContextRole(str, enum.Enum):
    PARTICIPANT = "PARTICIPANT"
    JUDGE = "JUDGE"

class UserRole(str, enum.Enum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"

class HackathonStatus(int, enum.Enum):
    PLANNED = 0
    REGISTRATION = 1
    ACTIVE = 2
    COMPLETED = 3