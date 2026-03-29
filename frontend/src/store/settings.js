import { reactive } from "vue";

const initialState = {
  isDarkMode: false
}

export const settings = reactive({
  ...initialState
})