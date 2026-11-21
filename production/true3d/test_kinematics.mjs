import assert from "node:assert/strict";
import { pumpKinematics } from "../../episodes/044-water-flosser/true3d/kinematics.mjs";

for (let i = 0; i < 360; i += 1) {
  const state = pumpKinematics((i / 360) * Math.PI * 2);
  const len = Math.hypot(state.slider - state.pin[0], state.pin[1]);
  assert.ok(Math.abs(len - 0.94) < 1e-9, `rod length drifted at ${i} deg`);
  assert.notEqual(state.inletOpen, state.outletOpen, `valves overlapped at ${i} deg`);
  assert.equal(state.intake, state.inletOpen);
  assert.equal(state.compression, state.outletOpen);
}

console.log("pump kinematics: 360 angles, rod length 0.94, valves exclusive");
