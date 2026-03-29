<script setup>
import { pages } from '../store/pages'
import { settings } from '../store/settings';
import { auth } from '../store/auth';
import Page from './helper/Page.vue';
import Avatar from './helper/Avatar.vue';

console.log(auth.user)
</script>

<template>
  <Page title="Your Account" custom-class="body">
    <div class="header">
      <Avatar :username="auth.user.username" custom-class="pfp"/>
      <h2> {{auth.user.username}} </h2>
      <h5> #{{auth.user.userId.substring(0, 6)}}</h5>
    </div>
    <h4>Settings</h4>
    <div class="form-check form-switch">
      <input v-model="settings.isDarkMode" class="form-check-input" type="checkbox" role="switch" id="darkModeCheck">
      <label class="form-check-label" for="darkModeCheck">Toggle Dark Mode</label>
    </div>
    <button type="button" class="logout-btn" @click="()=>auth.logout()">Logout</button>
  </Page>
</template>

<style scoped lang="scss">
.body {
  text-align: left;
  h4 {
    margin-top: 1rem;
  }
}
.header {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  .pfp {
    margin: .5rem;
    width: 50vw;
    height: 50vw;
    border-radius: 100%;
    overflow: hidden;
    box-shadow: 0px 2px 4px 2px var(--shadow);
  }
  h2 {
    font-size: 2.5rem;
    font-weight: bolder;
  }
  h5 {
    font-weight: 600;
    color: var(--secondary-color);
  }
}
.logout-btn {
  position: absolute;
  bottom: 1rem;
  border: none;
  padding: 0.5rem;
  width: calc(100% - 2rem);
  color: black;
  background-color: #00d965;
  font-size: 1rem;
  font-weight: bold;
  border-radius: 2rem;
  cursor: pointer;
  box-shadow: 0px 2px 4px 0px rgba(0, 0, 0, 0.25);
  margin-top: auto;
  color: white;
  background-color: #007BFF;
}
</style>