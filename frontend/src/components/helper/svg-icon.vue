
<script setup>
// Find the right icon with with https://pictogrammers.com/library/mdi/
const props = defineProps({
  width: { type: [String, Number], default: "3rem" },
  height: { type: [String, Number], default: "3rem" },
  style: { type: Object, default: () => ({}) },
  path: { type: String, required: true },
  id: { type: String, default: "" },
  customClass: { type: [String, Object, Array], default: "" },
});

</script>
<template>
  <svg
    :width="width"
    :height="height"
    :style="style"
    :id="id"
    :class="['svg-icon', customClass]"
    viewBox="0 0 25 25"
    preserveAspectRatio="xMidYMid meet"
    fill="currentColor"
    aria-hidden="true"
  >
    <path :d="path" />
  </svg>
</template>

<style scoped>
.svg-icon {
  display: block;
  flex: 0 0 auto;
}
</style>
