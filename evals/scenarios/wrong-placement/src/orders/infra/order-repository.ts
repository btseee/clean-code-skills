import type { Order } from "../domain/order";
export interface OrderRepository { byId(id: string): Promise<Order | undefined>; }
