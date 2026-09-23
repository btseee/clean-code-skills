import { Controller, Delete, Param } from "@nestjs/common";
import { UsersService } from "./users.service";

@Controller("users")
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Delete(":id")
  async remove(@Param("id") id: string) {
    return this.usersService.remove(id);
  }
}
