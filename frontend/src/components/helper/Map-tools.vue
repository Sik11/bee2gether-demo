<script setup>
import { mdiClose, mdiCreation } from '@mdi/js';
import svgIcon from './svg-icon.vue';
import { pages } from '../../store/pages'

const { customClass } = defineProps({
  customClass: { type: [String, Object, Array], default: "" },
})
console.log(pages)

</script>
<template>
  <span :class="customClass" id="body">
    <input type="checkbox" id="filter-checkbox">
    <label for="filter-checkbox">
      <div class="icons">
        <span id="icon-1">
          <svg-icon  :path="mdiCreation" height="2rem"/>
        </span>
        <span id="icon-2">
          <svg-icon :path="mdiClose" height="2rem"/>
        </span>
      </div>
      <div id="inner-body" @click.prevent="">
        <h5> Magic Tools </h5>
        <button class="btn" @click="() => pages.addLayer('create-event')"> Create Event </button>
      </div>
    </label>
  </span>
  
</template>

<style scoped lang="scss">
#body {
  --expand-height: 200px;
  --expand-offset: 3rem;
}
#filter-checkbox {
  width: 0px;
  height: 0px;
  visibility: hidden;
  &:checked + label, &:focus + label {
    width: calc(100vw - 2rem);
    height: var(--expand-height);
    #icon-1 {
      display: none;
    }
    #icon-2 {
      display: inline-block;
    }
    #inner-body {
      opacity: 1;
    }
  }

}
label {
  position: relative;
  pointer-events: none;
  bottom: 0;
  right: 0;
  width: 4rem;
  height: 4rem;
  
  background-color: var(--background-color);
  border-radius: 34px;
  box-shadow: 0px 2px 4px 2px rgba(0, 0, 0, 0.25);
  transition: width .2s var(--cubic-bezier), height .2s var(--cubic-bezier);
  display: flex;
  align-items: center;
  cursor: pointer;
  overflow: hidden;

  .icons {
    z-index: 2;
    pointer-events: all;
    position: absolute;
    top: 1rem;
    right: .5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    
    fill: #FFB800;
    #icon-2 {
      display: none;
    }
  }

  #inner-body {
    z-index: 1;
    position: absolute;
    width: calc(100vw - 2rem - var(--expand-offset));
    height: var(--expand-height);
    right: var(--expand-offset);
    bottom: 0px;
    transition: opacity .5s var(--cubic-bezier);
    opacity: 0;
    pointer-events: all;
    padding: 1.5rem;
    text-align: left;

    h5 {
      margin: 0 0 1rem 0;
      padding: 0;
      font-weight: 300;
    }
    .btn {
      border: none;
      padding: 0.5rem;
      width: 100%;
      color: black;
      background-color: #00d965;
      font-size: 1rem;
      font-weight: bold;
      border-radius: 2rem;
      cursor: pointer;
      box-shadow: 0px 2px 4px 0px rgba(0, 0, 0, 0.25);
      color: white;
      background-color: #007BFF;
    }
  }
}
</style>