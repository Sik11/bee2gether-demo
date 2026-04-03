<script setup>
import { computed, nextTick, ref } from 'vue';
import { mdiClose } from '@mdi/js';
import svgIcon from './helper/svg-icon.vue';
import { pages } from '../store/pages';
import { auth } from '../store/auth';
import { addGroup } from "../store/groups.js";
import { settings } from '../store/settings';
import logo from '../assets/logo.png';
import darkLogo from '../assets/dark-logo.png';

const errorMsg = ref('');
const groupName = ref('');
const description = ref('');

const activeLogo = computed(() => (settings.isDarkMode ? darkLogo : logo));

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
      pages.dropLayer('create-group');
    }
  } catch (error) {
    errorMsg.value = error.message || 'An error occurred while creating the group';
  }
};

function closeSheet() {
  pages.dropLayer('create-group');
}
</script>

<template>
  <section class="group-sheet soft-panel">
    <header class="group-sheet__header">
      <div class="group-sheet__identity">
        <img :src="activeLogo" alt="Bee2Gether logo" />
        <span>Bee2Gether</span>
        <span class="group-sheet__divider"></span>
        <strong>Create group</strong>
      </div>
      <button type="button" class="group-sheet__icon-btn" aria-label="Close create group" @click="closeSheet">
        <svg-icon :path="mdiClose" width="1.1rem" height="1.1rem" />
      </button>
    </header>

    <form class="group-sheet__body" @submit.prevent="createGroupListner">
      <div class="group-sheet__intro">
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

      <p v-if="errorMsg" class="error-inline">{{ errorMsg }}</p>

      <footer class="group-sheet__footer">
        <button type="button" class="btn btn-secondary" @click="closeSheet">Cancel</button>
        <button type="submit" class="btn btn-primary">Create Group</button>
      </footer>
    </form>
  </section>
</template>

<style scoped lang="scss">
.group-sheet {
  width: min(100%, 48rem);
  height: min(41.5rem, calc(100dvh - var(--topbar-height) - 0.85rem));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: calc(var(--radius-lg) + 0.3rem);
  border: 1px solid color-mix(in srgb, var(--border-strong) 88%, transparent);
  background: color-mix(in srgb, var(--surface) 95%, transparent);
  box-shadow:
    0 28px 70px rgba(23, 18, 12, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.34);
}

.group-sheet__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.85rem;
  padding: 1rem 1.2rem;
  border-bottom: 1px solid color-mix(in srgb, var(--border-strong) 82%, transparent);
}

.group-sheet__identity {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  color: var(--ink-soft);
  font-size: 0.96rem;
  line-height: 1;
}

.group-sheet__identity img {
  width: 1.6rem;
  height: 1.6rem;
  flex: 0 0 auto;
}

.group-sheet__identity strong {
  color: var(--ink);
  font-weight: 700;
}

.group-sheet__divider {
  width: 1px;
  height: 1.1rem;
  background: color-mix(in srgb, var(--border-strong) 82%, transparent);
}

.group-sheet__icon-btn {
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  background: color-mix(in srgb, var(--surface) 90%, transparent);
  border: 1px solid color-mix(in srgb, var(--border) 92%, transparent);
  color: var(--ink);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.group-sheet__body {
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.35rem 1.4rem 1.1rem;
  margin: 0;
  overflow: auto;
}

.group-sheet__intro {
  display: grid;
  gap: 0.4rem;
}

.group-sheet__intro .eyebrow,
.group-sheet__intro .section-copy {
  margin: 0;
}

.group-sheet__intro .eyebrow {
  width: fit-content;
  max-width: max-content;
}

.group-sheet__intro h2 {
  margin: 0.1rem 0 0.25rem;
  font-family: var(--font-display);
  font-size: clamp(1.7rem, 3vw, 2.3rem);
  letter-spacing: -0.05em;
  line-height: 1.02;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.field-group > span {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--ink-soft);
}

.field-group .field,
.field-group .textarea {
  width: 100%;
}

.textarea {
  min-height: 9rem;
  resize: vertical;
}

.group-sheet__footer {
  margin-top: auto;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 0.25rem;
  background: color-mix(in srgb, var(--surface) 96%, transparent);
}

.group-sheet__footer .btn {
  min-width: 8.5rem;
}

.error-inline {
  margin: 0;
  color: var(--danger);
  font-weight: 700;
}

@media (max-width: 720px) {
  .group-sheet {
    width: min(100%, calc(100% - 0.8rem));
    height: min(41.5rem, calc(100dvh - var(--topbar-height) - 0.45rem));
    border-radius: 1.25rem;
  }

  .group-sheet__footer {
    flex-direction: column-reverse;
  }
}
</style>
