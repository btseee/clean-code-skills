import { Injectable } from "@nestjs/common";

type User = { id: string; email: string };

@Injectable()
export class UsersService {
  private readonly users: User[] = [{ id: "u1", email: "ada@example.com" }];

  async remove(id: string): Promise<{ removed: boolean }> {
    const before = this.users.length;
    const remaining = this.users.filter((user) => user.id !== id);
    return { removed: remaining.length < before };
  }
}
