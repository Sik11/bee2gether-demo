<script setup>
import { mdiMapSearch as searchIcon } from '@mdi/js';
import svgIcon from './svg-icon.vue';
import { ref, watch, defineEmits  } from 'vue';
import { events } from '../../store/events';

const { customClass } = defineProps({
  customClass: { type: [String, Object, Array], default: "" },
})
const emit = defineEmits(['select']);

const searchTerm = ref('');
const onSubmit = (name) => {
  events.searchEvent(searchTerm.value).then(res =>{
    if (res.result) {
      onOpen(res.events[0])
    }
  })
}
const onOpen = (event) => {
  events.searchResults = []
  emit('select', event)
}

watch(searchTerm, (x,y) => {
  events.searchEvent(searchTerm.value)
})

</script>

<template>
  <div :class="customClass">
    <form @submit.prevent="onSubmit" >
      <input type="text" id="search-bar" v-model="searchTerm" placeholder="Search for event..." autocomplete="off" required>
      <div id="results" v-if="events.searchResults.length > 0 && searchTerm !== '' ">
        <button class="result" v-for="event in events.searchResults" @click.prevent="onOpen(event)"> 
          <span class="name"> {{event.name}} </span> 
          <span class="time"> @{{event.username}} </span> 
        </button>
      </div>
      <label for="search-bar">
        <svg-icon :path="searchIcon" height="2rem" custom-class="svg"/>
      </label>
      
    </form>
  </div>
</template>

<style scoped lang="scss">
.result {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 2rem;
  width: 100%;
  background: none;
  border: none;
  padding: .5rem;
  .name {
    font-weight: bold;
  }
  .time {
    margin: 0 0 0 auto;
    font-weight: normal;
  }
}
form {
  height: 3rem;
  color: var(--primary-color);
  background-color: var(--background-color);
  font-size: 0.9rem;
  display: flex;
  flex-direction: row-reverse;
  align-items: center;
  border-radius: 34px;
  z-index: 0;
  position: relative;

  #results {
    position: absolute;
    z-index: -100;
    top: calc(100%);
    width: 100%;
    padding-top: 1rem;
    background-color: var(--background-color);
    opacity: 0; 
    pointer-events: none; 
    margin-top: -1rem;
    padding: 2rem 0 1rem 0;
    transition: opacity .1s var(--cubic-bezier);
    box-shadow: 0px 2px 4px 2px var(--shadow);
  }

  input[type="text"] {
    width: 100%;
    background-color: var(--background-color);
    height: 100%;
    transition: padding-left .1s var(--cubic-bezier);
    border-radius: 34px;
    border: none;
    text-align: left;
    font-weight: 400;
    padding-left: 3rem;
    box-shadow: 0px 2px 4px 2px var(--shadow);

    &::placeholder {
      transition: opacity .1s var(--cubic-bezier);
      color: var(--primary-color);
    }
    &:focus,
    &:valid {
      padding-left: 1rem;
      &::placeholder {
        opacity: 0;
      }
      ~ label {
        opacity: 0;
      }
      + #results {
        opacity: 1;
        pointer-events: all; 
      }
    }
    &:focus,
    &:valid,
    &:disabled {
      outline: none;
    }
  }
  
  label  {
    width: 0px;
    transition: opacity .1s var(--cubic-bezier);
    opacity: 1;
    fill: var(--primary-color);
    stroke: var(--primary-color); 
    div {
      position: relative;
      width: 2rem;
      padding-left: .25rem;
    }
  }
}
</style>