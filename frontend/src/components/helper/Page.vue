<script setup>
const { title } = defineProps({
  title: { type: String, required: true },
  customClass: { type: [String, Object, Array], default: "" },
});
</script>

<template>
  <section :class="['page-wrapper', customClass]">
    <header class="page-title">
      <h1>{{ title }}</h1>
      <div class="page-title__rule"></div>
    </header>
    <slot/>
  </section>
</template>

<style scoped lang="scss">
.page-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  gap: 1.25rem;
  padding: 1.1rem;
}

.page-title {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;

  h1 {
    margin: 0;
    text-align: left;
    font-family: var(--font-display);
    font-size: clamp(1.7rem, 2.8vw, 2.4rem);
    line-height: 1.02;
    letter-spacing: -0.05em;
  }

  &__rule {
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, var(--border-strong), transparent);
  }
}
</style>
