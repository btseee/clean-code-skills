package users

final class UserRepository(usersById: Map[String, User]):

  def findById(id: String): User =
    usersById.get(id) match
      case Some(user) => user
      case None       => null
