/**
 * Get animation delay for staggered animations
 * @param index - The index of the element in the list
 * @param delayMs - Delay in milliseconds between each element (default: 20)
 * @returns CSS style object with animationDelay
 */
export function getStaggerDelay(index: number, delayMs: number = 20): React.CSSProperties {
  return { animationDelay: `${index * delayMs}ms` };
}

/**
 * Common animation classes for consistent animations across the app
 * All animations are now 150ms for snappier feel
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
  transitionWithMotionSafe: 'transition-all duration-150 motion-reduce:transition-none',
  
  // For elements that should only animate on initial mount (not on re-renders/selection changes)
  mountOnly: 'animate-fadeInUp [animation-fill-mode:both]',
} as const;

/**
 * Hook helper to determine if an element should animate
 * Use this to prevent re-animation on selection changes
 */
export function shouldAnimateOnMount(hasMounted: boolean): string {
  return hasMounted ? '' : animationClasses.fadeInWithMotionSafe;
}