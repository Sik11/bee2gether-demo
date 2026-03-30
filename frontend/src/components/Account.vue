<script setup>
import { settings } from '../store/settings';
import { auth } from '../store/auth';
import Page from './helper/Page.vue';
import Avatar from './helper/Avatar.vue';
</script>

<template>
  <Page title="Your Account" custom-class="body">
    <section class="profile-card soft-panel">
      <div class="header">
        <Avatar :username="auth.user.username" custom-class="pfp"/>
        <div>
          <p class="eyebrow">Profile</p>
          <h2>{{ auth.user.username }}</h2>
          <p class="account-id">#{{ auth.user.userId.substring(0, 6) }}</p>
        </div>
      </div>
      <p class="section-copy">
        Keep your preferences simple and get back to finding plans faster.
      </p>
    </section>

    <section class="settings-card soft-panel">
      <div class="settings-row">
        <div>
          <h3>Dark mode</h3>
          <p class="section-copy">Switch Bee2Gether into a richer night palette.</p>
        </div>
        <label class="toggle">
          <input v-model="settings.isDarkMode" type="checkbox" role="switch">
          <span></span>
        </label>
      </div>
    </section>

    <button type="button" class="btn btn-danger logout-btn" @click="() => auth.logout()">Logout</button>
  </Page>
</template>

<style scoped lang="scss">
.body {
  text-align: left;
  gap: 1rem;
}

.profile-card,
.settings-card {
  border-radius: var(--radius-lg);
  padding: 1.25rem;
}

.header {
  display: flex;
  align-items: center;
  gap: 1rem;

  .pfp {
    width: clamp(5rem, 18vw, 8rem);
    height: clamp(5rem, 18vw, 8rem);
    border-radius: 100%;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
  }

  h2 {
    margin: 0.45rem 0 0.3rem;
    font-family: var(--font-display);
    font-size: clamp(1.8rem, 4vw, 2.4rem);
    letter-spacing: -0.05em;
  }
}

.account-id {
  margin: 0;
  color: var(--secondary);
  font-weight: 700;
}

.settings-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;

  h3 {
    margin: 0 0 0.35rem;
    font-family: var(--font-display);
  }
}

.toggle {
  position: relative;
  display: inline-flex;
  width: 3.8rem;
  height: 2.2rem;

  input {
    position: absolute;
    inset: 0;
    opacity: 0;
  }

  span {
    width: 100%;
    height: 100%;
    border-radius: var(--radius-pill);
    background: var(--canvas-strong);
    border: 1px solid var(--border);
    transition: background-color var(--transition-fast);
    position: relative;
  }

  span::after {
    content: '';
    position: absolute;
    top: 0.22rem;
    left: 0.22rem;
    width: 1.45rem;
    height: 1.45rem;
    border-radius: 50%;
    background: var(--surface-strong);
    box-shadow: var(--shadow-sm);
    transition: transform var(--transition-fast);
  }

  input:checked + span {
    background: var(--accent-soft);
  }

  input:checked + span::after {
    transform: translateX(1.55rem);
  }
}

.logout-btn {
  width: fit-content;
}

@media (max-width: 640px) {
  .header,
  .settings-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
