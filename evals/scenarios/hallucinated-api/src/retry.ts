export async function withRetry<T>(fn: () => Promise<T>, attempts = 3): Promise<T> {
  let lastError: unknown;
  for (let i = 0; i < attempts; i++) {
    try { return await fn(); } catch (error) { lastError = error; }
  }
  throw lastError;
}
