export function applyDiscount(priceCents: number, percent: number): number {
  // Bug: floating-point drift; 11999 * 0.85 is 10199.15, which then rounds the wrong way for some inputs.
  return Math.floor(priceCents * (1 - percent / 100));
}
