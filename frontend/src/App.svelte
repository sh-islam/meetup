<script>
  import { parseHash } from './lib/store.js'
  import Home from './routes/Home.svelte'
  import NewMeetup from './routes/NewMeetup.svelte'
  import OpenMeetup from './routes/OpenMeetup.svelte'
  import Meetup from './routes/Meetup.svelte'

  let route = $state(parseHash())
  // shimmer (glow drift + sweep) only on the home page
  $effect(() => { document.body.classList.toggle('home', route.page === 'home') })
  $effect(() => {
    const onHash = () => { route = parseHash() }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  })
</script>

{#if route.page === 'home'}
  <Home />
{:else if route.page === 'new'}
  <NewMeetup step={route.step} />
{:else if route.page === 'open'}
  <OpenMeetup />
{:else if route.page === 'meetup'}
  {#key route.token}
    <Meetup token={route.token} tab={route.tab} />
  {/key}
{/if}
