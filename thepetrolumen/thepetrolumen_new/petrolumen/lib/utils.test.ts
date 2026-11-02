import { describe, it, expect } from 'vitest';
import { cn } from './utils'; // Assuming utils.ts is in the same directory or path is aliased

describe('cn utility function', () => {
  it('should concatenate class names correctly', () => {
    expect(cn('class1', 'class2')).toBe('class1 class2');
  });

  it('should ignore falsy values like undefined, null, false', () => {
    expect(cn('class1', undefined, 'class2', null, false, 'class3')).toBe('class1 class2 class3');
  });

  it('should handle a mix of strings and conditional classes', () => {
    const condition1 = true;
    const condition2 = false;
    expect(cn('base', condition1 && 'active', condition2 && 'hidden', 'another')).toBe('base active another');
  });

  it('should return an empty string if no valid classes are provided', () => {
    expect(cn(undefined, null, false)).toBe('');
  });

  it('should handle single class name', () => {
    expect(cn('single')).toBe('single');
  });

  it('should handle empty strings from conditional logic correctly', () => {
    const condition = true;
    // The current cn function `classes.filter(Boolean).join(' ')` will filter out empty strings.
    expect(cn('class1', condition && '', 'class2')).toBe('class1 class2');

    const falseCondition = false;
    expect(cn('class1', falseCondition && 'extra', 'class2')).toBe('class1 class2');
  });
});
