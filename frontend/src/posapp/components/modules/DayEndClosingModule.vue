<template>
  <div>
    <h2>Day End Closing</h2>
    <button @click="closeDay">Perform Day End Closing</button>
    <pre>{{ report }}</pre>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return { report: null };
  },
  methods: {
    async closeDay() {
      try {
        const res = await axios.post("/api/method/posawesome.posawesome.api.lazer_pos.day_end_closing");
        this.report = res.data;
      } catch (err) {
        console.error(err);
      }
    },
  },
};
</script>
