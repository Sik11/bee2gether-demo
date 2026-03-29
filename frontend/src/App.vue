<script setup>
import { mdiMap, mdiCalendar, mdiAccountCircle,mdiAccountGroup  } from '@mdi/js';
import Wrapper from "./components/helper/Wrapper.vue";
import Map from "./components/Map.vue";
import Auth from './components/Auth.vue';
import CreateEvent from './components/CreateEvent.vue';
import YourEvents from './components/YourEvents.vue';
import YourGroups from './components/YourGroups.vue';
import CreateGroups from './components/CreateGroup.vue';
import GroupOverview from './components/GroupOverview.vue';
import Account from './components/Account.vue';
import EventOverview from './components/EventOverview.vue'
import { auth } from './store/auth'
import { pages } from './store/pages'
import { settings } from './store/settings'
import { startTrackingLocation } from './store/userLocation'
import { startPollingEvents, startPollingEventAttendees } from './store/events';
import { startPollingAllGroups, startPollingUserGroups } from './store/groups';

// start tracking user location
startTrackingLocation();
startPollingEvents();
startPollingAllGroups();
startPollingUserGroups();
startPollingEventAttendees();

// Preset the pages you can move between
pages.init([
  { component: Map, id: "map", label: {text: "Map", icon: mdiMap}, props: {unsued: 'this feature does exist'}},
  { component: YourEvents, id: "events", label: {text: "Your Events", icon: mdiCalendar}},
  { component: YourGroups, id: "groups", label: {text: "Groups", icon: mdiAccountGroup}},
  { component: Account, id: "account", label: {text: "Account", icon: mdiAccountCircle}},
  { component: CreateEvent, id: "create-event" },
  { component: CreateGroups, id: "create-group" },
  { component: GroupOverview, id: "group-overview" },
  { component: EventOverview, id: "event-overview" }
], 'map')
</script>

<template>
  <div 
  :class="['viewport', {'dark-mode': settings.isDarkMode}]"
  >
    <Auth v-if="!auth.isLoggedIn"/>
    <Wrapper v-else/>
  </div>
</template>

<style>
@import './assets/themes.css';
/* Setting a global font and color for all elements. */
* {
  font-family: 'Inter', sans-serif;
  color: var(--primary-color);
  
}
body {
  background-color: var(--background-color);
}

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  position: relative;
}

/* Set to screen shape */
#app, body, .viewport {
  width: 100vw;
  height: 100vh;
  padding: 0px;
  margin: 0px;
  border: 0px;
  display: block;
  overflow-x: hidden;
}
</style>
