<main class="w-full flex justify-center">
    <div class="max-w-2xl w-full">
        <div class="flex flex-col gap-2 p-2">
            <p dir="rtl" class="mr-4 text-3xl my-4">آخر التخفيضات</p>
            <div class="flex overflow-x-auto gap-4">
                {#each Array(6) as _, i}
                {@const ratio = Math.random() * 0.5 + 0.75}
                    <div class="w-30 grow-0 shrink-0 bg-slate-950 overflow-hidden rounded flex flex-col">
                        <div class="overflow-hidden relative bg-rose-400 w-30 h-30">
                            <img src="/products/img{i + 1}.png" alt="Image {i + 1}" class="w-full !h-full object-cover" />
                            <span class="absolute top-0 right-0 bg-green-600 text-white text-bold text-xs rounded-bl p-1">{Math.round(ratio * 100)}%</span>
                            {#if i === 2}
                                <span class="absolute bottom-0 left-0 right-0 bg-rose-500 text-white text-xs p-1 text-center">آخر طرف متبقي</span>
                            {/if}
                        </div>
                        <div class="p-2 flex flex-col gap-1">
                            <p class="text-sm text-gray-400">اسم المنتج</p>
                            <p class="text-base font-bold"><span class="line-through opacity-50">${((i + 1) * Math.random() * 10).toFixed(2)}</span> <span>${((i + 1) * Math.random() * 10 * ratio).toFixed(2)}</span></p>
                        </div>
                    </div>
                {/each}
            </div>
        </div>
    </div>
</main>