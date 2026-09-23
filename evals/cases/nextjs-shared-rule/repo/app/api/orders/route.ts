import { NextResponse } from "next/server";
import { getOrders } from "../../../lib/orders";

export async function GET() {
  return NextResponse.json(getOrders());
}
