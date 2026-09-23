import { getOrders } from "../../lib/orders";

export default function OrdersPage() {
  const orders = getOrders();
  return (
    <ul>
      {orders.map((order) => (
        <li key={order.id}>
          {order.customer}: {order.amountEur} EUR
        </li>
      ))}
    </ul>
  );
}
