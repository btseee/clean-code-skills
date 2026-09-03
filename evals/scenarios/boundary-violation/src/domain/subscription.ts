import { systemClock } from "../infra/clock";

export interface Subscription { renewsAt: Date; }

export function isDue(subscription: Subscription): boolean {
  return subscription.renewsAt.getTime() <= systemClock.now().getTime();
}
