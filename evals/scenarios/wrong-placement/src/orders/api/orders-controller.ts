import { orderSubtotalCents, type Order } from "../domain/order";
import type { OrderRepository } from "../infra/order-repository";

export class OrdersController {
  constructor(private readonly orders: OrderRepository) {}

  async total(id: string): Promise<{ totalCents: number } | { error: string }> {
    const order: Order | undefined = await this.orders.byId(id);
    if (!order) return { error: "not found" };
    return { totalCents: orderSubtotalCents(order) };
  }
}
