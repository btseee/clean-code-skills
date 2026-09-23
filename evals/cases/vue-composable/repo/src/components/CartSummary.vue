<script setup lang="ts">
import { computed } from "vue";

type CartItem = { price: number; quantity: number };

const props = defineProps<{ items: CartItem[] }>();

function calculateCartTotal(items: CartItem[]): number {
  let total = 0;
  for (const item of items) {
    total += item.price * item.quantity;
  }
  return total;
}

const total = computed(() => calculateCartTotal(props.items));
</script>

<template>
  <p>Cart total: {{ total.toFixed(2) }}</p>
</template>
