<script lang="ts">
  import { onMount } from "svelte";

  type Product = { id: string; name: string; priceEur: number };

  let products: Product[] = $state([]);

  onMount(async () => {
    const response = await fetch("/api/products");
    products = await response.json();
  });
</script>

<ul>
  {#each products as product (product.id)}
    <li>{product.name} — {product.priceEur} EUR</li>
  {/each}
</ul>
