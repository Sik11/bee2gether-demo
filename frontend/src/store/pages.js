import { reactive } from "vue";
import { markRaw } from 'vue';

export const pages = reactive({
  selected: undefined,
  layers: [],
  tabs: [],
  lastAction: 'setSelected',

  /**
   * Initialise the wrapper pages
   * @param {{}} tabs 
   * @param {string} id 
   */
  init(tabs, id) {
    tabs.forEach(({component}) => markRaw(component))
    pages.tabs = tabs
    pages.selected = id
  },

  /**
   * Set the selected page & clears all layered pages
   * @param {string} id 
   */
  setSelected(id) {
    pages.selected = id
    pages.layers = []
    pages.lastAction = 'setSelected'
  },
  /**
   * 
   * @param {*} id 
   */
  addLayer(id) {
    if (!pages.layers.includes(id)) {
      pages.layers.push(id)
      pages.lastAction = 'addLayer'
    }
  },
  dropLayer() {
    pages.layers.pop()
    pages.lastAction = 'dropLayer'
  },

  // These are used by Wrapper.vue
  getLabelledTabs() {
    return pages.tabs.filter(({label}) => label !== undefined)
  },
  getZIndex(id) {
    const zindex =  [pages.selected, ...pages.layers].indexOf(id) + 1
    return zindex === 0 ? 10 : zindex
  },
  isSelected(id) {
    return id === pages.selected
  },
  isVisible(id) {
    return id === pages.selected || pages.layers.includes(id)
  },
  isLayerEmpty() {
    return pages.layers.length === 0 
  }
})