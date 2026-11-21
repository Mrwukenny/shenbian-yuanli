/** Slider-crank for the 044 piston pump. Rod length stays 0.94; the two valves never open together. */

export function pumpKinematics(theta) {
  const r = 0.2;
  const L = 0.94;
  const sin = Math.sin(theta);
  const cos = Math.cos(theta);
  const pinX = -0.65 + r * cos;
  const pinY = r * sin;
  const pinZ = 0.625;
  const slider = -0.65 + r * cos + Math.sqrt(L * L - r * r * sin * sin);
  return {
    theta,
    pin: [pinX, pinY, pinZ],
    slider,
    intake: sin >= 0,
    compression: sin < 0,
    stroke: Math.max(0, -sin),
    inletOpen: sin >= 0,
    outletOpen: sin < 0,
    rodLength: L,
  };
}
