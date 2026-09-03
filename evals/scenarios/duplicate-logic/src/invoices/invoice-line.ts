export interface InvoiceLine { description: string; amountCents: number; currency: string; }

export function describeLine(line: InvoiceLine): string {
  return `${line.description}: ${line.amountCents} ${line.currency}`;
}
