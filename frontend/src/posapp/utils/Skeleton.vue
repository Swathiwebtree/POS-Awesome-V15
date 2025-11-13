<template>
  <div class="pos-skeleton" :style="skeletonStyle"></div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  // Height of the skeleton block (e.g., '58px', '100%')
  height: {
    type: [String, Number],
    default: '1em' 
  },
  // Width of the skeleton block (e.g., '100%', '200px')
  width: {
    type: [String, Number],
    default: '100%'
  },
});

// Computed style for setting height and width dynamically
const skeletonStyle = computed(() => {
  const h = typeof props.height === 'number' ? `${props.height}px` : props.height;
  const w = typeof props.width === 'number' ? `${props.width}px` : props.width;

  return {
    height: h,
    width: w,
  };
});
</script>

<style scoped>
/* Base style for the skeleton block */
.pos-skeleton {
  background-color: #e0e0e0; /* Light gray color */
  border-radius: 4px; /* Slight rounding of corners */
  overflow: hidden;
  position: relative;
}

/* Optional: Add a shimmering effect to simulate loading */
.pos-skeleton::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  transform: translateX(-100%);
  background-image: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0) 0,
    rgba(255, 255, 255, 0.2) 20%,
    rgba(255, 255, 255, 0.5) 60%,
    rgba(255, 255, 255, 0)
  );
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}
</style>