# Unimplemented Properties

This document tracks MQTT properties that have been observed but not yet implemented in production code.

---

## 1:2 (Service 1 / Property 2)
**Status:** Not implemented in production

**Observation:** Single discovery value = `1`, no timeline updates.

**Hypothesis:** Capability / presence / feature‑enabled flag (boolean latch). Could also represent an initialization/ready indicator.

---

## 1:3 (Service 1 / Property 3)
**Status:** Not implemented in production

**Observation:** Single discovery value = `0`, no updates.

**Hypothesis:** Secondary capability or complementary flag to `1:2` (e.g., feature disabled). Potential pair (1:2=1 active, 1:3=0 inactive). No runtime function yet.
