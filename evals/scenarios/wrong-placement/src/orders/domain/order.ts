export interface OrderLine { unitPriceCents: number; quantity: number; }
export interface Order { id: string; lines: OrderLine[]; currency: string; }

export function orderSubtotalCents(order: Order): number {
  return order.lines.reduce((sum, line) => sum + line.unitPriceCents * line.quantity, 0);
}
