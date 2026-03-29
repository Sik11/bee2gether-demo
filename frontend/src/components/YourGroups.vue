<script setup>
import { pages } from '../store/pages'
import { ref, onMounted, computed } from 'vue';
import { auth } from '../store/auth';
import Page from './helper/Page.vue';
import { getGroups, updateUserGroups, updateGroups } from '../store/groups.js';

const title = "Groups"

const userId = auth.user.userId;

// Reactive computed property to always get the latest events
const userGroups = computed(() => getGroups().userGroups);

const allGroups = computed(() => getGroups().availableGroups);

// New reactive variable for tab management
const activeTab = ref('Your Groups');

onMounted(async () => {
  updateUserGroups(userId)
  updateGroups()
});

function groupOverview(group){
  getGroups().currentGroup = group;
  pages.addLayer('group-overview');
}

// Function to switch tabs
const switchTab = (tabName) => {
  activeTab.value = tabName;
};
</script>

<template>
  <Page :title="title">
    <!-- Tab Controls -->
    <div class="tab-controls">
      <button :class="{ active: activeTab === 'All Groups' }" @click="switchTab('All Groups')">
        All Groups
      </button>
      <button :class="{ active: activeTab === 'Your Groups' }" @click="switchTab('Your Groups')">
        Your Groups
      </button>
    </div>

    <!-- Groups Container -->
    <div class="groups-container">
      <!-- Container for 'Your Groups' -->
      <div v-if="activeTab === 'Your Groups'">
        <div v-for="group in userGroups" :key="group.id" class="group-card">
          <div class="group-info">
            <div class="group-name">{{ group.name }}</div>
          </div>
          <button class="more-info-btn"  @click="groupOverview(group)">More info...</button>
        </div>
      </div>

      <!-- Container for 'All Groups' -->
      <div v-if="activeTab === 'All Groups'">
        <div v-for="group in allGroups" :key="group.id" class="group-card">
          <div class="group-info">
            <div class="group-name">{{ group.name }}</div>
          </div>
          <button class="more-info-btn" @click="groupOverview(group)">More info...</button>
        </div>
      </div>
    </div>

    <button type="button" class="create-group-btn" @click="pages.addLayer('create-group')">
      Create New Group
    </button>
  </Page>
</template>


<style scoped lang="scss">
.groups-container {
  padding: 1rem;
  max-height: 65vh; // Adjust height calculation as needed
  overflow-y: auto;
}

.group-card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 1rem;
  height: 15vh;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: box-shadow 0.3s ease;

  &:hover {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
  }
}

.group-image {
  flex-shrink: 0;
  width: 100px; // Set width of image box
  height: 100px; // Set height of image box
  border-radius: 8px;
  overflow: hidden;
  margin-right: 1rem;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover; // Ensures image covers the box
  }
}



.group-info {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: left;
}

.group-date {
  font-size: 0.85rem;
  color: #666;
}

.group-name {
  font-weight: bold;
}

.more-info-btn {
  border: none;
  background-color: transparent;
  color: #FFC01F;
  cursor: pointer;
  align-self: flex-end;
}

.create-group-btn {
  // Existing styles
  bottom: 20px; // Adjust position from bottom
}


.create-group-btn {
  background-color: #FFC01F;
  /* Replace with the specific color you need */
  color: white;
  font-weight: bold;
  border: none;
  border-radius: 30px;
  /* Adjust as needed */
  padding: 15px 30px;
  width: 90%;
  /* Adjust to match your layout */
  position: fixed;
  bottom: 5rem;
  /* Center the button */
  display: block;
  left: 50%;
  text-transform: uppercase;
  /* Optional: Makes text uppercase */
  transform: translateX(-50%);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  /* Optional: Adds a shadow */
  cursor: pointer;
  transition: background-color 0.3s ease;
  /* Optional: Adds a transition effect */
}

.create-group-btn:hover {
  background-color: #e6b800;
  /* Darker shade for hover state */
}

.tab-controls {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.tab-controls button {
  padding: 0.5rem 1rem;
  border: none;
  background-color: transparent;
  cursor: pointer;
  font-weight: bold;
  margin: 0 0.5rem;
}

.tab-controls button.active {
  color: #FFC01F;
  border-bottom: 2px solid #FFC01F;
}
</style>