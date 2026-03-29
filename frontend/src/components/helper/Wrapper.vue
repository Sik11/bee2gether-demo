<script setup>
import { ref } from 'vue';
import { mdiMenu } from '@mdi/js';
import svgIcon from './svg-icon.vue';
import { auth } from '../../store/auth'
import { pages } from '../../store/pages'
import { settings } from '../../store/settings';
import logo from  '../../assets/logo.png'
import darkLogo from '../../assets/dark-logo.png'

// const {children, selected, setSelected} = defineProps(['children', 'selected', 'setSelected']);
const isHidden = ref(true);

const toggleMenu = () => {
  isHidden.value = !isHidden.value
}

const select = (id) => {
  pages.setSelected(id)
  toggleMenu()
}
</script>

<template>
  <div class="viewport">
  <div id="hamburger-button" @click="toggleMenu">
    <svg-icon :path="mdiMenu" width="2.25rem" class="icon"/>
  </div>
    
  <div id="menu-wrapper" @click="toggleMenu" class="viewport" :style="{'right': isHidden ? '100vw' : '0vw' }">
    <div @click.stop>
      <img :src="settings.isDarkMode ? darkLogo : logo" alt="Logo saying Bee 2 Gether with a happy bee ontop"/>
      <ul>
        <li> Hello, {{auth.user.username}} </li>
        <li 
        v-for="({id, label}, _) in pages.getLabelledTabs()" 
        :key="id"
         @click="select(id)">
          <svg-icon :path="label.icon" height="2rem"/>
          <span>{{ label.text }}</span>
        </li>
      </ul>
    </div>
  </div>

  <!-- <div id="event-button" @click="toggleAddEvent">
    <svg-icon :path="mdiCreation" width="2.25rem" class="star-icon" />
  </div> -->

    <div 
    v-for="({component, id, props}, index) in pages.tabs" 
    :key="id" 
    :class="['viewport', 'page', {
      'selected': pages.isSelected(id),
      'visibile': pages.isVisible(id),
      'no-transition': pages.lastAction === 'setSelected'
    }]" 
    :style="{zIndex: pages.getZIndex(id)}"
    :label="id"
    >
      <!-- <component v-if="pages.isSelected(id)" :is="component" v-bind="props"/> -->
      <component :is="component" v-bind="props"/>
    </div>
  </div>
  
</template>

<style scoped lang="scss">
@keyframes slideAndHide {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(100vw);
    display: none;
  }
}
@keyframes reverseSlideAndShow {
  0% {
    transform: translateX(100vw);
    display: none;
  }
  100% {
    transform: translateX(0);
    display: block;
  }
}
.page {
  position: absolute;
  background-color: var(--background-color);
  transition: var(--background-transition);

  
  &:not(.visibile) {
    animation: slideAndHide .2s forwards;
  }
  &.visibile {
    display: block;
    animation: reverseSlideAndShow .2s forwards;
  }
  &.no-transition {
    animation-duration: 0s;
  }
}
#hamburger-button {
  position: absolute;
  z-index: 20;
  top: 2rem;
  height: 3rem;
  width: 4rem;
  border-radius: 0 2rem 2rem 0;

  background-color: #FFC01F;
  filter: drop-shadow(0px 2px 4px var(--shadow));

  display: flex;
  align-items: center;
  justify-content: center;
}
#menu-wrapper {
  position: absolute;
  z-index: 30;
  top: 0;
  background: rgba(0, 0, 0, 0.37);
  backdrop-filter: blur(3.5px); 
  transition: right .2s cubic-bezier(.57,.95,.71,.91);
  
  > div {
    width: calc(100% - 5rem);
    height: 100%;
    background-color: var(--background-color);
    box-shadow: 4px 0px 4px 0px var(--shadow);
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
  }
  img {
    width: 15vh;
    margin: .5rem 0 0 .5rem;
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
  }
}
#event-button {
  position: absolute;
  z-index: 20;
  bottom: 2rem;
  right: 1rem;
  height: 3rem;
  width: 3rem;
  border-radius: 2rem 2rem 2rem 2rem;

  background-color: #fefefe;
  filter: drop-shadow(4px 4px 4px rgba(0, 0, 0, 0.25));

  display: flex;
  align-items: center;
  justify-content: center;
}

#menu-wrapper ul {
  list-style-type: none;
  padding: 0px;
  margin: 0px;
  font-size: 1rem;
  font-weight: 500;

  li {
    height: 3rem;
    padding-left: .5rem;
    border-bottom: 1px solid var(--shadow);
    display: flex;
    align-items: center;
    justify-content: center;

    &:first-child {
      background: #FFB800;
      border-top: 1px solid var(--shadow);
    }
    &:active {
      background-color: var(--shadow);
    }
    span {
      margin-right: auto;
    }
    div {
      fill: var(--primary-color);
      stroke: var(--primary-color); 
    }
  }
}
.icon {
  margin-right: .5rem;
}
.star-icon{
  fill: #FFB800;
}
</style>