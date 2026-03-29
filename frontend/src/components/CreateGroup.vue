
<script setup>
import { onMounted, ref, nextTick , watchEffect} from 'vue';
import Page from './helper/Page.vue';
import svgIcon from './helper/svg-icon.vue';
import { mdiCamera } from '@mdi/js';
import {userLocation} from "../store/userLocation.js";
import { pages } from '../store/pages'
import { auth } from '../store/auth';
import {groups, addGroup} from "../store/groups.js";


const errorMsg = ref('');
const groupName = ref('');
const description = ref('');

const title = 'Create Group'


const createGroupListner = async () => {


  const groupData = {
    name: groupName.value,
    description: description.value,
    userId: auth.user.userId
  }
  
  try {
    const response = await addGroup(groupData.name, groupData.description, groupData.userId);
    console.log("Response:", response)
    errorMsg.value = (!response.result) ? response.msg : '';
    if (response.result) {
      description.value = '';
      groupName.value = '';
      await nextTick();
      pages.dropLayer();
    }
  } catch (error) {
    errorMsg.value = error.message || 'An error occurred while creating the group';
  }

  watchEffect(() => {
    console.log('availableGroups changed:', groups.availableGroups);
  });

};


</script>

<template>
  <Page :title="title">

    
    <form class="add-event-form" @submit.prevent>
      <!-- Form elements like input fields and buttons go here -->
    
      <!-- Event Name Input -->
      <input type="text" placeholder="Group Name" v-model="groupName"/>
      <!-- Description Input -->
      <textarea placeholder="Description" v-model="description"></textarea>
      <!-- Event Buttons-->
      <button class="create-btn" @click="createGroupListner">Create Group</button>
      <button class="forget-btn" @click="pages.dropLayer">Forget Group</button>
    </form>

    <!-- Error Popup -->
    <div v-if="errorMsg" class="error-popup">
      <div class="error-content">
        <span class="error-icon">⚠️</span>
        <p class="error-message">{{ errorMsg }}</p>
        <button class="error-dismiss-btn" @click="errorMsg = ''">Dismiss</button>
      </div>
    </div>
  
  </Page>
</template>

<style scoped lang="scss">

#page-wrapper {
  padding: 0rem 1rem 0rem 1rem;
}
#page-title {
  h1 {
    text-align: right;
    margin: -2rem;
  }
  hr {
    opacity: 0.5;
  }
}

.add-event-form {
  display: flex;
  flex-direction: column;
  gap: 0.25rem; /* Space between form elements */
  h2 {
    text-align: center;
  }

  hr {
    margin-top: -1rem;  
  }

  .image-upload-container {
    margin-bottom: 1rem;
    text-align: center;
    position: relative;
  }
  
  /* Styles for the image upload label, which visually represents the input */
  .image-upload-label {
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    background-size: cover; /* Ensure background image covers the area */
    background-position: center;
    border-radius: 25px;
    width: 100%;
    height: 150px;
    background-color: #d9d9d9; /* Light grey background, adjust as needed */
    cursor: pointer;
    transition: background-color 0.3s;
  
    &:hover {
      background-color: #c0c0c0; /* Darker grey on hover */
    }
  }

  .image-name{
    margin-bottom: -1rem;
    span{
      color: #919191;
    }
  }
  

  input[type="text"],
  input[type="date"],
  textarea {
    width: 100%; /* Full width inputs */
    margin-bottom: 0.5rem; /* Space between inputs */
    padding: 0.5rem; /* Padding inside inputs */
    border-radius: 5px; /* Rounded corners for inputs */
    border: 1px solid #ccc; /* Border for inputs */
  }

  textarea {
    resize: vertical; /* Allow vertical resize only */
    height: 5rem; /* Initial height for the textarea */
    max-height: 7rem;
  }

  .create-btn, .forget-btn {
    width: 100%; /* Full width buttons */
    padding: 0.5rem; /* Padding inside buttons */
    border-radius: 25px; /* Rounded corners for buttons */
    border: none; /* No border for buttons */
    color: white; /* Text color for buttons */
    font-weight: bold; /* Bold font for button text */
    cursor: pointer; /* Cursor change for hover */
  }

  .create-btn {
    background-color: #FFC01F; /* Background color for create button */
  }

  .forget-btn {
    background-color: #f44336; /* Background color for delete button */
  }
}

.tags-input {
  background-color: #fff;
  border-radius: 10px;
  border: 1px solid #ccc;
  padding: 10px;
  width: 100%; 
  height: 15vh;
  overflow-y: auto;// Set a specific width if needed

  .tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 0px;

    .tag {
      display: flex;
      align-items: center;
      background-color: #e0e0e0;
      border-radius: 6px;
      padding: 6px 10px;

      .delete-tag {
        background-color: transparent;
        border: none;
        margin-left: 8px;
        cursor: pointer;
      }
    }

    .tag-input-field {
      flex-grow: 1;
      border: none;
      outline: none;
      padding: 6px;
    }
  }

  .tag-instructions {
    font-size: 0.85rem;
    color: #6c757d;
    margin-bottom: 0px;
    margin-top: rem;
  }

  .tags-info {
    font-size: 0.85rem;
    color: #6c757d;
    margin-bottom: -10px;
  }

  .remove-all-btn {
    background-color: #007bff;
    color: #fff;
    border: none;
    border-radius: 5px;
    padding: 10px 15px;
    cursor: pointer;
    font-size: 0.85rem;
  }
}

.error-popup {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 100;
  background-color: #fff;
  border: 1px solid #f44336;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 20px;
  width: 300px;
  text-align: center;
}

.error-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.error-icon {
  font-size: 2rem;
  color: #f44336;
  margin-bottom: 10px;
}

.error-message {
  color: #333;
  margin-bottom: 20px;
}

.error-dismiss-btn {
  border: none;
  background-color: #f44336;
  color: white;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}


</style>