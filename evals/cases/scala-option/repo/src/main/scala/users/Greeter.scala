package users

object Greeter:

  def greet(repository: UserRepository, id: String): String =
    val user = repository.findById(id)
    if user == null then "Unknown user" else s"Hello, ${user.name}!"
