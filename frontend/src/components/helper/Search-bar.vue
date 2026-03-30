<script setup>
import { mdiMapSearch as searchIcon } from '@mdi/js';
import svgIcon from './svg-icon.vue';
import { ref, watch } from 'vue';
import { events } from '../../store/events';

const { customClass } = defineProps({
  customClass: { type: [String, Object, Array], default: "" },
});

const emit = defineEmits(['select']);
const searchTerm = ref('');

const onSubmit = () => {
  events.searchEvent(searchTerm.value).then(res => {
    if (res.result && res.events?.length) {
      onOpen(res.events[0]);
    }
  });
};

const onOpen = (event) => {
  events.searchResults = [];
  emit('select', event);
};

watch(searchTerm, () => {
  events.searchEvent(searchTerm.value);
});
</script>

<template>
  <div :class="customClass">
    <form class="search-shell soft-panel" @submit.prevent="onSubmit">
      <div class="search-form">
        <label class="search-icon" for="search-bar">
          <svg-icon :path="searchIcon" height="1.3rem" custom-class="svg"/>
        </label>
        <input
          id="search-bar"
          v-model="searchTerm"
          class="search-field"
          type="text"
          placeholder="Search for events, plans, and meetups"
          autocomplete="off"
        >
      </div>

      <div class="filter-panel" aria-label="Map filters">
        <span class="filter-label">Filters</span>
        <button
          type="button"
          :class="['filter-toggle', { active: events.filters.groupsOnly }]"
          @click="events.toggleGroupsOnly()"
        >
          Groups
        </button>
        <label class="filter-select-wrap">
          <select class="filter-select" :value="events.filters.window" @change="events.setFilterWindow($event.target.value)">
            <option value="all">No filter</option>
            <option value="today">Today</option>
            <option value="week">This week</option>
          </select>
        </label>
        <label class="filter-select-wrap">
          <select class="filter-select" :value="events.filters.tag" @change="events.setTagFilter($event.target.value)">
            <option v-for="tag in events.getAvailableTags()" :key="tag" :value="tag">
              {{ tag === 'all' ? 'All Tags' : tag }}
            </option>
          </select>
        </label>
      </div>

      <div class="results" v-if="events.searchResults.length > 0 && searchTerm !== ''">
        <button class="result" v-for="event in events.searchResults" :key="event.id" @click.prevent="onOpen(event)">
          <span class="name">{{ event.name }}</span>
          <span class="time">@{{ event.username }}</span>
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped lang="scss">
.search-shell {
  position: relative;
  display: grid;
  grid-template-columns: minmax(21rem, 1.9fr) auto;
  align-items: center;
  gap: 0.55rem;
  border-radius: 2rem;
  padding: 0.55rem 0.75rem;
}

.search-form {
  display: flex;
  align-items: center;
  min-height: 3rem;
  padding: 0 0.3rem 0 0.1rem;
  min-width: 0;
  border-right: 1px solid var(--border);
  padding-right: 0.45rem;
}

.search-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  color: var(--ink-muted);
}

.search-field {
  flex: 1;
  min-width: 0;
  border: 0;
  background: transparent;
  color: var(--ink);
  padding: 0;
  font-size: 0.92rem;

  &::placeholder {
    color: var(--ink-muted);
  }

  &:focus {
    outline: none;
  }
}

.filter-panel {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex-wrap: nowrap;
  min-width: 0;
}

.filter-label {
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--ink-muted);
}

.filter-toggle,
.filter-select {
  min-height: 1.82rem;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border);
  background: var(--surface-strong);
  color: var(--ink);
  padding: 0.18rem 0.58rem;
  font-weight: 700;
  font-size: 0.76rem;
  line-height: 1.1;
  transition: background-color var(--transition-fast), color var(--transition-fast), border-color var(--transition-fast);
}

.filter-select-wrap {
  display: inline-flex;
}

.filter-toggle.active {
  background: var(--accent-soft);
  color: var(--accent-strong);
  border-color: color-mix(in srgb, var(--accent-strong) 25%, var(--border));
}

.filter-select {
  min-width: 5.9rem;
}

.filter-toggle {
  white-space: nowrap;
}

.results {
  position: absolute;
  top: calc(100% + 0.55rem);
  left: 0;
  right: 0;
  display: grid;
  gap: 0.35rem;
  padding: 0.65rem;
  border-radius: var(--radius-md);
  background: var(--surface-strong);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-md);
}

.result {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  border-radius: var(--radius-sm);
  padding: 0.8rem 0.9rem;
  background: transparent;
  color: var(--ink);
  cursor: pointer;

  &:hover {
    background: var(--accent-soft);
  }

  .name {
    font-weight: 700;
  }

  .time {
    margin-left: auto;
    color: var(--ink-muted);
    font-size: 0.88rem;
  }
}

@media (max-width: 768px) {
  .search-shell {
    grid-template-columns: 1fr;
    gap: 0.55rem;
    padding: 0.65rem 0.7rem 0.75rem;
    border-radius: 1.8rem;
  }

  .filter-panel {
    gap: 0.45rem;
    flex-wrap: wrap;
    padding-top: 0.1rem;
  }

  .filter-label {
    width: 100%;
  }

  .search-form {
    border-right: 0;
    padding-right: 0.2rem;
  }

  .filter-toggle,
  .filter-select {
    min-height: 2.1rem;
    padding: 0.38rem 0.7rem;
    font-size: 0.82rem;
  }

  .filter-select {
    min-width: 7.2rem;
  }
}
</style>
