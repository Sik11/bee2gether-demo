<script setup>
import { auth } from '../store/auth'
import { ref } from 'vue';

// Defining reactive references for the username and password input fields.
const username = ref('');
const password = ref('');
const errorMsg = ref('');

// Defining functions to handle login and registration.
// Method to handle login
const login = async () => {
  const response = await auth.login(username.value, password.value);
  errorMsg.value = (!response.result) ? response.msg : ''
};

// Method to handle registration
const register = async () => {
  const response = await auth.register(username.value, password.value);
  errorMsg.value = (!response.result) ? response.msg : ''
};

</script>

<template>
  <div class="viewport" id="background">
    <div class="viewport" id="filter">
      <img src="../assets/logo-big.png" alt="Logo  saying Bee 2 Gether with a happy bee ontop">
      <hr>
      <!-- Form for Login and Registration -->
      <form id="auth-form">
        <!-- Input Fields for Username and Password -->
        <input type="text" placeholder="Username" v-model="username"/>
        <input type="password" placeholder="Password" v-model="password" />
        <!-- Error message -->
        <div v-if="errorMsg" class="error-message">{{ errorMsg }}</div>

        <!-- Login and Register Buttons -->
        <button type="button" class="login-btn" @click=login>LOGIN</button>
        <button type="button" class="register-btn" @click=register>REGISTER</button>
        <button type="button" @click="async () => {
          const response = await auth.register('guest','test12345678');
          if (!response.result) {
            await auth.login('guest','test12345678');
          }
        }">SKIP</button>
      </form>
    </div>
  </div>
</template>

<style scoped lang="scss">
  #background {
    background-image: url('../assets/heart-background.png');
    background-position: center;
    background-size: cover;
    #filter { 
      background: rgba(255, 255, 255, 0.4);
      backdrop-filter: blur(5px);

      padding: 0 2rem 0 2rem;
    }
  }
  img {
    margin-top: 1rem;
    width: min(70vw, 250px);
  }
  hr {
    margin-top: 0;
    background: #000000;
  }

  #auth-form {
    display: flex;
    flex-direction: column;
    gap: 1rem; /* Adjust gap to match your design */
  
    input[type="text"],
    input[type="password"] {
      /* Style your input fields */
      border: 1px solid #000; /* Example border */
      padding: 0.5rem;
      font-size: 1rem;
    }
    input[type="password"] {
      margin-bottom: 0.5rem;
    }
    .error-message {
      color: rgb(167, 30, 30);
      margin-bottom: 1rem; 
      /* Space below the error message */
      /* Add any additional styling you want for the error message */
      font-weight: bold !important;
    }

    button {
      /* Style your buttons */
      border: none;
      padding: 0.5rem;
      color: black;
      background-color: #00d965;
      font-size: 1rem;
      font-weight: bold;
      border-radius: 2rem; /* Example border radius */
      cursor: pointer;
      box-shadow: 0px 2px 4px 0px rgba(0, 0, 0, 0.25);
    }

    .login-btn {
      margin-top: auto;
      color: white;
      background-color: #007BFF; /* A shade of blue */
    }

    .register-btn {
      background: #FFC01F; /* Example background color */
    }

    .login-btn:hover, .register-btn:hover{
      background-color: #00d965; /* Slightly darker shade of blue */
    }
  }
</style>