<script setup>
const { title } = defineProps({
  title: { type: String, required: true },
  customClass: { type: [String, Object, Array], default: "" },
})
</script>

<template>
  <div :class="['viewport', customClass]" id="page-wrapper">
    <div id="page-title">
      <h1>{{ title }}</h1>
      <hr>
    </div>
    <slot/>
  </div>
</template>

<style scoped lang="scss">
#page-wrapper {
  padding: 0rem 1rem 0rem 1rem;
}
#page-title {
  h1 {
    text-align: right;
    font-weight: 300;
    margin: 2.5rem 0rem 1.5rem;
  }
  hr {
    opacity: 0.25;
  }
}
</style>