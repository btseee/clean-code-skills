export type Order = { id: string; customer: string; amountEur: number };

const orders: Order[] = [
  { id: "o1", customer: "Ada", amountEur: 120 },
  { id: "o2", customer: "Grace", amountEur: 80 },
  { id: "o3", customer: "Lin", amountEur: 145.5 },
];

export function getOrders(): Order[] {
  return orders;
}
