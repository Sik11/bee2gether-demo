<script setup>
import { pages } from '../store/pages'
import Page from './helper/Page.vue';
import { sendJoinEvent, sendLeaveEvent, removeEvent, events, findEventAttendees } from '../store/events'
import { ref, watchEffect, toRefs } from 'vue';
import { auth } from '../store/auth';
import heartBackground from '../assets/heart-background-full.png'
import Avatar from './helper/Avatar.vue';

const msg = ref('')
const showJoin = ref(true);
const join = async () => {
  const response = await sendJoinEvent(auth.user.userId, auth.user.username, events.selected.id);
  events.selected.attendees = await findEventAttendees(events.selected.id);
  msg.value = response.msg || '';
}

const leave = async () => {
  const response = await sendLeaveEvent(auth.user.userId, events.selected.id);
  events.selected.attendees = await findEventAttendees(events.selected.id);
  msg.value = response.msg || '';
}

const onDelete = async () => {
  const response = await removeEvent(events.selected.id, auth.user.userId);
  msg.value = '';
  pages.dropLayer()
}
function backtoMap() {
  msg.value = '';
  pages.dropLayer()
}

watchEffect(() => {
  // Check if 'attendees' exists in 'events.selected'
  if (!events.selected.attendees) {
    return; // Do nothing if 'attendees' is not present
  }

  // Proceed with the existing logic if 'attendees' is present
  showJoin.value = !events.selected.attendees.some(attendee => attendee.userId === auth.user.userId);
});


</script>

<template>
  <Page title="Event Info">

    <form id="form">
      <div class="img-container">
        <img v-if="events.selected['eventImg(s)'][0]" :src="events.selected['eventImg(s)'][0]" alt="Event image" />
        <img v-else :src="heartBackground" alt="Event image" />
      </div>

      <div class="info-container">
        <div class="date"> {{events.selected.time}}</div>
        <div class="name"> {{events.selected.name}}</div>
  
        <div class="sub-title"> Description </div>
        <div class="description"> {{events.selected.description}}</div>
  
        <div class="sub-title"> Tags </div>
        <ul class="tags">
          <li v-for="tag in events.selected.tags">{{tag}}</li>
        </ul>
        
  
        <div class="sub-title"> Organiser </div>
        <div class="account">
          <Avatar :username="events.selected.username" custom-class="pfp"/>
          <div class="text">
            <div class="username"> {{events.selected.username}} </div>
            <div class="id"> #{{auth.user.userId.substring(0, 6)}} </div>
          </div>
        </div>
  
        <div class="sub-title"> Attendees </div>
        <div class="account" v-for="attendee in events.selected.attendees">
          <Avatar :username="attendee.username" custom-class="pfp"/>
          <div class="text">
            <div class="username"> {{attendee.username}} </div>
            <div class="id"> #{{attendee.userId.substring(0, 6)}} </div>
          </div>
        </div>
      </div>

      
    </form>

    
    <template v-if="events.selected.userId === auth.user.userId">
      <button class="overview-btn" @click="onDelete">Delete Event</button>
    </template>
    <template v-else>
      <template v-if="showJoin">
        <button class="overview-btn" @click="join">Join Event</button>
      </template>
      <template v-else>
        <button class="overview-btn" @click="leave">Leave Event</button>
      </template>
    </template>
    <button class="overview-btn" @click="backtoMap">Back To Map</button>
    <template v-if="msg === 'OK'">
      <p class="success-msg">Success!</p>
    </template>
    <template v-else>
      <p class="error-msg">{{ msg }}</p>
    </template>

  </Page>
</template>

<style scoped lang="scss">
#form {
  width: 100%;
  border-radius: 2rem;
  overflow: hidden;
  background-color: var(--background-color);
  box-shadow: 0px 2px 4px 2px var(--shadow);
  text-align: left;
  .img-container {
    width: 100%;
    height: 40vh;
    overflow: hidden;
    img {
      width: 100%; 
      height: 100%; 
      object-fit: cover; 
    }
  }
  .info-container {
    padding: .5rem 1rem 1rem 1rem;
  }
  .date {
    font-size: 14px;
    font-weight: 400;
  }
  .name {
    font-size: 26px;
    font-weight: 400;
    margin: -.5rem 0 .5rem 0;
  }
  .sub-title {
    font-size: 12px;
    font-weight: 700;
  }
  .description, .tags {
    margin: 0 0 .5rem 0;
  }
  .account {
    height: 3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: .5rem 0 .5rem 0;
    .pfp {
      height: 100%;
      aspect-ratio: 1/1;
      border-radius: 100%;
      overflow: hidden;
      margin: 0 .5rem 0 0;
    }
    .text {
      margin-right: auto;
      .username {
        font-size: 20px;
        font-weight: 400;
      }
      .id {
        font-size: 12px;
        font-weight: 400;
      }
    }
  }

}

.overview-btn {
  width: 100%;
  padding: 0.5rem;
  border-radius: 25px;
  border: none;
  color: var(--primary-color);
  font-weight: bold;
  cursor: pointer;
  background-color: var(--prime-color);
  margin: 0.5rem 0;
  box-shadow: 0px 2px 4px 2px var(--shadow);

  &:hover {
    background-color: #000000;
  }
}

.success-msg {
  color: green;
}

.error-msg {
  color: red;
}
</style>

