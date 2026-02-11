<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { MenuIcon, SearchIcon, ShoppingCart } from 'lucide-svelte';

	let { children } = $props();
</script>

<svelte:head
	><link rel="icon" href={favicon} />
	<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@1.0.4/css/bulma.min.css" />
</svelte:head>

<div class="flex justify-center w-full">
	<div class="flex h-12 items-center max-w-2xl w-full justify-between bg-black p-2 px-4">
		<!-- svelte-ignore a11y_consider_explicit_label -->
		<div class="flex flex-1 items-center justify-start gap-2">
			<button class="inline-block sm:hidden">
				<MenuIcon />
			</button>
			<div class="hidden items-center gap-2 sm:flex">
				<input
					type="text"
					placeholder="Search..."
					class="w-30 rounded bg-gray-800 px-4 py-2 text-white"
				/>
			</div>
		</div>
	
		<a href="/" class="flex justify-center">متجر يونا</a>
	
		<div class="flex flex-1 justify-end gap-2">
			<a href="/cart" class="ml-auto hidden items-center gap-2 rounded-2xl bg-gray-700 sm:flex">
				<ShoppingCart />
				<span>0</span>
			</a>
			<a href="/auth" class="button is-link">تسجيل الدخول</a>
		</div>
	</div>
</div>

{@render children()}
