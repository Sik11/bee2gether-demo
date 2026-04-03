<script setup>
import { auth } from '../store/auth';
import { ref } from 'vue';

const username = ref('');
const password = ref('');
const errorMsg = ref('');

const login = async () => {
  if (auth.isBusy) return;
  const response = await auth.login(username.value, password.value);
  errorMsg.value = (!response.result) ? response.msg : '';
};

const register = async () => {
  if (auth.isBusy) return;
  const response = await auth.register(username.value, password.value);
  errorMsg.value = (!response.result) ? response.msg : '';
};

const continueAsGuest = async () => {
  if (auth.isBusy) return;
  const response = await auth.continueAsGuest();
  errorMsg.value = (!response.result) ? response.msg : '';
};
</script>

<template>
  <div class="auth-screen">
    <section class="auth-hero">
      <div class="auth-hero__veil"></div>
      <div class="auth-hero__content">
        <span class="eyebrow">Bee2Gether</span>
        <img src="../assets/logo-big.png" alt="Logo saying Bee 2 Gether with a happy bee ontop">
        <h1>Find your next event without fighting the interface.</h1>
        <p>
          Discover nearby plans, organise groups, and turn spontaneous ideas into something people actually join.
        </p>
      </div>
    </section>

    <section class="auth-panel soft-panel">
      <div v-if="auth.isBusy" class="auth-progress" aria-hidden="true">
        <span class="auth-progress__bar"></span>
      </div>
      <div class="auth-panel__header">
        <p class="eyebrow">Welcome back</p>
        <h2>Sign in or create an account</h2>
        <p class="section-copy">
          Bee2Gether works best when you can jump from discovery to planning in a few taps.
        </p>
      </div>

      <form class="auth-form" @submit.prevent="login">
        <label class="field-group">
          <span>Username</span>
          <input
            v-model="username"
            class="field"
            type="text"
            placeholder="Your username"
            autocomplete="username"
            :disabled="auth.isBusy"
          />
        </label>
        <label class="field-group">
          <span>Password</span>
          <input
            v-model="password"
            class="field"
            type="password"
            placeholder="10 to 20 characters"
            autocomplete="current-password"
            :disabled="auth.isBusy"
          />
        </label>

        <div v-if="errorMsg" class="error-message">{{ errorMsg }}</div>
        <div v-if="auth.isBusy" class="auth-status">{{ auth.busyLabel }}…</div>

        <div class="auth-actions">
          <button type="submit" class="btn btn-primary auth-btn" :disabled="auth.isBusy">
            <span v-if="auth.busyLabel === 'Signing in'" class="button-loader" aria-hidden="true"></span>
            <span>{{ auth.busyLabel === 'Signing in' ? 'Signing in' : 'Log In' }}</span>
          </button>
          <button type="button" class="btn btn-secondary auth-btn" @click="register" :disabled="auth.isBusy">
            <span v-if="auth.busyLabel === 'Creating account'" class="button-loader" aria-hidden="true"></span>
            <span>{{ auth.busyLabel === 'Creating account' ? 'Creating account' : 'Create Account' }}</span>
          </button>
        </div>
        <button
          type="button"
          class="btn btn-ghost guest-btn"
          @click="continueAsGuest"
          :disabled="auth.isBusy"
        >
          <span v-if="auth.busyLabel === 'Opening guest session'" class="button-loader" aria-hidden="true"></span>
          <span>{{ auth.busyLabel === 'Opening guest session' ? 'Opening guest session' : 'Continue as guest' }}</span>
        </button>
      </form>
    </section>
  </div>
</template>

<style scoped lang="scss">
.auth-screen {
  min-height: 100dvh;
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(22rem, 28rem);
  background: var(--canvas);
  overflow-y: auto;
}

.auth-hero {
  position: relative;
  min-height: 100dvh;
  background:
    linear-gradient(150deg, rgba(10, 7, 6, 0.52), rgba(10, 7, 6, 0.24)),
    url('../assets/heart-background-full.png') center / cover no-repeat;
  overflow: hidden;
}

.auth-hero__veil {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at top right, rgba(244, 178, 35, 0.26), transparent 30%),
    radial-gradient(circle at bottom left, rgba(44, 122, 123, 0.18), transparent 34%);
}

.auth-hero__content {
  position: relative;
  z-index: 1;
  max-width: 34rem;
  padding: clamp(2rem, 4vw, 3.75rem);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  min-height: 100%;
  color: #fff5ea;

  img {
    width: clamp(12rem, 24vw, 16rem);
    margin: 1.25rem 0 1.5rem;
  }

  h1 {
    margin: 0 0 1rem;
    font-family: var(--font-display);
    font-size: clamp(2.4rem, 5vw, 4.8rem);
    line-height: 0.95;
    letter-spacing: -0.06em;
    color: #fff6eb;
  }

  p {
    max-width: 28rem;
    margin: 0;
    color: rgba(255, 246, 235, 0.82);
    font-size: 1.02rem;
    line-height: 1.7;
  }
}

.auth-panel {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: clamp(1.5rem, 4vw, 3rem);
  border-radius: 0;
  border-left: 1px solid var(--border);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--surface) 96%, transparent), color-mix(in srgb, var(--canvas-strong) 88%, transparent));
}

.auth-progress {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 0.22rem;
  overflow: hidden;
  border-radius: inherit;
}

.auth-progress__bar {
  display: block;
  width: 38%;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent 0%, var(--accent) 22%, color-mix(in srgb, var(--accent) 55%, white 45%) 55%, transparent 100%);
  animation: auth-progress-slide 1.05s ease-in-out infinite;
}

.auth-panel__header {
  margin-bottom: 1.5rem;

  h2 {
    margin: 1rem 0 0.65rem;
    font-family: var(--font-display);
    font-size: clamp(1.8rem, 2vw, 2.4rem);
    line-height: 1.02;
    letter-spacing: -0.04em;
  }
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.auth-status {
  font-size: 0.92rem;
  color: var(--ink-muted);
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-align: left;

  span {
    font-size: 0.92rem;
    font-weight: 700;
    color: var(--ink-soft);
  }
}

.auth-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.auth-btn {
  width: 100%;
}

.guest-btn {
  margin-top: 0.25rem;
}

.auth-actions .btn,
.guest-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
}

.button-loader {
  width: 0.95rem;
  height: 0.95rem;
  border-radius: 50%;
  border: 2px solid color-mix(in srgb, currentColor 24%, transparent);
  border-top-color: currentColor;
  animation: button-loader-spin 0.7s linear infinite;
}

.error-message {
  border-radius: var(--radius-md);
  padding: 0.85rem 1rem;
  background: var(--danger-soft);
  color: var(--danger);
  font-size: 0.94rem;
  font-weight: 700;
}

:global(.dark-mode) .auth-hero {
  background:
    linear-gradient(145deg, rgba(6, 8, 11, 0.72), rgba(10, 13, 18, 0.38)),
    url('../assets/heart-background-full.png') center / cover no-repeat;
}

:global(.dark-mode) .auth-hero__veil {
  background:
    radial-gradient(circle at top right, rgba(242, 184, 74, 0.12), transparent 34%),
    radial-gradient(circle at bottom left, rgba(127, 201, 202, 0.08), transparent 38%);
}

:global(.dark-mode) .auth-panel {
  background:
    linear-gradient(180deg, rgba(17, 21, 28, 0.96), rgba(20, 24, 32, 0.94));
  border-left-color: rgba(255, 255, 255, 0.08);
}

:global(.dark-mode) .auth-panel__header .section-copy,
:global(.dark-mode) .field-group span {
  color: var(--ink-soft);
}

:global(.dark-mode) .field {
  background: rgba(14, 18, 25, 0.94);
  border-color: rgba(255, 255, 255, 0.08);
  color: var(--ink);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

:global(.dark-mode) .field::placeholder {
  color: var(--ink-muted);
}

:global(.dark-mode) .btn-secondary.auth-btn {
  background: rgba(24, 30, 39, 0.96);
  color: var(--ink);
  border-color: rgba(255, 255, 255, 0.08);
}

:global(.dark-mode) .btn-secondary.auth-btn:hover {
  background: rgba(31, 37, 47, 0.98);
}

:global(.dark-mode) .guest-btn {
  color: var(--ink-soft);
}

@media (max-width: 960px) {
  .auth-screen {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .auth-hero {
    min-height: auto;
    padding-top: 2rem;
  }

  .auth-hero__content {
    min-height: 24rem;
    justify-content: flex-start;
  }

  .auth-panel {
    border-left: 0;
    border-top: 1px solid var(--border);
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    margin-top: -1.5rem;
    padding-bottom: max(2rem, env(safe-area-inset-bottom));
  }
}

@media (max-width: 640px) {
  .auth-screen {
    align-content: start;
  }

  .auth-hero__content {
    min-height: 20rem;
  }

  .auth-actions {
    grid-template-columns: 1fr;
  }

  .auth-panel {
    padding-inline: 1.1rem;
    padding-bottom: max(2.4rem, env(safe-area-inset-bottom));
  }
}

@keyframes auth-progress-slide {
  0% {
    transform: translateX(-110%);
  }
  100% {
    transform: translateX(320%);
  }
}

@keyframes button-loader-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
