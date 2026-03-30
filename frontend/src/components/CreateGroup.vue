<script setup>
import { ref, nextTick } from 'vue';
import Page from './helper/Page.vue';
import { pages } from '../store/pages';
import { auth } from '../store/auth';
import { addGroup } from "../store/groups.js";

const errorMsg = ref('');
const groupName = ref('');
const description = ref('');
const title = 'Create Group';

const createGroupListner = async () => {
  const groupData = {
    name: groupName.value,
    description: description.value,
    userId: auth.user.userId
  };

  try {
    const response = await addGroup(groupData.name, groupData.description, groupData.userId);
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
};
</script>

<template>
  <Page :title="title">
    <form class="group-form soft-panel" @submit.prevent="createGroupListner">
      <div>
        <p class="eyebrow">Create group</p>
        <h2>Bring the right people together.</h2>
        <p class="section-copy">Give your group a clear identity so members understand what kind of event belongs there.</p>
      </div>

      <label class="field-group">
        <span>Group name</span>
        <input class="field" type="text" placeholder="Southampton food crew" v-model="groupName"/>
      </label>
      <label class="field-group">
        <span>Description</span>
        <textarea class="textarea" placeholder="What kind of events does this group organise?" v-model="description"></textarea>
      </label>

      <div class="form-actions">
        <button type="submit" class="btn btn-primary">Create Group</button>
        <button type="button" class="btn btn-secondary" @click="pages.dropLayer">Cancel</button>
      </div>
    </form>

    <div v-if="errorMsg" class="error-popup soft-panel">
      <p class="error-message">{{ errorMsg }}</p>
      <button class="btn btn-secondary" @click="errorMsg = ''">Dismiss</button>
    </div>
  </Page>
</template>

<style scoped lang="scss">
.group-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.25rem;
  border-radius: var(--radius-lg);

  h2 {
    margin: 0.8rem 0 0.55rem;
    font-family: var(--font-display);
    font-size: clamp(1.7rem, 3vw, 2.3rem);
    letter-spacing: -0.05em;
  }
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;

  span {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--ink-soft);
  }
}

.textarea {
  min-height: 9rem;
  resize: vertical;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
}

.error-popup {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.15rem;
  border-radius: var(--radius-md);
}

.error-message {
  margin: 0;
  color: var(--danger);
  font-weight: 700;
}

@media (max-width: 640px) {
  .form-actions,
  .error-popup {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
