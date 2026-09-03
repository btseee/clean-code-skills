// Someone's earlier drive-by copy. Left in the fixture on purpose.
export function formatMoneyV2(cents: number, currency: string): string {
  return `${currency} ${(cents / 100).toFixed(2)}`;
}
