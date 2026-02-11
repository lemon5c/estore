<script>
    let activeTab = 'login';
</script>

<div class="container">
    <div class="tabs">
        <button 
            class="tab" 
            class:active={activeTab === 'login'}
            on:click={() => activeTab = 'login'}
        >
            Login
        </button>
        <button 
            class="tab"
            class:active={activeTab === 'signup'}
            on:click={() => activeTab = 'signup'}
        >
            Sign Up
        </button>
    </div>

    {#if activeTab === 'login'}
        <form class="form">
            <h2>Login</h2>
            <input type="email" placeholder="Email" required />
            <input type="password" placeholder="Password" required />
            <button type="submit">Login</button>
        </form>
    {:else}
        <form class="form">
            <h2>Sign Up</h2>
            <input type="email" placeholder="Email" required />
            <input type="password" placeholder="Password" required />
            <input type="password" placeholder="Confirm Password" required />
            <button type="submit">Sign Up</button>
        </form>
    {/if}
</div>

<style>
    .container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        border: 1px solid #ccc;
        border-radius: 8px;
    }

    .tabs {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
        border-bottom: 2px solid #eee;
    }

    .tab {
        padding: 0.5rem 1rem;
        border: none;
        background: none;
        cursor: pointer;
        font-size: 1rem;
        border-bottom: 3px solid transparent;
    }

    .tab.active {
        border-bottom-color: #007bff;
        color: #007bff;
    }

    .form {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    h2 {
        margin: 0 0 1rem 0;
    }

    input {
        padding: 0.75rem;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 1rem;
    }

    button[type="submit"] {
        padding: 0.75rem;
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 1rem;
        cursor: pointer;
    }

    button[type="submit"]:hover {
        background-color: #0056b3;
    }
</style>