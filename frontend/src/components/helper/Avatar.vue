<script setup>
// Find the right icon with with https://pictogrammers.com/library/mdi/
import { getAvatar } from '../../api';
const props = defineProps({
  style: { type: Object, default: () => ({}) },
  username: { type: String, required: true },
  id: { type: String, default: "" },
  customClass: { type: [String, Object, Array], default: "" },
});

</script>
<template>
  <div 
    :class="customClass"
    :style="style"
    v-html="getAvatar(username)"
  />
</template>
