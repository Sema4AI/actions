/**
 * Get animation delay for staggered animations
 * @param index - The index of the element in the list
 * @param delayMs - Delay in milliseconds between each element (default: 30)
 * @returns CSS style object with animationDelay
 */
export function getStaggerDelay(index: number, delayMs: number = 30): React.CSSProperties {
  return { animationDelay: `${index * delayMs}ms` };
}

/**
 * Common animation classes for consistent animations across the app
 */
export const animationClasses = {
  fadeIn: 'animate-fadeIn',
  fadeInUp: 'animate-fadeInUp',
  slideIn: 'animate-slide-in',
  scaleIn: 'animate-scaleIn',

  // With motion reduce support
  withMotionSafe: 'motion-reduce:transform-none motion-reduce:transition-none motion-reduce:animate-none',

  // Common combinations
  fadeInWithMotionSafe: 'animate-fadeInUp motion-reduce:transform-none motion-reduce:transition-none motion-reduce:animate-none',
  transitionWithMotionSafe: 'transition-all duration-200 motion-reduce:transition-none',
} as const;