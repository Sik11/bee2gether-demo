
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
  <div>
    <svg 
      :width="width" 
      :height="height" 
      :style="style" 
      :id="id" :class="customClass"
      viewBox="0 0 25 25"
      preserveAspectRatio="xMidYMid meet"
    >
      <path :d="path" />
    </svg>
  </div>
</template>
<style scoped>
</style>