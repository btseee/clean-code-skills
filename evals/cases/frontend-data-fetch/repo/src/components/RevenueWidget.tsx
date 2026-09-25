import { useEffect, useState } from "react";

type Revenue = { totalCents: number };

export function RevenueWidget() {
  const [totalCents, setTotalCents] = useState<number | null>(null);

  useEffect(() => {
    fetch("/api/revenue/this-month")
      .then((response) => response.json())
      .then((revenue: Revenue) => setTotalCents(revenue.totalCents));
  }, []);

  if (totalCents === null) {
    return null;
  }

  return <span>${(totalCents / 100).toFixed(2)}</span>;
}
