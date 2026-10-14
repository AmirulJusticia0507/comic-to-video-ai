<template>
  <footer class="border-t border-white/10 bg-slate-950/70 px-6 py-8 text-sm text-slate-500 backdrop-blur-xl">
    <div class="mx-auto flex max-w-6xl flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <p>© 2026 Comic Motion Studio</p>
      <nav class="flex flex-wrap gap-x-5 gap-y-2">
        <router-link to="/privacy" class="hover:text-slate-200">Kebijakan Privasi</router-link>
        <router-link to="/cookies" class="hover:text-slate-200">Cookies</router-link>
        <router-link to="/help" class="hover:text-slate-200">Bantuan</router-link>
        <router-link to="/about" class="hover:text-slate-200">Tentang</router-link>
      </nav>
    </div>
  </footer>
</template>
